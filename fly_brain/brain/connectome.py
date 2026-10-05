"""The male CNS v1.0 wiring as a compressed sparse matrix, plus one metadata row per neuron.

    python -m brain.connectome     # data/*.feather -> brain.npz, brain_meta.parquet (about half a minute)

Source: the public male-CNS v1.0 release (male-cns.janelia.org/download), body annotations, neurotransmitter
predictions and the minconf-0.5 synapse-weight table, all in data/.

What counts as a neuron: an annotated body that has been given a superclass. The simulator's neuron i is the
i-th of those in bodyId order.
What counts as a connection: a row of the weight table whose two ends are both neurons; its weight is the
number of synapses from the first to the second.
Excitatory or inhibitory: decided by the presynaptic neuron's transmitter, following Shiu et al. 2024 (GABA and
glutamate are inhibitory, everything else excitatory). This dataset also predicts histamine, which acts through
chloride channels in insects, so it is counted as inhibitory as well.
Which transmitter: the best call available for the body, trying the consensus call (which already includes
the experimental ground truth), the call for its cell type and the body's own prediction, in that order.

brain.npz stores the matrix row by row (CSR, rows = presynaptic neurons): row i's targets are
post[ptr[i]:ptr[i+1]] and their signed synapse counts syn[ptr[i]:ptr[i+1]], targets in ascending order.
"""
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.feather as ft
import torch

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ANNOTATIONS = DATA / "body-annotations-male-cns-v1.0-minconf-0.5.feather"
TRANSMITTERS = DATA / "body-neurotransmitters-male-cns-v1.0.feather"
WEIGHTS = DATA / "connectome-weights-male-cns-v1.0-minconf-0.5.feather"
NPZ, META = ROOT / "brain.npz", ROOT / "brain_meta.parquet"

CHLORIDE_TRANSMITTERS = {"gaba", "glutamate", "histamine"}
CALLS_BY_TRUST = ["consensus_nt", "celltype_predicted_nt", "predicted_nt"]
FIELDS = ["type", "instance", "superclass", "class", "subclass", "somaSide", "rootSide", "entryNerve"]


class Brain:
    """A built wiring diagram, ready to simulate: `n` neurons and the CSR arrays (as torch tensors)."""

    def __init__(self, path=NPZ):
        with np.load(path, allow_pickle=False) as stored:
            if "ptr" not in stored.files:
                raise SystemExit(f"{path} has an older layout; rebuild it with `python -m brain.connectome`")
            arrays = {name: stored[name] for name in stored.files}
        self.body_ids = arrays["body_ids"]
        self.ptr, self.post = (torch.as_tensor(arrays[k], dtype=torch.int64) for k in ("ptr", "post"))
        self.syn = torch.as_tensor(arrays["syn"], dtype=torch.float32)
        self.n, self.n_edges = self.ptr.numel() - 1, self.post.numel()
        self._per_device = {}
        self._sorted = None

    def on(self, device):
        """(ptr, post, syn) on `device`, copied there once."""
        device = torch.device(device)
        if device not in self._per_device:
            self._per_device[device] = (self.ptr.to(device), self.post.to(device), self.syn.to(device))
        return self._per_device[device]

    def index_of(self, body_ids):
        """Simulator indices of the given bodyIds, in the order given; ids that are not neurons are dropped."""
        if self._sorted is None:
            order = np.argsort(self.body_ids, kind="stable")  # the FlyWire network keeps Shiu's own order
            self._sorted = (self.body_ids[order], order)
        ids, order = self._sorted
        wanted = np.asarray(body_ids, dtype=np.int64)
        at = np.minimum(np.searchsorted(ids, wanted), len(ids) - 1)
        return order[at][ids[at] == wanted]

    def edges(self):
        """(pre, post, syn) numpy arrays, one entry per connected pair."""
        pre = torch.repeat_interleave(torch.arange(self.n), self.ptr.diff())
        return pre.numpy(), self.post.numpy(), self.syn.numpy()


def best_transmitter_call(body_ids):
    calls = (ft.read_table(TRANSMITTERS, columns=["body", *CALLS_BY_TRUST]).to_pandas()
             .drop_duplicates("body").set_index("body").reindex(body_ids)[CALLS_BY_TRUST])
    usable = calls.where(calls.notna() & (calls != "unclear"))
    return usable.bfill(axis=1).iloc[:, 0].fillna("unclear").to_numpy(dtype=object)


def build():
    clock = time.time()
    annotations = ft.read_table(ANNOTATIONS, columns=["bodyId", *FIELDS]).to_pandas()
    neurons = annotations.dropna(subset=["superclass"]).sort_values("bodyId").reset_index(drop=True)
    body_ids = neurons["bodyId"].to_numpy(np.int64)
    n = len(body_ids)
    transmitter = best_transmitter_call(body_ids)
    inhibitory = np.isin(transmitter, list(CHLORIDE_TRANSMITTERS))
    tally = pd.Series(transmitter).value_counts()
    print(f"{n:,} neurons; " + ", ".join(f"{name} {k:,}" for name, k in tally.items()), flush=True)

    weights = ds.dataset(WEIGHTS, format="feather").to_table(columns=["body_pre", "body_post", "weight"])
    neuron_set = pa.array(body_ids)
    src = pc.index_in(weights["body_pre"], value_set=neuron_set)   # null where the body is not a neuron
    dst = pc.index_in(weights["body_post"], value_set=neuron_set)
    both = pc.and_(pc.is_valid(src), pc.is_valid(dst))
    src, dst, synapses = (pc.filter(col, both).to_numpy() for col in (src, dst, weights["weight"]))
    print(f"{weights.num_rows:,} weight rows, {len(src):,} between neurons ({time.time() - clock:.0f}s)", flush=True)
    del weights

    warnings.filterwarnings("ignore", message="Sparse CSR tensor support is in beta")
    matrix = torch.sparse_coo_tensor(torch.from_numpy(np.stack([src, dst]).astype(np.int64)),
                                     torch.from_numpy(synapses.astype(np.float64)), (n, n)).coalesce().to_sparse_csr()
    ptr, post, counts = matrix.crow_indices(), matrix.col_indices(), matrix.values()
    pre = torch.repeat_interleave(torch.arange(n), ptr.diff())
    sign = torch.where(torch.from_numpy(inhibitory), -1.0, 1.0).to(torch.float64)
    np.savez(NPZ, body_ids=body_ids, ptr=ptr.numpy(), post=post.numpy().astype(np.int32),
             syn=(counts * sign[pre]).numpy().astype(np.float32))
    total, through_chloride = counts.sum().item(), counts[sign[pre] < 0].sum().item()
    print(f"{post.numel():,} connected pairs carrying {int(total):,} synapses, {through_chloride / total:.1%} inhibitory")

    meta = pd.DataFrame({"row": np.arange(n), "bodyId": body_ids})
    for field in FIELDS:
        meta[field] = neurons[field].to_numpy()
    meta["transmitter"] = transmitter
    meta["inhibitory"] = inhibitory
    meta["synapses_out"] = torch.zeros(n, dtype=torch.float64).index_add_(0, pre, counts).numpy().astype(np.int64)
    meta["synapses_in"] = torch.zeros(n, dtype=torch.float64).index_add_(0, post, counts).numpy().astype(np.int64)
    meta.to_parquet(META, index=False)
    print(f"brain.npz and brain_meta.parquet written in {time.time() - clock:.0f}s")


if __name__ == "__main__":
    build()

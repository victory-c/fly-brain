"""A small made-up brain in the real file layout, for tests and for trying code without the 20 GB build.

    from tests.synthetic_brain import write
    paths = write(tmp_path)            # brain.npz, brain_meta.parquet, web_data/atlas.npz under tmp_path
    brain = Brain(paths["npz"], meta=paths["meta"], atlas=paths["atlas"])

It has the names the code looks up (Shiu's taste GRN types on both sides, MN9_L / MN9_R, a few descending neuron
types) and random background neurons. Its wiring is invented: sugar GRNs excite one interneuron type on their side,
which excites that side's MN9; bitter GRNs inhibit it through a GABAergic one. Positions are random micrometres in a 600 x 300 x 1000 box;
one background neuron in ten has none, as in the real atlas.
"""
from pathlib import Path

import numpy as np
import pandas as pd

GRNS = {"LB3b": "sugar", "LB3c": "sugar", "LB3d": "sugar", "LB4b": "sugar", "LB3a": "water",
        "LB1a": "bitter", "LB1b": "bitter"}
DNS = ["DNp20", "DNg46", "DNp22"]


def write(root, background=400, seed=0):
    rng = np.random.default_rng(seed)
    rows = []  # (type, instance, superclass, class, somaSide, rootSide, transmitter)
    for t in GRNS:
        for side in "LR":
            for _ in range(3):
                rows.append((t, f"{t}_{side}", "cb_sensory", "gustatory", None, side, "acetylcholine"))
    for side in "LR":
        rows.append(("SugarIN", f"SugarIN_{side}", "cb_intrinsic", None, side, None, "acetylcholine"))
        rows.append(("BitterIN", f"BitterIN_{side}", "cb_intrinsic", None, side, None, "gaba"))
        rows.append(("MN9", f"MN9_{side}", "cb_motor", None, side, None, "acetylcholine"))
        for t in DNS:
            rows.append((t, f"{t}_{side}", "descending_neuron", None, side, None, "acetylcholine"))
    superclasses = ["cb_intrinsic", "ol_intrinsic", "vnc_intrinsic", "ascending_neuron"]
    for k in range(background):
        side = "LR"[k % 2]
        rows.append((f"Bg{k // 4:03d}", f"Bg{k // 4:03d}_{side}", superclasses[k % 4], None, side, None,
                     ["acetylcholine", "gaba", "glutamate"][k % 3]))
    n = len(rows)
    meta = pd.DataFrame(rows, columns=["type", "instance", "superclass", "class", "somaSide", "rootSide", "transmitter"])
    meta.insert(0, "bodyId", 10_000 + 7 * np.arange(n, dtype=np.int64))
    meta.insert(0, "row", np.arange(n, dtype=np.int64))
    meta["subclass"] = None
    meta["entryNerve"] = None
    meta["inhibitory"] = meta["transmitter"].isin(["gaba", "glutamate", "histamine"])

    edges = {}

    def link(pre, post, count):
        for i in pre:
            for j in post:
                if i != j:
                    edges[(int(i), int(j))] = float(count)

    def instance(name):
        return meta.index[meta["instance"] == name]

    for side in "LR":
        side_of = (meta["somaSide"] == side) | (meta["rootSide"] == side)
        sugar = meta.index[meta["type"].isin([t for t, g in GRNS.items() if g == "sugar"]) & side_of]
        bitter = meta.index[meta["type"].isin([t for t, g in GRNS.items() if g == "bitter"]) & side_of]
        link(sugar, instance(f"SugarIN_{side}"), 160)
        link(instance(f"SugarIN_{side}"), instance(f"MN9_{side}"), 220)
        link(bitter, instance(f"BitterIN_{side}"), 160)
        link(instance(f"BitterIN_{side}"), instance(f"MN9_{side}"), 300)
    bg = meta.index[meta["type"].str.startswith("Bg")]
    for _ in range(8 * background):
        i, j = rng.choice(bg, 2, replace=False)
        edges.setdefault((int(i), int(j)), float(rng.integers(1, 20)))

    pairs = sorted(edges)
    pre = np.array([p[0] for p in pairs], np.int64)
    post = np.array([p[1] for p in pairs], np.int32)
    counts = np.array([edges[p] for p in pairs], np.float32)
    sign = np.where(meta["inhibitory"].to_numpy(), -1.0, 1.0).astype(np.float32)
    ptr = np.zeros(n + 1, np.int64)
    np.cumsum(np.bincount(pre, minlength=n), out=ptr[1:])
    meta["synapses_out"] = np.bincount(pre, weights=counts, minlength=n).astype(np.int64)
    meta["synapses_in"] = np.bincount(post, weights=counts, minlength=n).astype(np.int64)

    root = Path(root)
    paths = {"npz": root / "brain.npz", "meta": root / "brain_meta.parquet", "atlas": root / "web_data" / "atlas.npz"}
    np.savez(paths["npz"], body_ids=meta["bodyId"].to_numpy(), ptr=ptr, post=post, syn=counts * sign[pre])
    columns = ["row", "bodyId", "type", "instance", "superclass", "class", "subclass", "somaSide", "rootSide",
               "entryNerve", "transmitter", "inhibitory", "synapses_out", "synapses_in"]
    meta[columns].to_parquet(paths["meta"], index=False)

    xyz_um = rng.uniform([0, 0, 0], [600, 300, 1000], size=(n, 3))
    drawn = ~(meta["type"].str.startswith("Bg") & (np.arange(n) % 10 == 0)).to_numpy()
    paths["atlas"].parent.mkdir(parents=True, exist_ok=True)
    xyz = xyz_um[drawn]
    centre, scale = (xyz.max(0) + xyz.min(0)) / 2, 2 / np.ptp(xyz, axis=0).max()
    np.savez(paths["atlas"], xyz=((xyz - centre) * scale).astype(np.float32), row=np.flatnonzero(drawn),
             xyz_um=xyz.astype(np.float32))
    return paths

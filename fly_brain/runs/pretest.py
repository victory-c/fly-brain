"""Transmission pre-test for a wiring-ladder rung (docs/GLOSSARY.md section 7, "Transmission gate").

Does a (rewired) brain still carry the bike's left/right sensory signals to its output neurons, at a sane activity
level? Same setup as runs/probe.py: bike held upright at cruise speed, every sensory population at its cruise rate,
and one population (VS, HS, haltere) gets extra drive on the LEFT in half the brains and on the RIGHT in the other
half. Reports, per population, the whole brain's spike rate and how many descending/motor neurons respond
differently to left and right (|z| > 3), plus the largest |z|.

    python -m runs.pretest --brain results/variants/r4_s1.npz --tag r4_s1 --brains 8
    python -m runs.pretest --tag r0 --brains 8               # the real wiring, for comparison
"""
import argparse
import itertools
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from bike.dynamics import Peloton
from bike.senses import Senses
from brain.connectome import Brain
from brain.engine import PARAMS, W_SYN
from brain.loop import BrainLoop

ROOT = Path(__file__).resolve().parents[1]


def zscores(hz, group, ms):
    """Per-neuron z of mean(group) - mean(rest), Welch SE with ddof=1. The floor (a spread of 1 spike per window in
    each brain) stops neurons that never fire in one group from scoring z = difference / 0."""
    A, C = hz[group], hz[~group]
    floor = (1000.0 / ms) ** 2
    se = np.sqrt((A.var(0, ddof=1) + floor) / len(A) + (C.var(0, ddof=1) + floor) / len(C))
    return (A.mean(0) - C.mean(0)) / se


def balanced_splits(B):
    """Group masks with half of the first B/2 brains and half of the last B/2, each split counted once."""
    h = B // 2
    out = []
    for a in itertools.combinations(range(h), h // 2):
        for b in itertools.combinations(range(h, B), h // 2):
            m = np.zeros(B, bool)
            m[list(a) + list(b)] = True
            if m[0]:
                out.append(m)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain", default=None, help="connectome npz (default brain.npz)")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--pop", nargs="+", default=["VS", "HS", "HALT"])
    ap.add_argument("--extra", type=float, default=30.0)
    ap.add_argument("--brains", type=int, default=8, help="half get the left probe, half the right")
    ap.add_argument("--ms", type=float, default=1000.0)
    ap.add_argument("--warmup-ms", type=float, default=300.0)
    ap.add_argument("--v", type=float, default=4.5)
    ap.add_argument("--w-syn-scale", type=float, default=None, help="default: the calibrated W_SYN (scale 0.47)")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default=None, help="default results/rungs/pretest_<tag>.json")
    a = ap.parse_args()
    dev = ("cuda" if torch.cuda.is_available() else "cpu") if a.device == "auto" else a.device
    meta = pd.read_parquet(ROOT / "brain_meta.parquet")
    senses = Senses(meta, device=dev, lane="hs")
    brain = Brain(a.brain or ROOT / "brain.npz")
    w = W_SYN if a.w_syn_scale is None else PARAMS["w_syn"] * a.w_syn_scale
    B = a.brains - a.brains % 2
    bikes = Peloton(B, device=dev)
    bikes.reset(a.v, 0.0)
    base = senses.population_rates(bikes.state, bikes.psi_dot)
    out_mask = meta.superclass.isin(["descending_neuron", "vnc_motor", "cb_motor"]).to_numpy()
    report = {"brain": a.brain or "brain.npz", "w_syn": w, "brains": B, "ms": a.ms, "extra_hz": a.extra, "pops": {}}
    for pop in a.pop:
        clock = time.time()
        P = base.clone()
        P[: B // 2, senses.names.index(f"{pop}_L")] += a.extra
        P[B // 2:, senses.names.index(f"{pop}_R")] += a.extra
        loop = BrainLoop(brain, B, senses.idx, [], params={"w_syn": w}, device=dev, seed=a.seed)
        loop.set_rates(P @ senses.E)
        loop.run(a.warmup_ms)
        loop.take_counts()
        loop.run(a.ms)
        hz = loop.take_counts().float().cpu().numpy() / (a.ms / 1000.0)  # (B, N)
        left = np.arange(B) < B // 2
        zo = np.abs(zscores(hz, left, a.ms)[out_mask])
        # null: every relabelling that puts half of the left-probed and half of the right-probed brains in each group,
        # so the probe side cancels and only brain-to-brain noise is left
        null = [np.abs(zscores(hz, s, a.ms)[out_mask]) for s in balanced_splits(B)]
        null_counts = np.array([(n > 3).sum() for n in null])
        net = np.ones(brain.n, bool)
        net[senses.idx.cpu().numpy() if torch.is_tensor(senses.idx) else senses.idx] = False
        row = {"spikes_per_s": float(hz.sum(1).mean()), "network_spikes_per_s": float(hz[:, net].sum(1).mean()),
               "network_active": int((hz[:, net].mean(0) > 0).sum()), "active_frac": float((hz.mean(0) > 0).mean()),
               "max_neuron_hz": float(hz.mean(0).max()), "outputs_z3": int((zo > 3).sum()),
               "max_abs_z": float(zo.max()), "out_mean_hz": float(hz[:, out_mask].mean()),
               "outputs_active": int((hz[:, out_mask].mean(0) > 0).sum()),
               "null_outputs_z3_mean": float(null_counts.mean()), "null_outputs_z3_max": int(null_counts.max()),
               "null_max_abs_z": float(max(n.max() for n in null)), "null_splits": len(null),
               "wall_s": round(time.time() - clock, 1)}
        report["pops"][pop] = row
        print(f"{a.tag} {pop} scale {w / PARAMS['w_syn']:.2f}: {row['spikes_per_s']:,.0f} spikes/s, "
              f"{row['network_spikes_per_s']:,.0f} outside the driven neurons ({row['network_active']:,} of them fire), "
              f"outputs |z|>3: {row['outputs_z3']} (null mean {row['null_outputs_z3_mean']:.1f}, max "
              f"{row['null_outputs_z3_max']}), max |z| {row['max_abs_z']:.1f} (null {row['null_max_abs_z']:.1f}) "
              f"({row['wall_s']} s)", flush=True)
    sc = "" if a.w_syn_scale is None else f"_w{a.w_syn_scale:g}"
    out = ROOT / (a.out or f"results/rungs/pretest_{a.tag}{sc}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1))
    print("->", out)


if __name__ == "__main__":
    main()

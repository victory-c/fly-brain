#!/usr/bin/env python3
"""Markdown table of rung rides against the balance gate on the real wiring, generation by generation.

    python3 tools/ride_table.py [--speed 4.5] [--results fly_brain/results]

Rows are generations (0, 1, 2, 3, 5, 8, 10, then every 5); columns are the real wiring's gate runs at that speed
(results/gate/v<V>_s<SEED>/cem.json) and every rung ride at that speed
(results/rungs/<TAG>/[<READOUT>/]v<V>_s<SEED>/cem.json; READOUT is top8, bypass, ... from ride-readout.sbatch).
Each cell is the mean riding time over the 48 riders of that generation, in seconds.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--speed", type=float, default=4.5)
    ap.add_argument("--results", default="fly_brain/results")
    a = ap.parse_args()
    res = ROOT / a.results
    cols = []
    for p in sorted(res.glob(f"gate/v{a.speed}_s*/cem.json")):
        cols.append((f"R0 seed {p.parent.name.split('_s')[1]}", json.loads(p.read_text())))
    for p in sorted(res.glob(f"rungs/**/v{a.speed}_s*/cem.json")):
        tag = "/".join(p.parent.parent.relative_to(res / "rungs").parts)  # <TAG> or <TAG>/<READOUT>
        cols.append((f"{tag} seed {p.parent.name.split('_s')[1]}", json.loads(p.read_text())))
    last = max(len(d["history"]) for _, d in cols) - 1
    gens = sorted({g for g in [0, 1, 2, 3, 5, 8, 10] + list(range(15, last + 1, 5)) + [len(d["history"]) - 1 for _, d in cols] if g <= last})
    print("| Generation | " + " | ".join(n for n, _ in cols) + " |")
    print("|---|" + "---|" * len(cols))
    for g in gens:
        cells = [f"{d['history'][g]['upright_mean']:.2f}" if g < len(d["history"]) else "" for _, d in cols]
        print(f"| {g} | " + " | ".join(cells) + " |")
    print("| generations done | " + " | ".join(str(len(d["history"])) for _, d in cols) + " |")
    print("| finishing 15 s, last generation | " + " | ".join(f"{100 * d['history'][-1]['finish_frac']:.0f}%" for _, d in cols) + " |")
    print("| spikes/s per brain, last generation | " + " | ".join(f"{d['history'][-1]['pop_hz']:,.0f}" for _, d in cols) + " |")
    print("| device | " + " | ".join(d.get("device", "") for _, d in cols) + " |")


if __name__ == "__main__":
    main()

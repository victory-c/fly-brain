#!/usr/bin/env python3
"""Markdown table of the transmission pre-test (runs/pretest.py) from fly_brain/results/rungs/pretest_*_b<N>_w*.json.

    python3 tools/pretest_table.py [--brains 30] [--results fly_brain/results/rungs]

One row per rung and synapse scale. A cell passes the gate (docs/GLOSSARY.md, "Transmission gate") when, for both
the VS and the haltere probe, the lateralised outputs exceed the largest null count and the network rate lies within
2x of the real wiring's at scale 0.47 (21,500 spikes/s, so 10,750 to 43,000).
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LO, HI = 10_750, 43_000
ORDER = ["r0", "r1_s1", "r2_s1", "r3_s1", "r35_s1", "r4_s1", "r5_s1"]
NAMES = {"r0": "R0 real wiring", "r1_s1": "R1 transmitter errors", "r2_s1": "R2 count jitter", "r3_s1": "R3 type-preserving",
         "r35_s1": "R3.5 strength-preserving", "r4_s1": "R4 degree-preserving", "r5_s1": "R5 random"}


def verdict(pops):
    signal = all(p["outputs_z3"] > p["null_outputs_z3_max"] for p in pops.values())
    rates = [p["network_spikes_per_s"] for p in pops.values()]
    if signal and all(LO <= r <= HI for r in rates):
        return "pass"
    why = [] if signal else ["no signal"]
    if any(r < LO for r in rates):
        why.append("too quiet")
    if any(r > HI for r in rates):
        why.append("runaway")
    return "fail: " + ", ".join(why)


def cells(results, brains):
    out = {}
    for p in results.glob(f"pretest_*_b{brains}_w*.json"):
        m = re.fullmatch(rf"pretest_(.+)_b{brains}_w([\d.]+)\.json", p.name)
        out[(m.group(1), float(m.group(2)))] = json.loads(p.read_text())["pops"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brains", type=int, default=30)
    ap.add_argument("--results", default="fly_brain/results/rungs")
    a = ap.parse_args()
    c = cells(ROOT / a.results, a.brains)
    print("| Rung | Scale | Network spikes/s, VS / haltere probe | Lateralised outputs VS / haltere | Null max | Largest abs z (null) | Gate |")
    print("|---|---|---|---|---|---|---|")
    for rung, scale in sorted(c, key=lambda k: (ORDER.index(k[0]) if k[0] in ORDER else 99, k[1])):
        v, h = c[(rung, scale)]["VS"], c[(rung, scale)]["HALT"]
        print(f"| {NAMES.get(rung, rung)} | {scale:g} | {v['network_spikes_per_s']:,.0f} / {h['network_spikes_per_s']:,.0f} | "
              f"{v['outputs_z3']} / {h['outputs_z3']} | {v['null_outputs_z3_max']} / {h['null_outputs_z3_max']} | "
              f"{v['max_abs_z']:.0f} / {h['max_abs_z']:.0f} ({max(v['null_max_abs_z'], h['null_max_abs_z']):.1f}) | {verdict(c[(rung, scale)])} |")


if __name__ == "__main__":
    main()

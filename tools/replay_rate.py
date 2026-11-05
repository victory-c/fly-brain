#!/usr/bin/env python3
"""Population rate of a brain while it rides, from replay traces (runs/ride.py --replay ... --trace).

    python3 tools/replay_rate.py "R0=fly_brain/results/gate/v4.5_s201/ride_slow_mu_trace.json" "R4 x1.2=..." [--window 0.6] [--json out.json]

The replay's own summary (`pop ... sp/s`) averages every brain until the last rider has fallen, fallen riders
included, so replays of different length are not comparable. This prints the mean spikes/s per brain over the first
WINDOW seconds, when (nearly) every rider is still up, next to that whole-replay mean.
"""
import argparse
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def rates(path, window):
    tr = json.loads(Path(path).read_text())["trace"]
    t = np.array([r["t"] for r in tr])
    pop = np.array([r["pop_hz"] for r in tr])
    done = np.array([r["done"] for r in tr])
    w = t <= window + 1e-9
    return {"window_s": window, "rate_window": float(pop[w].mean()), "rate_whole_replay": float(pop.mean()),
            "replay_s": float(t[-1]), "riders": int(pop.shape[1]), "first_fall_s": float(t[done.any(1)][0]) if done.any() else None,
            "fallen_in_window": int(done[w].any(0).sum())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+", help="LABEL=trace.json; the first one is the reference")
    ap.add_argument("--window", type=float, default=0.6)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    out, ref = {}, None
    print(f"| Brain | First {a.window:g} s of riding, spikes/s per brain | Relative to {a.runs[0].split('=')[0]} | Whole replay (its length) | First fall |")
    print("|---|---|---|---|---|")
    for item in a.runs:
        label, path = item.split("=", 1)
        r = rates(path if Path(path).is_absolute() else ROOT / path, a.window)
        ref = ref or r["rate_window"]
        r["relative"] = r["rate_window"] / ref
        out[label] = r
        fall = "none" if r["first_fall_s"] is None else f"{r['first_fall_s']:.2f} s"
        print(f"| {label} | {r['rate_window']:,.0f} | {r['relative']:.2f} | {r['rate_whole_replay']:,.0f} ({r['replay_s']:.2f} s) | {fall} |")
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()

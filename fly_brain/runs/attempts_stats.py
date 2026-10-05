"""Summary numbers of a learning-from-blank run (runs/ride.py --log-attempts DIR), as quoted in bike/README.md.

    python -m runs.attempts_stats [results/relearn/attempts]
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FINISHED, FELL, OFF_ROAD, BAILED = range(4)


def main():
    src = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "results/relearn/attempts")
    gens = json.loads((src / "attempts.json").read_text())["generations"]
    t = [np.array(g["t_end"]) for g in gens]
    d = np.concatenate([g["distance"] for g in gens])
    o = [np.array(g["outcome"]) for g in gens]
    allo = np.concatenate(o)
    records, best = [], -1.0  # as on the page: the first attempt is the baseline record, attempts are numbered from 1
    for k, x in enumerate(d):
        if x > best:
            records.append((k + 1, float(x)))
            best = x
    first, mid, last = 0, min(10, len(gens) - 1), len(gens) - 1
    print(f"{len(gens)} generations, {len(d):,} attempts")
    print(f"gen {first}: {(t[first] <= 1.0).sum()} of {len(t[first])} down within a second, mean {t[first].mean():.1f} s, "
          f"record {d[:len(t[0])].max():.0f} m")
    print(f"gen {mid}: mean {t[mid].mean():.1f} s")
    print(f"gen {last}: {(o[last] == FINISHED).sum()} of {len(o[last])} finish, {(o[last] == FELL).sum()} fall, "
          f"{(o[last] == OFF_ROAD).sum()} leave the road (mean {t[last].mean():.1f} s)")
    print(f"{len(records)} distance records, the last {records[-1][1]:.1f} m at attempt {records[-1][0]:,}" if records else "no records")
    print(f"all attempts: {(allo == FINISHED).sum()} finished, {(allo == FELL).sum()} fell, "
          f"{(allo == OFF_ROAD).sum()} left the road, {(allo == BAILED).sum()} bailed")


if __name__ == "__main__":
    main()

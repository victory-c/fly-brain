#!/usr/bin/env python3
"""Queue the primary design of the Scrambled Brains preregistration (tag prereg-v1, section 5): the hand-picked readout on
R0 and on rewiring draws 3 to 5 of R1, R2 and R3, CEM seeds 211 to 215, 4.5 and 4.0 m/s, 60 generations, 100 rides.

The rides go into CHAINS Slurm dependency chains (afterany), so at most CHAINS of them hold a GPU at a time and a failed
ride does not stop the rest. The order is whole blocks: a seed and speed for every brain, then the next, so a queue cut
short still leaves complete, balanced blocks. A ride whose cem.json already has 60 generations, or which is in the queue
now, is skipped; a ride stopped short by the 340 min cap is resumed by submitting it again, so this can be rerun. Make the
draws first (conf-prep.sbatch). Run it from the root of ~/flybrain:

    python3 tools/submit_confirmatory.py --dry-run
    python3 tools/submit_confirmatory.py [--chains 2] [--after JOBID[,JOBID]] [--first N] [--last N]
"""
import argparse
import json
import subprocess
from pathlib import Path

SEEDS = (211, 212, 213, 214, 215)
SPEEDS = ("4.5", "4.0")
DRAWS = (3, 4, 5)
GENS = 60
MINUTES = 340


def brains():
    yield "brain.npz", "conf_r0"
    for rung in ("r1", "r2", "r3"):
        for draw in DRAWS:
            yield f"results/variants/{rung}_s{draw}.npz", f"conf_{rung}_s{draw}"


def rides():
    return [(v, seed, brain, tag) for seed in SEEDS for v in SPEEDS for brain, tag in brains()]


def generations(tag, v, seed):
    path = Path(f"fly_brain/results/rungs/{tag}/v{v}_s{seed}/cem.json")
    try:
        return len(json.load(open(path))["history"])
    except (OSError, ValueError, KeyError):
        return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chains", type=int, default=2)
    ap.add_argument("--after", default="", help="comma-separated job ids, one per chain: that chain's first ride waits for it (afterany)")
    ap.add_argument("--first", type=int, default=0, help="first ride of the ordered list, 0-based")
    ap.add_argument("--last", type=int, default=None, help="one past the last ride of the ordered list")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    todo = rides()
    assert len(todo) == 100, len(todo)
    after = a.after.split(",") if a.after else []
    tail = [after[c] if c < len(after) else None for c in range(a.chains)]
    queued = set(subprocess.run(["squeue", "-h", "--me", "-o", "%j"], check=True, capture_output=True, text=True).stdout.split())
    submitted = 0
    for i, (v, seed, brain, tag) in enumerate(todo[a.first:a.last], a.first):
        have = generations(tag, v, seed)
        if have >= GENS:
            print(f"{i:3d} have {tag} v{v} s{seed}: {have} generations")
            continue
        name = f"cm-{tag[5:]}-v{v}-s{seed}"
        if name in queued:
            print(f"{i:3d} in the queue: {name}")
            continue
        chain = submitted % a.chains
        cmd = ["sbatch", "--parsable", f"--job-name={name}", f"--export=ALL,GENS={GENS},REQUIRE_CUDA=1"]
        if tail[chain]:
            cmd.append(f"--dependency=afterany:{tail[chain]}")
        cmd += ["ride-rung.sbatch", v, str(seed), brain, tag, str(MINUTES)]
        if a.dry_run:
            print(f"{i:3d} chain {chain}: {' '.join(cmd)}")
        else:
            tail[chain] = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip().split(";")[0]
            print(f"{i:3d} chain {chain}: job {tail[chain]} {tag} v{v} s{seed}")
        submitted += 1
    print(f"{submitted} rides {'would be ' if a.dry_run else ''}queued")


if __name__ == "__main__":
    main()

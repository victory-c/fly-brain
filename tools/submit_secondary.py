#!/usr/bin/env python3
"""Queue the secondary design of the Scrambled Brains preregistration (tag prereg-v1, section 5), 38 rides, 60 generations,
4.5 m/s unless stated: top-32 plus lane on R0 (5 CEM seeds), on R4 (draw 1, seed 211, scale 1.2) and on R1 to R3 (draws 3 to 5,
seed 211); random-32 plus lane on R0 (READOUT_SEED 0 to 2, seed 211); bypass on R0 (seed 211, both speeds); the six model-side
variants with the primary readout (seeds 211 to 213).

Like tools/submit_confirmatory.py: CHAINS afterany chains, GPU required, a ride with 60 generations or already in the queue is
skipped, and rerunning resumes the rides the 340 min cap stopped short. Pass the last job of each primary chain with --after, so
the secondary design runs after the primary one. Run it from the root of ~/flybrain:

    python3 tools/submit_secondary.py --dry-run
    python3 tools/submit_secondary.py --after JOBID,JOBID
"""
import argparse
import json
import os
import subprocess
from pathlib import Path

GENS = 60
MINUTES = 340
SEEDS = (211, 212, 213, 214, 215)
RESULTS = Path("fly_brain/results/rungs")
MODEL = [  # name, synapse scale, MODEL_ARGS (the variants of the model-side pre-test, section 3)
    ("w0.9", "0.423", ""),
    ("w1.1", "0.517", ""),
    ("tmbr18", "", "--t-mbr 18"),
    ("tmbr22", "", "--t-mbr 22"),
    ("tau4.5", "", "--tau 4.5"),
    ("tau5.5", "", "--tau 5.5"),
]


def readout(v, seed, rung, kind, ws="", rseed=0):
    """One ride-readout.sbatch ride: (job name, sbatch arguments, environment, its cem.json)."""
    lane = 12 if kind in ("topk", "randk") else 0
    name = {"topk": "top32", "randk": f"rand32_r{rseed}", "bypass": "bypass"}[kind] + (f"_lane{lane}" if lane else "")
    tag = rung + (f"_w{ws}" if ws else "")
    job = f"sc-{tag}-{name}-v{v}-s{seed}"
    args = ["ride-readout.sbatch", v, str(seed), rung, kind, "32", str(MINUTES), ws, str(rseed)]
    return job, args, {"LANE_K": str(lane)}, RESULTS / tag / name / f"v{v}_s{seed}" / "cem.json"


def rides():
    out = [readout("4.5", s, "r0", "topk") for s in SEEDS]
    out.append(readout("4.5", 211, "r4_s1", "topk", ws="1.2"))
    out += [readout("4.5", 211, "r0", "randk", rseed=r) for r in (0, 1, 2)]
    out += [readout("4.5", 211, f"{r}_s{d}", "topk") for r in ("r1", "r2", "r3") for d in (3, 4, 5)]
    out += [readout(v, 211, "r0", "bypass") for v in ("4.5", "4.0")]
    for variant, ws, model_args in MODEL:
        for seed in SEEDS[:3]:
            tag = f"conf_model_{variant}"
            args = ["ride-rung.sbatch", "4.5", str(seed), "brain.npz", tag, str(MINUTES)] + ([ws] if ws else [])
            out.append((f"sc-model_{variant}-v4.5-s{seed}", args, {"MODEL_ARGS": model_args}, RESULTS / tag / f"v4.5_s{seed}" / "cem.json"))
    return out


def generations(path):
    try:
        return len(json.load(open(path))["history"])
    except (OSError, ValueError, KeyError):
        return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chains", type=int, default=2)
    ap.add_argument("--after", default="", help="comma-separated job ids, one per chain: that chain's first ride waits for it (afterany)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    todo = rides()
    assert len(todo) == 38, len(todo)
    after = a.after.split(",") if a.after else []
    tail = [after[c] if c < len(after) else None for c in range(a.chains)]
    queued = set(subprocess.run(["squeue", "-h", "--me", "-o", "%j"], check=True, capture_output=True, text=True).stdout.split())
    submitted = 0
    for i, (job, args, env, cem) in enumerate(todo):
        have = generations(cem)
        if have >= GENS:
            print(f"{i:3d} have {job}: {have} generations")
            continue
        if job in queued:
            print(f"{i:3d} in the queue: {job}")
            continue
        chain = submitted % a.chains
        cmd = ["sbatch", "--parsable", f"--job-name={job}", f"--export=ALL,GENS={GENS},REQUIRE_CUDA=1"]
        if tail[chain]:
            cmd.append(f"--dependency=afterany:{tail[chain]}")
        cmd += args
        if a.dry_run:
            print(f"{i:3d} chain {chain}: {env} {' '.join(cmd)}")
        else:
            tail[chain] = subprocess.run(cmd, check=True, capture_output=True, text=True, env={**os.environ, **env}).stdout.strip().split(";")[0]
            print(f"{i:3d} chain {chain}: job {tail[chain]} {job}")
        submitted += 1
    print(f"{submitted} rides {'would be ' if a.dry_run else ''}queued")


if __name__ == "__main__":
    main()

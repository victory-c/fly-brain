#!/usr/bin/env python3
"""Queue everything the Scrambled Brains preregistration (tag prereg-v1) still needs as ONE Slurm dependency chain, so this
user holds one job at a time on the node. The cluster's default QoS says one running job per user (MaxJobsPU=1), though
Slurm does not enforce it here (AccountingStorageEnforce=none); this keeps to it anyway (decided 2026-11-11).

Order, each link waiting for the one before it (afterany, so a failed link does not stop the chain):
  1. the held-out replays (section 5) of primary rides that are finished or riding now and have none yet;
  2. each remaining primary ride (tools/submit_confirmatory.py's order), followed by its held-out replays;
  3. the 38 secondary rides (tools/submit_secondary.py);
  4. prediction 3's replays (tools/heldout.py --pred3's four rides, replay seed 201).
A ride with 60 generations, or a job whose name is already in the queue, is skipped, as are held-out replays already on disk.
A ride the 340 min cap stops short leaves its held-out link to fail (heldout.py refuses fewer than 60 generations); rerun
this script and it queues that ride again with its replays. Run it from the root of ~/flybrain:

    python3 tools/submit_serial.py --dry-run [--running-only]
    python3 tools/submit_serial.py --after JOBID            the whole list as one dependency chain

Relay mode (since 2026-11-11, so the queue shows only what is next): --next submits only the first link that is left, plus
a one-CPU relay job (serial-next.sbatch) that waits for it (afterany) and runs --next again. Each pass works out what is
left from the results on disk, so a ride the 340 min cap stopped short is queued again (it resumes), and a link that has
been submitted MAX_TRIES times is skipped and named in the relay's log. --next does nothing while a link of this queue
(cm-, sc-, ho-) is already in Slurm, unless --after is given, so two relays cannot run two links at once.

    python3 tools/submit_serial.py --next [--after JOBID] [--dry-run]
    tail logs/serial-next-*.out                             what each relay did; logs/serial-tries.json counts submissions
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import heldout  # noqa: E402
import submit_confirmatory as sc  # noqa: E402
import submit_secondary as ss  # noqa: E402

GENS = 60
MAX_TRIES = 3
TRIES = Path("logs/serial-tries.json")
PREFIXES = ("cm-", "sc-", "ho-")


def has_replays(cem, conditions):
    return all((Path(cem).parent / "heldout" / f"{c}.json").exists() for c in conditions)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--after", default="", help="job id the chain's first link waits for (afterany)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--running-only", action="store_true", help="count only running jobs as queued (to preview before cancelling the pending ones)")
    ap.add_argument("--next", action="store_true", help="relay mode: submit the first link left and a relay job after it")
    a = ap.parse_args()
    state = ["-t", "R"] if a.running_only else []
    queued = set(subprocess.run(["squeue", "-h", "--me", "-o", "%j", *state], check=True, capture_output=True, text=True).stdout.split())
    tail = a.after or None
    links = []  # (job name, sbatch arguments, extra environment)

    def ho(name, cem, conditions):
        if name not in queued and not has_replays(cem, conditions):
            links.append((name, ["heldout.sbatch", ",".join(conditions), str(cem)], {}))

    primary = list(zip(sc.rides(), heldout.primary()))
    assert len(primary) == 100
    later = []
    for (v, seed, brain, tag), (ho_name, cem) in primary:
        ride = f"cm-{tag[5:]}-v{v}-s{seed}"
        if sc.generations(tag, v, seed) >= GENS or ride in queued:
            ho(ho_name, cem, heldout.SECTION5)  # 1: finished or riding now
        else:
            later.append((ride, ["ride-rung.sbatch", v, str(seed), brain, tag, str(sc.MINUTES)], {"GENS": str(GENS), "REQUIRE_CUDA": "1"}, ho_name, cem))
    for ride, args, env, ho_name, cem in later:  # 2
        links.append((ride, args, env))
        links.append((ho_name, ["heldout.sbatch", ",".join(heldout.SECTION5), str(cem)], {}))
    for job, args, env, cem in ss.rides():  # 3
        if ss.generations(cem) < GENS and job not in queued:
            links.append((job, args, {**env, "GENS": str(GENS), "REQUIRE_CUDA": "1"}))
    for name, cem in heldout.pred3():  # 4
        ho(name, cem, ("seed201",))

    if a.next:
        return relay(a, queued, links)
    for i, (name, args, env) in enumerate(links):
        cmd = ["sbatch", "--parsable", f"--job-name={name}"]
        if "GENS" in env:
            cmd.append(f"--export=ALL,GENS={env['GENS']},REQUIRE_CUDA=1")
        if tail:
            cmd.append(f"--dependency=afterany:{tail}")
        cmd += args
        if a.dry_run:
            extra = {k: v for k, v in env.items() if k not in ("GENS", "REQUIRE_CUDA")}
            print(f"{i:3d} {extra or ''} {' '.join(cmd)}")
            tail = f"<{i}>"
        else:
            tail = subprocess.run(cmd, check=True, capture_output=True, text=True, env={**os.environ, **env}).stdout.strip().split(";")[0]
            print(f"{i:3d} job {tail} {name}", flush=True)
    print(f"{len(links)} links {'would be ' if a.dry_run else ''}queued")


def relay(a, queued, links):
    busy = sorted(n for n in queued if n.startswith(PREFIXES))
    if busy and not a.after:
        print(f"{len(busy)} links already in Slurm ({busy[0]}{', ...' if len(busy) > 1 else ''}); nothing submitted")
        return
    try:
        tries = json.loads(TRIES.read_text())
    except (OSError, ValueError):
        tries = {}
    skipped = [n for n, _, _ in links if tries.get(n, 0) >= MAX_TRIES]
    if skipped:
        print(f"skipped after {MAX_TRIES} submissions: {', '.join(skipped)}")
    left = [l for l in links if tries.get(l[0], 0) < MAX_TRIES]
    if not left:
        print("nothing left to run; the relay stops here")
        return
    name, args, env = left[0]
    cmd = ["sbatch", "--parsable", f"--job-name={name}"]
    if "GENS" in env:
        cmd.append(f"--export=ALL,GENS={env['GENS']},REQUIRE_CUDA=1")
    if a.after:
        cmd.append(f"--dependency=afterany:{a.after}")
    cmd += args
    print(f"{len(left)} links left; next: {name} (try {tries.get(name, 0) + 1})")
    if a.dry_run:
        print(" ".join(cmd), "\nthen: sbatch --dependency=afterany:<it> serial-next.sbatch")
        return
    job = subprocess.run(cmd, check=True, capture_output=True, text=True, env={**os.environ, **env}).stdout.strip().split(";")[0]
    tries[name] = tries.get(name, 0) + 1
    TRIES.write_text(json.dumps(tries, indent=1))
    nxt = subprocess.run(["sbatch", "--parsable", f"--dependency=afterany:{job}", "serial-next.sbatch"], check=True, capture_output=True,
                         text=True).stdout.strip().split(";")[0]
    print(f"submitted {name} as job {job}; relay job {nxt} waits for it", flush=True)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Track C replays of the Scrambled Brains preregistration (tag prereg-v1, section 7): spike counts of one finished search.

Each replay rides one search's final CEM mean (`mu` of cem.json) under that search's ride settings (tools/heldout.py ride_args),
then overrides: 48 riders, 15 s, replay seed 201, no off-road rule, CPU, and a 10 ms brain recording. It writes to <cem dir>/trackc/:

    decoder.json      {best_theta: mu, decoder_names}: the decoder the replay reads
    counts10.npz      descending + wing-motor spike counts per 10 ms bin (tools/track_c.py --sum-to-ms 100)
    probe100.npz      with --rows: counts of those rows per 100 ms bin (tools/track_c_probe.py)
    trace.json        the ride trace (about 95 MB; a .gitignore here keeps it and probe100.npz out of sync.sh's commits)

A replay whose outputs all exist is skipped, so a cut job can be submitted again. --pilot-r0 instead repeats the pilot R0 replay
(job 38178) at 10 ms bins, for checking that 10 bins sum to its 100 ms counts and that the trace is unchanged. From ~/flybrain:

    python3 tools/track_c_replay.py --dry-run fly_brain/results/rungs/conf_r0/v4.5_s211/cem.json
    python3 tools/track_c_replay.py --pilot-r0 --dry-run
    sbatch -J tc-r0 trackc.sbatch [--rows ROWS.json] fly_brain/results/rungs/conf_r0/v4.5_s211/cem.json ...      (on the node)
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FLY = HERE.parent / "fly_brain"
sys.path.insert(0, str(HERE))
from heldout import GENS, RIDERS, SECONDS, ride_args  # noqa: E402

SEED, BIN_MS = 201, 10
# job 38178 (trackc-r0), from sacct SubmitLine; its decoder lives only in the pilot cache
PILOT = Path.home() / ".cache" / "sb-replay"
# the traces (~95 MB each, 13 replays) and probe counts stay out of git: sync.sh commits new files under fly_brain/results
GITIGNORE = "trace.json\nprobe100.npz\n"
PILOT_R0 = ["--readout", "lane", "--lane", "hs", "--lane-filter", "results/gate/v4.5_s201/probe.json", "--tau-lane-ms", "300", "--center-batch",
            "--gains", "hs_heading=150,hs_lane=50", "--v0", "4.5", "--gust", "5", "--offroad", "0", "--lane-penalty", "0.02",
            "--riders", "48", "--seconds", "15", "--seed", "201", "--replay", str(PILOT / "r0_s201_mu.json")]


def outputs(out, rows):
    """The files a replay writes into `out`, by role."""
    files = {"counts": out / "counts10.npz", "trace": out / "trace.json"}
    if rows:
        files["probe"] = out / "probe100.npz"
    return files


def record_args(files, rows):
    """The recording flags: 10 ms site counts, 100 ms probe counts with rows, and the trace."""
    args = ["--brain-bin-ms", str(BIN_MS), "--counts-out", str(files["counts"])]
    if rows:
        args += ["--probe-rows", str(Path(rows).resolve()), "--probe-counts-out", str(files["probe"])]
    return args + ["--trace", str(files["trace"])]


def plan(cem_path, rows=None):
    """(command, decoder json body, output dir, output files) of one search's Track C replay."""
    cem_path = Path(cem_path).resolve()
    d = json.loads(cem_path.read_text())
    cfg, names = d["config"], d["decoder_names"]
    if len(d["history"]) < GENS:
        raise SystemExit(f"{cem_path}: {len(d['history'])} generations, not {GENS}")
    if (cfg["riders"], cfg["seconds"]) != (RIDERS, SECONDS):
        raise SystemExit(f"{cem_path}: searched with {cfg['riders']} riders x {cfg['seconds']} s")
    out = cem_path.parent / "trackc"
    files = outputs(out, rows)
    decoder = {"best_theta": list(d["mu"]), "decoder_names": names, "note": f"final CEM mean of {cem_path}, Track C replay seed {SEED}"}
    cmd = [sys.executable, "-m", "runs.ride", "--replay", str(out / "decoder.json"), "--riders", str(RIDERS), "--seconds", str(SECONDS),
           "--v0", str(cfg["v0"]), "--seed", str(SEED)] + ride_args(cfg) + ["--offroad", "0", "--device", "cpu"] + record_args(files, rows)
    return cmd, decoder, out, files


def plan_pilot(rows=None):
    """The 38178 command at 10 ms bins, writing trackc10_r0_* next to the pilot's files."""
    files = {"counts": PILOT / "trackc10_r0_counts.npz", "trace": PILOT / "trackc10_r0_trace.json"}
    if rows:
        files["probe"] = PILOT / "trackc10_r0_probe100.npz"
    # --device cpu: what 38178's "auto" picked (its log says "48 riders on cpu"), pinned so a visible GPU cannot change the path
    cmd = [sys.executable, "-m", "runs.ride"] + PILOT_R0 + record_args(files, rows) + ["--out", str(PILOT / "unused_trackc10_r0.json"),
                                                                                       "--device", "cpu"]
    return cmd, None, PILOT, files


def run(cmd, decoder, out, files, dry_run):
    name = out.parent if decoder is not None else "pilot R0 (38178)"
    if all(f.exists() for f in files.values()):
        print(f"have {out}", flush=True)
        return
    print(f"== {name}", flush=True)
    print(" ".join(cmd), flush=True)
    if dry_run:
        return
    out.mkdir(exist_ok=True)
    if decoder is not None:
        (out / "decoder.json").write_text(json.dumps(decoder))
        (out / ".gitignore").write_text(GITIGNORE)
    for f in files.values():  # a cut run leaves no half set behind
        f.unlink(missing_ok=True)
    (files["trace"].parent / (files["trace"].stem + "_command.txt")).write_text(" ".join(cmd) + "\n")
    r = subprocess.run(cmd, cwd=FLY, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stdout[-2000:] + r.stderr[-2000:])
    print("\n".join(line for line in r.stdout.splitlines() if line.startswith(("replay", "counts", "probe", "trace")))[:800], flush=True)
    missing = [str(f) for f in files.values() if not f.exists()]
    if missing:
        raise SystemExit(f"ride finished without {missing}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cem", nargs="*", help="finished searches' cem.json")
    ap.add_argument("--rows", default=None, help="json of neuron rows (tools/track_c_probe.py) to record at 100 ms to probe100.npz")
    ap.add_argument("--pilot-r0", action="store_true", help="repeat the pilot R0 replay (job 38178) at 10 ms bins instead")
    ap.add_argument("--dry-run", action="store_true", help="print the commands, write nothing")
    a = ap.parse_args()
    if not a.cem and not a.pilot_r0:
        ap.error("give cem.json files or --pilot-r0")
    rows = str(Path(a.rows).resolve()) if a.rows else None  # relative to where it was called from, before the chdir
    if rows and not Path(rows).is_file():
        ap.error(f"no rows file {rows}")
    cems = [Path(c).resolve() for c in a.cem]
    os.chdir(HERE.parent)
    plans = ([plan_pilot(rows)] if a.pilot_r0 else []) + [plan(c, rows) for c in cems]
    for p in plans:
        run(*p, a.dry_run)


if __name__ == "__main__":
    main()

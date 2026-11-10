#!/usr/bin/env python3
"""Held-out replays of the Scrambled Brains preregistration (tag prereg-v1): section 5's descriptive tests and prediction 3.

Each test replays one finished search's final mean decoder (the CEM mean `mu` of cem.json, in decoder coordinates) under the
exact settings of that search: every setting is taken from the `config` recorded in cem.json, so the replay reads the same
brain, scale, readout, lane filter and centring as the search did. 48 riders, 15 s, off-road rule as searched.

Conditions:
    gust301, gust302   training speed, unseen gust seeds
    vplus, vminus      training speed +0.5 / -0.5 m/s, pedal bias reset to hold the test speed, replay seed 301 (section 5 gives
                       the seeds for the gust test only; this one reuses the first)
    seed201            training speed, replay seed 201 (prediction 3)

A condition writes <run>/heldout/<condition>.json: per-rider riding time and offset, and the outcome counts of
tools/replay_summary.py. A condition with a file is skipped, so a cut job can be submitted again. From the root of ~/flybrain:

    python3 tools/heldout.py submit --dry-run           the primary rides that have 60 generations, CPU, one chain
    python3 tools/heldout.py submit --pred3             prediction 3's four rides instead
    python3 tools/heldout.py table                      median over each rung's runs, per speed and condition
    venv-cuda/bin/python tools/heldout.py run [--conditions a,b] fly_brain/results/rungs/.../cem.json ...      (on the node)
"""
import argparse
import json
import math
import os
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FLY = HERE.parent / "fly_brain"
sys.path.insert(0, str(HERE))
from replay_summary import outcome  # noqa: E402

GENS = 60
RIDERS, SECONDS = 48, 15.0
CONDITIONS = {"gust301": (301, 0.0), "gust302": (302, 0.0), "vplus": (301, 0.5), "vminus": (301, -0.5), "seed201": (201, 0.0)}
SECTION5 = ("gust301", "gust302", "vplus", "vminus")
RESULTS = Path("fly_brain/results/rungs")
# cem.json config keys that belong to the search, not to the ride, or that this script sets itself
NOT_REPLAYED = {"generations", "max_minutes", "resume", "out", "init", "init_theta", "sigma_new", "sigma0", "sigma_lane_filter", "sigma_min",
                "sigma_pedal", "elite", "ridge", "zbar", "dagger", "dagger_beta0", "replay", "trace", "brain_out", "counts_out", "brain_bin_ms",
                "log_attempts", "oracle", "open_loop", "quiet", "device", "seed", "v0", "riders", "seconds"}


def ride_args(cfg):
    """The runs/ride.py flags of everything in a search's config that shapes a ride."""
    args = []
    for key, value in cfg.items():
        if key in NOT_REPLAYED or value is None or value is False:
            continue
        flag = "--" + key.replace("_", "-")
        args += [flag] if value is True else [flag, str(value)]
    return args


def pedal_bias(v):
    """The pedal bias that holds speed v, as in ride-rung.sbatch's init_hold."""
    sys.path.insert(0, str(FLY))
    from bike.dynamics import Peloton
    from bike.tarmac import G, LONGITUDINAL as L
    mT = Peloton(1).mT
    P = v * (0.5 * L["rho"] * L["CdA"] * v * v + L["Crr"] * mT * G) / L["drivetrain"]
    return math.log(P / (250.0 - P))


def replay(cem_path, condition):
    cem_path = Path(cem_path).resolve()
    out = cem_path.parent / "heldout" / f"{condition}.json"
    if out.exists():
        print(f"have {out}", flush=True)
        return
    d = json.loads(cem_path.read_text())
    cfg, names = d["config"], d["decoder_names"]
    if len(d["history"]) < GENS:
        raise SystemExit(f"{cem_path}: {len(d['history'])} generations, not {GENS}")
    if (cfg["riders"], cfg["seconds"]) != (RIDERS, SECONDS):
        raise SystemExit(f"{cem_path}: searched with {cfg['riders']} riders x {cfg['seconds']} s")
    seed, dv = CONDITIONS[condition]
    v, theta, i = cfg["v0"] + dv, list(d["mu"]), names.index("pedal:bias")
    if abs(theta[i] - pedal_bias(cfg["v0"])) > 1e-3:  # the pedal is frozen in the search, so this formula must give its value
        raise SystemExit(f"{cem_path}: pedal bias {theta[i]} is not the value that holds {cfg['v0']} m/s")
    if dv:
        theta[i] = pedal_bias(v)
    out.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        decoder, trace = Path(tmp) / "decoder.json", Path(tmp) / "trace.json"
        decoder.write_text(json.dumps({"best_theta": theta, "decoder_names": names, "note": f"final CEM mean of {cem_path}, {condition}"}))
        cmd = [sys.executable, "-m", "runs.ride", "--replay", str(decoder), "--trace", str(trace), "--riders", str(RIDERS), "--seconds", str(SECONDS),
               "--seed", str(seed), "--v0", str(v)] + ride_args(cfg)
        print(f"== {cem_path.parent}: {condition}, v {v}, seed {seed}", flush=True)
        run = subprocess.run(cmd, cwd=FLY, capture_output=True, text=True)
        if run.returncode:
            raise SystemExit(run.stdout[-2000:] + run.stderr[-2000:])
        print("\n".join(line for line in run.stdout.splitlines() if line.startswith("replay"))[:400], flush=True)
        r = json.loads(trace.read_text())["result"]
    summary = {"condition": condition, "replay_seed": seed, "v0": v, "training_v0": cfg["v0"], "decoder": "final CEM mean (mu)",
               "device": "cuda" if "cuda" in run.stdout.split(" riders on ")[-1][:8] else "cpu", "outcome": outcome(r, SECONDS, cfg["offroad"]),
               **{k: r[k] for k in ("upright", "lateral", "bailed") if k in r}}
    tmp_out = out.with_suffix(".json.tmp")
    tmp_out.write_text(json.dumps(summary))
    tmp_out.replace(out)
    print(json.dumps(summary["outcome"]), flush=True)


def primary():
    import submit_confirmatory as sc
    return [(f"ho-{tag[5:]}-v{v}-s{seed}", RESULTS / tag / f"v{v}_s{seed}" / "cem.json") for v, seed, _, tag in sc.rides()]


def pred3():
    r0 = RESULTS / "r0"
    return [("ho-r4-top32", RESULTS / "r4_s1_w1.2" / "top32_lane12" / "v4.5_s211" / "cem.json")] + [
        (f"ho-r0-rand32-r{r}", r0 / f"rand32_r{r}_lane12" / "v4.5_s211" / "cem.json") for r in (0, 1, 2)]


def generations(path):
    try:
        return len(json.load(open(path))["history"])
    except (OSError, ValueError, KeyError):
        return 0


def submit(a):
    conditions = ("seed201",) if a.pred3 else SECTION5
    queued = set(subprocess.run(["squeue", "-h", "--me", "-o", "%j"], check=True, capture_output=True, text=True).stdout.split())
    tail, submitted = a.after, 0
    for name, cem in (pred3() if a.pred3 else primary()):
        if generations(cem) < GENS or name in queued or all((cem.parent / "heldout" / f"{c}.json").exists() for c in conditions):
            continue
        cmd = ["sbatch", "--parsable", f"--job-name={name}"]
        if tail:
            cmd.append(f"--dependency=afterany:{tail}")
        cmd += ([] if not a.gpu else ["--gres=gpu:1", "--cpus-per-task=8", "--mem=16G"]) + ["heldout.sbatch", ",".join(conditions), str(cem)]
        print(" ".join(cmd))
        if not a.dry_run:
            tail = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip().split(";")[0]
        submitted += 1
    print(f"{submitted} jobs {'would be ' if a.dry_run else ''}queued")


def table():
    groups = {}
    for name, cem in primary():
        for c in SECTION5:
            f = cem.parent / "heldout" / f"{c}.json"
            if f.exists():
                tag = cem.parent.parent.name
                rung = tag.split("_")[1]
                groups.setdefault((rung, cem.parent.name.split("_")[0], c), []).append(json.load(open(f))["outcome"]["upright_mean"])
    print("| Rung | Trained at | Condition | Runs | Median riding time (s) |\n|---|---|---|---|---|")
    for (rung, v, c), values in sorted(groups.items()):
        print(f"| {rung} | {v} | {c} | {len(values)} | {statistics.median(values):.2f} |")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--conditions", default=",".join(SECTION5))
    r.add_argument("cem", nargs="+")
    s = sub.add_parser("submit")
    s.add_argument("--pred3", action="store_true")
    s.add_argument("--gpu", action="store_true")
    s.add_argument("--after", default="", help="job id the first replay waits for (afterany)")
    s.add_argument("--dry-run", action="store_true")
    sub.add_parser("table")
    a = ap.parse_args()
    os.chdir(HERE.parent)
    if a.cmd == "run":
        for cem in a.cem:
            for condition in a.conditions.split(","):
                replay(cem, condition)
    elif a.cmd == "submit":
        submit(a)
    else:
        table()


if __name__ == "__main__":
    main()

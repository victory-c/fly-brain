#!/usr/bin/env python3
"""Track C on the 13 confirmatory brains of the Scrambled Brains preregistration (tag prereg-v1, section 7): which brains,
where their replays and screens are, and the three analyses run over all of them (trackc-analysis.sbatch, one relay link each).

Brains: R0, R1 to R3 draws 3 to 5, and the R3.5, R4 and R5 single rides at their ride scales, each the final CEM mean of seed
211 at 4.5 m/s replayed by tools/track_c_replay.py into <run>/trackc/ (counts10.npz, probe100.npz, trace.json). Outputs are
small jsons in fly_brain/results/track_c/confirmatory/, <brain>_<mode>.json; a brain whose output exists is skipped, so a cut
job can be submitted again.

    n90       tools/track_c.py --sum-to-ms 100 --primary-ref own              (10 ms counts summed to the preregistered 100 ms)
    calcium   tools/track_c_calcium.py with its defaults                       (needs the 10 ms counts)
    probe     tools/track_c_probe.py fit on probe100.npz (already 100 ms)    (needs this brain's n90 output for the site R^2)

From the root of ~/flybrain (pandas with pyarrow: the compute venv), on the node:

    venv-cuda/bin/python tools/track_c_all.py n90|calcium|probe [--dry-run] [--only r0,r1_s3]
    python3 tools/track_c_all.py status                                       what exists, per brain (login VM, no numpy)
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNGS = Path("fly_brain/results/rungs")
SCREENS = RUNGS / "screens"
TC = Path("fly_brain/results/track_c/confirmatory")
PROBE_ROWS = TC / "probe_rows.json"
VERIFY = TC / "verify.json"
RUN = "v4.5_s211"
MODES = ("n90", "calcium", "probe")


def _brains():
    """(short name, results/rungs tag, screen stem) of the 13 confirmatory brains, in ladder order."""
    yield "r0", "conf_r0", "r0"
    for rung in ("r1", "r2", "r3"):
        for draw in (3, 4, 5):
            yield f"{rung}_s{draw}", f"conf_{rung}_s{draw}", f"{rung}_s{draw}"
    # single rides at their ride scales; the screens follow screen-rungs.sbatch's naming (<rung>[_w<scale>])
    yield "r35_s1_w0.47_cpu", "conf_r35_s1_w0.47_cpu", "r35_s1"   # default scale 0.47: no _w suffix
    yield "r4_s1_w1.2_cpu", "conf_r4_s1_w1.2_cpu", "r4_s1_w1.2"
    yield "r5_s1_w2_cpu", "conf_r5_s1_w2_cpu", "r5_s1_w2"


BRAINS = list(_brains())
assert len(BRAINS) == 13


def cem(tag):
    return RUNGS / tag / RUN / "cem.json"


def replay_files(tag):
    """What tools/track_c_replay.py --rows writes for one brain."""
    d = RUNGS / tag / RUN / "trackc"
    return {"counts": d / "counts10.npz", "probe": d / "probe100.npz", "trace": d / "trace.json"}


def screen(stem):
    return SCREENS / f"{stem}.parquet"


def output(short, mode):
    return TC / f"{short}_{mode}.json"


def inputs(short, tag, stem, mode):
    """The files one brain's analysis reads (for probe, also that brain's n90 output)."""
    f = replay_files(tag)
    if mode == "n90":
        return [f["counts"], f["trace"], screen(stem)]
    if mode == "calcium":
        return [f["counts"], f["trace"], screen(stem)]
    return [f["probe"], f["trace"], PROBE_ROWS, output(short, "n90")]


def command(short, tag, stem, mode, out):
    f = replay_files(tag)
    py = [sys.executable]
    if mode == "n90":
        return py + [str(HERE / "track_c.py"), str(f["counts"]), str(f["trace"]), str(screen(stem)), str(out),
                     "--sum-to-ms", "100", "--primary-ref", "own"]
    if mode == "calcium":
        return py + [str(HERE / "track_c_calcium.py"), str(f["counts"]), str(f["trace"]), str(screen(stem)), str(out)]
    # probe100.npz is recorded at 100 ms already, so no --sum-to-ms
    return py + [str(HERE / "track_c_probe.py"), "fit", str(f["probe"]), str(f["trace"]), str(PROBE_ROWS),
                 str(output(short, "n90")), str(out)]


def run_mode(mode, only=None, dry_run=False):
    TC.mkdir(parents=True, exist_ok=True)
    failed = []
    for short, tag, stem in BRAINS:
        if only and short not in only:
            continue
        out = output(short, mode)
        if out.exists():
            print(f"have {out}", flush=True)
            continue
        missing = [str(p) for p in inputs(short, tag, stem, mode) if not p.exists()]
        if missing:
            print(f"!! {short} {mode}: missing {', '.join(missing)}", flush=True)
            failed.append(short)
            continue
        part = out.with_name(out.stem + ".part.json")  # renamed only when the tool finished, so a cut job leaves no output
        cmd = command(short, tag, stem, mode, part)
        print(f"== {short} {mode}\n{' '.join(cmd)}", flush=True)
        if dry_run:
            continue
        r = subprocess.run(cmd)
        if r.returncode or not part.exists():
            print(f"!! {short} {mode}: exit {r.returncode}", flush=True)
            part.unlink(missing_ok=True)
            failed.append(short)
            continue
        part.replace(out)
        print(f"-> {out}", flush=True)
    if failed:
        raise SystemExit(f"{mode}: failed or missing inputs for {', '.join(failed)}")


def status():
    print(f"verify: {'yes' if VERIFY.exists() else 'no'}  probe rows: {'yes' if PROBE_ROWS.exists() else 'no'}")
    for short, tag, stem in BRAINS:
        f = replay_files(tag)
        have = {k: v.exists() for k, v in f.items()}
        print(f"{short:18s} replay {''.join('x' if have[k] else '.' for k in ('counts', 'probe', 'trace'))}  screen "
              f"{'x' if screen(stem).exists() else '.'} {stem:12s} " + " ".join(f"{m}:{'x' if output(short, m).exists() else '.'}" for m in MODES))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=MODES + ("status",))
    ap.add_argument("--only", default="", help="comma-separated short names (e.g. r0,r1_s3)")
    ap.add_argument("--dry-run", action="store_true", help="print the commands, run nothing")
    a = ap.parse_args()
    os.chdir(HERE.parent)
    if a.mode == "status":
        return status()
    run_mode(a.mode, set(a.only.split(",")) - {""}, a.dry_run)


if __name__ == "__main__":
    main()

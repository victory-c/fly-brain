#!/usr/bin/env python3
"""Check the 10 ms Track C recording against the pilot (Scrambled Brains, Track C plan section 1), before any confirmatory replay.

`tools/track_c_replay.py --pilot-r0` repeats the pilot R0 replay (job 38178) with the new recorder at --brain-bin-ms 10 and writes
~/.cache/sb-replay/trackc10_r0_{counts.npz,trace.json}. This compares them with the pilot's 100 ms files there:

    counts   summing each block of 10 consecutive 10 ms bins (an incomplete tail dropped) reproduces trackc_r0_counts.npz
             exactly: same rows, same site labels, same number of 100 ms bins and riders, every count equal
    trace    the new trace json equals trackc_r0_trace.json except result.wall, the episode's wall-clock seconds (byte for
             byte is reported too, but two runs of one replay never match there); if not, what differs (top-level keys, the
             first differing control step and field, the largest state difference)

and writes fly_brain/results/track_c/confirmatory/verify.json {ok, checks, date}. ok is true only if both checks pass; the
relay (tools/submit_serial.py) queues the 13 confirmatory replays only when it is true, and stops Track C when it is false.
Exit status 1 when not ok. A missing input file or a crash writes no verify.json (no verdict), so the relay can try again.
trackc.sbatch runs this after every --pilot-r0 replay. From ~/flybrain (numpy):

    venv-cuda/bin/python tools/track_c_verify.py [--new-counts ... --ref-counts ... --new-trace ... --ref-trace ... --out ...]
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PILOT = Path.home() / ".cache" / "sb-replay"
OUT = Path("fly_brain/results/track_c/confirmatory/verify.json")
BLOCK = 10


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def check_counts(new_path, ref_path):
    new, ref = np.load(new_path), np.load(ref_path)
    c = {"new_file": str(new_path), "ref_file": str(ref_path), "new_bin_ms": float(new["bin_ms"]), "ref_bin_ms": float(ref["bin_ms"]),
         "block": BLOCK}
    nc, rc = new["counts"], ref["counts"]
    nb = nc.shape[0] // BLOCK
    c.update(new_shape=list(nc.shape), ref_shape=list(rc.shape), blocks=int(nb), dropped_tail_bins=int(nc.shape[0] - nb * BLOCK))
    c["bin_ms_ok"] = abs(c["new_bin_ms"] * BLOCK - c["ref_bin_ms"]) < 1e-6
    c["rows_equal"] = bool(new["rows"].shape == ref["rows"].shape and np.array_equal(new["rows"], ref["rows"]))
    c["site_equal"] = bool(new["site"].shape == ref["site"].shape and np.array_equal(new["site"].astype(str), ref["site"].astype(str)))
    summed = nc[:nb * BLOCK].reshape(nb, BLOCK, *nc.shape[1:]).sum(1, dtype=np.int64)
    c["shape_equal"] = list(summed.shape) == list(rc.shape)
    if c["shape_equal"]:
        diff = summed - rc.astype(np.int64)
        c["counts_equal"] = bool(not diff.any())
        c["cells_differing"] = int(np.count_nonzero(diff))
        c["max_abs_diff"] = int(np.abs(diff).max()) if diff.size else 0
        if not c["counts_equal"]:
            b, r, n = np.unravel_index(int(np.flatnonzero(diff)[0]), diff.shape)
            c["first_difference"] = {"bin": int(b), "rider": int(r), "neuron_col": int(n), "new": int(summed[b, r, n]), "ref": int(rc[b, r, n])}
    else:
        c["counts_equal"] = False
    c["spikes_new"], c["spikes_ref"] = int(nc.sum(dtype=np.int64)), int(rc.sum(dtype=np.int64))
    c["spikes_new_in_blocks"] = int(summed.sum())
    c["ok"] = bool(c["bin_ms_ok"] and c["rows_equal"] and c["site_equal"] and c["shape_equal"] and c["counts_equal"])
    return c


def trace_differences(new, ref, limit=20):
    """What differs between two parsed traces: top-level keys, then within `trace` the first differing step and its fields."""
    out = []
    for k in sorted(set(new) | set(ref)):
        if k not in new or k not in ref:
            out.append({"key": k, "only_in": "new" if k in new else "ref"})
        elif k != "trace" and new[k] != ref[k]:
            out.append({"key": k, "new": str(new[k])[:300], "ref": str(ref[k])[:300]})
    tn, tr = new.get("trace", []), ref.get("trace", [])
    if tn != tr:
        d = {"key": "trace", "steps_new": len(tn), "steps_ref": len(tr)}
        first = next((i for i, (a, b) in enumerate(zip(tn, tr)) if a != b), None)
        if first is not None:
            a, b = tn[first], tr[first]
            d["first_differing_step"] = first
            d["t"] = a.get("t")
            d["fields"] = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))[:limit]
        try:  # the largest difference in the bike state over the common steps
            n = min(len(tn), len(tr))
            sn = np.array([s["state"] for s in tn[:n]], dtype=np.float64)
            sr = np.array([s["state"] for s in tr[:n]], dtype=np.float64)
            if sn.shape == sr.shape:
                dd = np.abs(sn - sr)
                d["state_max_abs_diff"] = float(dd.max()) if dd.size else 0.0
                d["state_steps_differing"] = int((dd.reshape(n, -1) > 0).any(1).sum())
        except (KeyError, TypeError, ValueError):
            pass
        out.append(d)
    return out


def check_trace(new_path, ref_path):
    c = {"new_file": str(new_path), "ref_file": str(ref_path), "size_new": os.path.getsize(new_path), "size_ref": os.path.getsize(ref_path)}
    c["sha256_new"], c["sha256_ref"] = sha256(new_path), sha256(ref_path)
    c["byte_identical"] = c["size_new"] == c["size_ref"] and c["sha256_new"] == c["sha256_ref"]
    c["equal_except_wall"] = c["byte_identical"]
    if not c["byte_identical"]:
        new, ref = json.loads(Path(new_path).read_text()), json.loads(Path(ref_path).read_text())
        c["parsed_equal"] = new == ref
        # result.wall is the episode's wall-clock seconds (runs/ride.py), so two runs of the same replay never match byte for
        # byte (the pilot R0 trace and the 38178-era r0_s201_mu_noroad_trace.json differ only there); it is set aside here
        walls = [d.get("result", {}).pop("wall", None) if isinstance(d.get("result"), dict) else None for d in (new, ref)]
        c["wall_new"], c["wall_ref"] = walls
        c["equal_except_wall"] = new == ref
        c["differences"] = trace_differences(new, ref)
        del new, ref
    c["ok"] = bool(c["equal_except_wall"])
    return c


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--new-counts", default=str(PILOT / "trackc10_r0_counts.npz"))
    ap.add_argument("--ref-counts", default=str(PILOT / "trackc_r0_counts.npz"))
    ap.add_argument("--new-trace", default=str(PILOT / "trackc10_r0_trace.json"))
    ap.add_argument("--ref-trace", default=str(PILOT / "trackc_r0_trace.json"))
    ap.add_argument("--out", default=None, help=f"default {OUT} under the repo root")
    a = ap.parse_args()
    out = Path(a.out) if a.out else HERE.parent / OUT
    checks = {}
    for name, fn, new, ref in (("counts", check_counts, a.new_counts, a.ref_counts), ("trace", check_trace, a.new_trace, a.ref_trace)):
        missing = [p for p in (new, ref) if not Path(p).exists()]
        if missing:  # no verdict: verify.json is not written, so the relay runs tc-verify again (up to its tries)
            raise SystemExit(f"cannot verify {name}: missing {', '.join(missing)}; nothing written")
        checks[name] = fn(new, ref)  # a crash (unreadable file, memory) likewise writes nothing
    ok = all(c["ok"] for c in checks.values())
    result = {"ok": ok, "what": "pilot R0 replay (38178) re-run at 10 ms bins: 10-bin sums vs the 100 ms counts, trace equal except its wall-clock time",
              "checks": checks, "date": datetime.datetime.now().astimezone().isoformat(timespec="seconds")}
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".tmp")
    tmp.write_text(json.dumps(result, indent=1))
    tmp.replace(out)
    for name, c in checks.items():
        print(f"{name}: {'ok' if c['ok'] else 'FAILED'}", {k: v for k, v in c.items() if k not in ("differences",)})
        for d in c.get("differences", []):
            print("  differs:", d)
    print(f"verify {'OK' if ok else 'FAILED'} -> {out}", flush=True)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()

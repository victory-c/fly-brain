#!/usr/bin/env python3
"""Tests for the Track C relay links (submit_serial.track_c_links) and tools/track_c_verify.py, on fake result trees in a temp
directory; nothing is submitted. Run: python3 tools/test_track_c_relay.py (or pytest)."""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import submit_serial as ss  # noqa: E402
import track_c_all as tc  # noqa: E402


@contextlib.contextmanager
def tree(verify=None, screens=(), replays=(), outputs=()):
    """A temp results tree: verify.json (None: none), the given screen stems, brains' replay files and (short, mode) outputs."""
    old = os.getcwd()
    with tempfile.TemporaryDirectory() as d:
        os.chdir(d)
        try:
            def touch(p):
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("x")
            touch(tc.PROBE_ROWS)
            if verify is not None:
                tc.VERIFY.write_text(json.dumps({"ok": verify}))
            for s in screens:
                touch(tc.screen(s))
            for tag in replays:
                for f in tc.replay_files(tag).values():
                    touch(f)
            for short, mode in outputs:
                touch(tc.output(short, mode))
            yield
        finally:
            os.chdir(old)


def names(queued=()):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        links = ss.track_c_links(set(queued))
    for _, args, env in links:
        assert env == {}, "Track C links carry no GENS export"
    return [n for n, _, _ in links], links, buf.getvalue()


ALL_SCREENS = [s for _, _, s in tc.BRAINS]
ALL_TAGS = [t for _, t, _ in tc.BRAINS]
OLD_SCREENS = [s for s in ALL_SCREENS if s not in ("r35_s1", "r5_s1_w2")]


def test_fresh():
    with tree(screens=OLD_SCREENS):
        n, links, _ = names()
    assert n == ["tc-verify", "scr-r35", "scr-r5"]
    assert links[0][1] == ["trackc.sbatch", "--pilot-r0"]
    assert links[1][1][-2:] == ["screen-rungs.sbatch", "r35_s1"] and "--gres=none" in links[1][1]
    assert links[2][1][-3:] == ["screen-rungs.sbatch", "r5_s1", "2"]


def test_verified_runs_replays_in_order():
    with tree(verify=True, screens=OLD_SCREENS):
        n, links, _ = names()
    assert n == ["scr-r35", "scr-r5"] + [f"tc-{s}" for s, _, _ in tc.BRAINS]
    assert links[2][1] == ["trackc.sbatch", "--rows", str(tc.PROBE_ROWS), "fly_brain/results/rungs/conf_r0/v4.5_s211/cem.json"]


def test_analyses_after_everything():
    with tree(verify=True, screens=ALL_SCREENS, replays=ALL_TAGS[:-1]):
        assert names()[0] == ["tc-r5_s1_w2_cpu"]
    with tree(verify=True, screens=ALL_SCREENS[:-1], replays=ALL_TAGS):
        assert names()[0] == ["scr-r5"]  # a screen missing: no analysis yet
    with tree(verify=True, screens=ALL_SCREENS, replays=ALL_TAGS):
        n, links, _ = names()
        assert n == ["tc-n90", "tc-calcium", "tc-probe"]
        assert links[0][1] == ["--time=03:00:00", "trackc-analysis.sbatch", "n90"]
        assert names(queued=["tc-n90"])[0] == ["tc-calcium"]  # probe waits for n90's outputs
    with tree(verify=True, screens=ALL_SCREENS, replays=ALL_TAGS, outputs=[(s, "n90") for s, _, _ in tc.BRAINS]):
        assert names()[0] == ["tc-calcium", "tc-probe"]
    done = [(s, m) for s, _, _ in tc.BRAINS for m in tc.MODES]
    with tree(verify=True, screens=ALL_SCREENS, replays=ALL_TAGS, outputs=done):
        assert names()[0] == []


def test_failed_verify_stops_track_c():
    with tree(verify=False, screens=OLD_SCREENS):
        n, _, out = names()
    assert n == [] and "TRACK C STOPPED" in out


def test_queued_links_are_skipped():
    with tree(screens=OLD_SCREENS):
        assert names(queued=["tc-verify"])[0] == ["scr-r35", "scr-r5"]


def test_prefixes():
    for p in ("tc-", "scr-"):
        assert p in ss.PREFIXES


def _npz(path, counts, bin_ms, rows=None, site=None):
    n = counts.shape[2]
    np.savez_compressed(path, counts=counts, rows=np.arange(n) if rows is None else rows,
                        site=np.array(["descending"] * n) if site is None else site, bin_ms=bin_ms)


def _verify(d, new10, ref100, new_trace=b'{"a": 1}', ref_trace=b'{"a": 1}', **kw):
    d = Path(d)
    _npz(d / "new.npz", new10, 10.0, **kw)
    _npz(d / "ref.npz", ref100, 100.0)
    (d / "new.json").write_bytes(new_trace)
    (d / "ref.json").write_bytes(ref_trace)
    r = subprocess.run([sys.executable, str(HERE / "track_c_verify.py"), "--new-counts", str(d / "new.npz"), "--ref-counts", str(d / "ref.npz"),
                        "--new-trace", str(d / "new.json"), "--ref-trace", str(d / "ref.json"), "--out", str(d / "verify.json")],
                       capture_output=True, text=True)
    return r.returncode, json.loads((d / "verify.json").read_text())


def test_verify():
    rng = np.random.default_rng(0)
    new = rng.integers(0, 4, size=(1505, 3, 5)).astype(np.int16)  # 150 blocks and a 5-bin tail that is dropped
    ref = new[:1500].reshape(150, 10, 3, 5).sum(1).astype(np.int16)
    with tempfile.TemporaryDirectory() as d:
        rc, v = _verify(d, new, ref)
        assert rc == 0 and v["ok"] and v["checks"]["counts"]["dropped_tail_bins"] == 5 and v["checks"]["trace"]["byte_identical"]
        bad = ref.copy(); bad[7, 1, 2] += 1
        rc, v = _verify(d, new, bad)
        assert rc == 1 and not v["ok"] and v["checks"]["counts"]["first_difference"] == {"bin": 7, "rider": 1, "neuron_col": 2,
                                                                                         "new": int(ref[7, 1, 2]), "ref": int(bad[7, 1, 2])}
        rc, v = _verify(d, new, ref, rows=np.arange(5) + 1)
        assert rc == 1 and not v["checks"]["counts"]["rows_equal"]
        t1 = json.dumps({"mode": "m", "trace": [{"t": 0.0, "state": [[0.0, 1.0]]}, {"t": 0.01, "state": [[0.0, 2.0]]}]}).encode()
        t2 = json.dumps({"mode": "m", "trace": [{"t": 0.0, "state": [[0.0, 1.0]]}, {"t": 0.01, "state": [[0.0, 2.5]]}]}).encode()
        rc, v = _verify(d, new, ref, t1, t2)
        tr = v["checks"]["trace"]
        assert rc == 1 and not tr["byte_identical"] and tr["differences"][0]["first_differing_step"] == 1
        assert tr["differences"][0]["fields"] == ["state"] and tr["differences"][0]["state_max_abs_diff"] == 0.5
        # only result.wall (wall-clock seconds) differs: not byte identical, but the same replay
        t1 = json.dumps({"mode": "m", "trace": [{"t": 0.0}], "result": {"fitness": [1.0], "wall": 945.88}}).encode()
        t2 = json.dumps({"mode": "m", "trace": [{"t": 0.0}], "result": {"fitness": [1.0], "wall": 855.63}}).encode()
        rc, v = _verify(d, new, ref, t1, t2)
        tr = v["checks"]["trace"]
        assert rc == 0 and v["ok"] and not tr["byte_identical"] and tr["equal_except_wall"] and tr["wall_new"] == 945.88
        t3 = json.dumps({"mode": "m", "trace": [{"t": 0.0}], "result": {"fitness": [1.5], "wall": 855.63}}).encode()
        rc, v = _verify(d, new, ref, t1, t3)
        assert rc == 1 and not v["checks"]["trace"]["equal_except_wall"]


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f()
            print("ok", k)

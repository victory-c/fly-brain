#!/usr/bin/env python3
"""Unit tests for track_c_calcium.py on tiny synthetic spikes. Run: python tools/test_track_c_calcium.py (or pytest)."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import track_c_calcium as tcc  # noqa: E402


def one_spike(n_bins=300, at=50):
    c = np.zeros((n_bins, 1, 1), dtype=np.int16)
    c[at, 0, 0] = 1
    return c


def test_single_spike_peak_is_1ap_dff():
    for v, p in tcc.PARAMS.items():
        for sat in (True, False):
            (tr,) = tcc.dff_frames(one_spike(), 10.0, (1.0,), v, sat)
            assert abs(tr.max() - p["d1"]) < 1e-5, (v, sat, tr.max())
            assert tr[:505].max() == 0.0  # nothing before the spike at the centre of bin 50 (505 ms)


def test_hill_k_arithmetic():
    assert abs(tcc.hill_k(4.174, 0.75, 1.92) - 2.205) < 1e-3
    for v, p in tcc.PARAMS.items():
        K = tcc.hill_k(p["hill"]["dmax"], p["d1"], p["hill_n"])
        assert abs(p["hill"]["dmax"] / (1 + K ** p["hill_n"]) - p["d1"]) < 1e-12


def test_decay_time_constant_recovered():
    for v, p in tcc.PARAMS.items():
        for sat in (False, True):
            (tr,) = tcc.dff_frames(one_spike(n_bins=600, at=20), 10.0, (1.0,), v, sat)
            g = tr[:, 0, 0].astype(np.float64)
            tau_r, tau_d, _ = tcc.model(v, sat)
            t0 = 205 + int(10 * tau_r)  # well after the rise
            t = np.arange(t0, t0 + int(tau_d))
            if sat:  # invert the Hill curve back to calcium
                n, dmax = p["hill_n"], p["hill"]["dmax"]
                x = tcc.hill_k(dmax, p["d1"], n) * (g / (dmax - g)) ** (1 / n)
            else:
                x = g
            slope = np.polyfit(t, np.log(x[t]), 1)[0]
            assert abs(-1 / slope / tau_d - 1) < 0.01, (v, sat, -1 / slope, tau_d)
            pk = int(g.argmax())
            half = pk + int(np.argmax(g[pk:] <= g[pk] / 2)) - pk
            assert abs(half - p["decay_ms"]) <= 2.0, (v, sat, half, p["decay_ms"])  # published 1AP half-decay, 1 ms grid


def test_noise_scales_inverse_sqrt_n0():
    F = np.zeros((2000, 4, 25), dtype=np.float32)
    sds = {}
    for n0 in (30, 100, 300):
        rng = np.random.default_rng(1)
        N = tcc.add_noise(F, n0, tcc.T30, rng)
        assert abs(N.mean()) < 0.01
        sds[n0] = N.std()
        assert abs(sds[n0] * np.sqrt(n0) - 1) < 0.03, (n0, sds[n0])
    assert abs(sds[30] / sds[300] - np.sqrt(10)) < 0.1
    N10 = tcc.add_noise(F, 100, tcc.T10, np.random.default_rng(2))  # 10 Hz own acquisition: 3x photons
    assert abs(N10.std() * np.sqrt(300) - 1) < 0.03
    avg = tcc.average_frames(tcc.add_noise(F, 100, tcc.T30, np.random.default_rng(3)))
    assert abs(avg.std() / N10.std() - 1) < 0.05  # same under Poisson noise
    assert tcc.add_noise(F, None, tcc.T30, None) is F


def test_30hz_frame_assignment():
    fr = tcc.bin_frames(30, 10.0, tcc.T30)
    assert np.bincount(fr).tolist() == [3, 4, 3] * 3
    assert tcc.bin_frames(30, 10.0, tcc.T10).tolist() == [0] * 10 + [1] * 10 + [2] * 10
    c = np.arange(30, dtype=np.int16).reshape(30, 1, 1)
    s = tcc.spike_frames(c, 10.0, tcc.T30)[:, 0, 0]
    assert s[:3].tolist() == [0 + 1 + 2, 3 + 4 + 5 + 6, 7 + 8 + 9] and len(s) == 9
    # 1 ms dF/F samples split 34, 33, 33 per 100 ms; a constant input gives a constant frame mean
    F30, F10 = tcc.dff_frames(np.ones((300, 1, 1), dtype=np.int16), 10.0, (tcc.T30, tcc.T10), "8m", False)
    assert F30.shape[0] == 90 and F10.shape[0] == 30
    assert np.isfinite(F30).all() and (F30[1:] > 0).all()


def test_frame_targets_and_masking():
    n_s, riders = 30, 3
    phi = np.tile(np.arange(n_s, dtype=float)[:, None], (1, riders))
    done = np.zeros((n_s, riders), dtype=bool)
    done[7:, 1] = True  # rider 1 falls in step 7, [70, 80) ms: frame 2 only (frame 1 ends at 66.7 ms)
    done[3:, 2] = True  # rider 2 falls in step 3, [30, 40) ms: overlaps frames 0 and 1 though its centre is in frame 1
    y, ok = tcc.frame_targets(phi, done, 10.0, tcc.T30, 9)
    assert y[:3, 0].tolist() == [1.0, 4.5, 8.0]  # means of steps 0-2, 3-6, 7-9
    assert ok[:, 0].all()
    assert ok[:2, 1].all() and not ok[2:, 1].any()
    assert not ok[:, 2].any()
    y10, ok10 = tcc.frame_targets(phi, done, 10.0, tcc.T10, 3)
    assert y10[:, 0].tolist() == [4.5, 14.5, 24.5] and not ok10[:, 1].any()


def test_burn_in_dropped():
    F = np.random.default_rng(0).normal(size=(60, 2, 3)).astype(np.float32)
    y = np.tile(np.arange(60.0)[:, None], (1, 2)); ok = np.ones((60, 2), dtype=bool)
    X, Y, R = tcc.stack(F, y, ok, tcc.T30)
    assert Y.min() == 30 and len(Y) == 60 and X.shape == (60, 3)  # frames 30..59, 2 riders
    XL, YL, RL = tcc.stack_lagged(F, y, ok, tcc.T30, 4)
    assert XL.shape == (2 * 27, 3, 4) and YL.max() == 56
    v = tcc.LagView(XL)
    assert v[:, [0, 2]].shape == (54, 8) and v.shape == (54, 3)


def test_end_to_end_tiny():
    rng = np.random.default_rng(5)
    n_bins, riders, neurons = 300, 10, 6  # 3 s, 10 ms bins
    t = np.arange(n_bins) * 0.01
    phi = np.sin(2 * np.pi * 0.7 * t[:, None] + rng.uniform(0, 6, riders))
    gain = np.array([1.0, -1.0, 0.5, 0.0, 0.0, 0.8])
    rate = np.clip(8 + 7 * phi[:, :, None] * gain, 0, None)  # Hz; low enough that 8m is not saturated
    counts = rng.poisson(rate * 0.01).astype(np.int16)
    done = np.zeros((n_bins, riders), dtype=bool); done[250:, 3] = True
    site = np.array(["descending"] * 4 + ["wing_motor"] * 2)
    screen_r = np.array([0.9, -0.8, 0.4, 0.0, 0.1, 0.6])
    F30, F10 = tcc.dff_frames(counts, 10.0, (tcc.T30, tcc.T10), "8m", True)
    for F, fm in ((F30, tcc.T30), (F10, tcc.T10)):
        y, ok = tcc.frame_targets(phi, done, 10.0, fm, F.shape[0])
        r = tcc.score_row(tcc.add_noise(F, 100, fm, np.random.default_rng(0)), y, ok, fm, site, screen_r, 2)
        d = r["sites"]["descending"]
        assert d["neurons"] == 4 and d["r2_all"] > 0.05, d  # weak: 4 sparse neurons, same frame only
        assert set(r["sites"]["wing_motor"]["references"]) == {"site", "descending"}
    y, ok = tcc.frame_targets(phi, done, 10.0, tcc.T30, F30.shape[0])
    rl = tcc.score_row(F30, y, ok, tcc.T30, site, screen_r, 0, lags=4)
    assert rl["sites"]["descending"]["neurons"] == 4
    assert rl["sites"]["descending"]["r2_all"] > tcc.score_row(F30, y, ok, tcc.T30, site, screen_r, 0)["sites"]["descending"]["r2_all"]
    r30 = tcc.score_row(F30, y, ok, tcc.T30, site, screen_r, 0)
    rs = tcc.score_row(tcc.spike_frames(counts, 10.0, tcc.T30), y, ok, tcc.T30, site, screen_r, 0)
    # 60 frames after the 1 s burn-in x 10 riders, minus rider 3's frames 75-89 (done from 2500 ms = frame 75's start)
    assert rs["samples"] == r30["samples"] == 585, (rs["samples"], r30["samples"])
    assert rl["samples"] == 57 * 10 - 15  # lagged: frames 30..86 need k..k+3 unmasked, so rider 3 loses k = 72..86


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)

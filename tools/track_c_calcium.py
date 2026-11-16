#!/usr/bin/env python3
"""Track C from simulated jGCaMP8 dF/F at 30 and 10 Hz (preregistration section 7, plan section 3).

Input is one replay recorded with --brain-bin-ms 10 (`runs/ride.py --replay ... --brain-bin-ms 10 --counts-out COUNTS.npz
--trace TRACE.json`, best with --offroad 0) and that brain's passenger screen. From fly_brain/:

    PYTHONPATH=. python ../tools/track_c_calcium.py COUNTS.npz TRACE.json results/rungs/screens/r0.parquet OUT.json

Model, per rider and neuron:
- each 10 ms bin's spikes are placed at the bin centre on a 1 ms grid;
- a calcium-like trace x(t) = sum over spikes of a double-exponential kernel, scaled so one spike peaks at x = 1, run as two
  first-order recursive (IIR) filters;
- dF/F = Dmax x^n / (x^n + K^n), with n the purified-protein Hill coefficient and K set so one spike gives the published
  1-AP dF/F (a `linear` row uses dF/F = dF/F_1AP * x with its own kernel fit, as a contrast);
- frames: the mean dF/F over each frame (full-frame integration), 30 Hz (33.3 ms) or 10 Hz (100 ms, its own acquisition);
- noise: photons ~ Poisson(N0 (T / 33.3 ms) (1 + dF/F)), dF/F read back as photons / (N0 T / 33.3 ms) - 1, so 10 Hz
  collects 3x the photons; the 30 Hz movie averaged in threes is reported too;
- a rider's frame is dropped if `done` is set in any control step overlapping it; the first 1 s of every rider is dropped.
Roll-rate targets: the mean phi_dot over the 10 ms control steps whose centres fall in the frame (3, 4, 3 steps at 30 Hz).
Decoding reuses cv_r2, pick_lambda and n90 from track_c.py with the same folds, screen order and references; a matched
spike-count baseline is scored on the same frames. Every published number and assumption is in PARAMS below.
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import track_c  # noqa: E402  (cv_r2, pick_lambda, n90)

T30 = 100.0 / 3  # ms, one 30 Hz frame; N0 is photons per neuron per T30
T10 = 100.0
BURN_MS = 1000.0  # about 2-3 decay constants of the 8m calcium kernel; the counts already start after the 300 ms warm-up
N0_PRIMARY, N0_GRID = 100, (30, 100, 300)  # ASSUMPTION: photons per neuron per 33.3 ms frame; not a published value
PRIMARY = "8m"

# Published values: Zhang et al. 2023, Nature 615:884-891, doi:10.1038/s41586-023-05828-9 (open access, PMC10060165),
# Extended Data Table 3, "Characterization of jGCaMP8 in purified protein and in dissociated neuronal culture", read from
# the table image itself (not Janelia's web copy, whose culture numbers differ: e.g. 8m 0.76 / 118.3 ms there).
#   d1, d10, d160: "1AP / 10AP / 160AP dF/F0", dissociated rat hippocampal culture, field stimulation, 200 Hz imaging,
#                  room temperature; 160 pulses at 83 Hz (Extended Data Fig. 3 title: "3, 10, and 160 field stimulation
#                  pulses (45 V, 83 Hz)"). dF/F0 = (Fpeak - F0)/F0, Fpeak the single highest post-stimulus frame (Methods).
#   rise_ms:       "1AP half-rise time", ms (Methods: time at which F crosses Fpeak/2, interpolated between frames).
#   decay_ms:      "1AP half-decay time", ms. Taken here as peak to half-peak (the paper does not state the start point).
#   hill_n:        "Hill coefficient", purified protein (8f 2.08 +- 0.22, 8m 1.92 +- 0.12, 8s 2.20 +- 0.13).
#   (purified Kd: 8f 334, 8m 108, 8s 46 nM; (Fsat-Fapo)/Fapo 78.8, 45.7, 49.5 - recorded, not used: the in-cell ceiling is
#    the 160AP response, an order of magnitude lower.)
# Fitted (FIT, by fit_variant() below, numpy Nelder-Mead on a 0.1 ms grid; loss = sum of squared log ratios):
#   hill:   tau_r, tau_d (ms) of the calcium kernel and Dmax so that the single-spike FLUORESCENCE (after the Hill curve)
#           has the published half-rise and half-decay, and 10 and 160 spikes at 83 Hz give the published peaks. Because
#           dF/F ~ x^n for small x, the calcium tau_d is about n times the fluorescence half-decay / ln 2 would suggest.
#   linear: tau_r, tau_d fitted to half-rise and half-decay only (no saturation).
# Dmax is therefore FIT to the culture 10AP/160AP responses (not the placeholder 15); K follows from the 1-AP peak:
#   one spike peaks at x = 1, so d1 = Dmax / (1 + K^n)  =>  K = (Dmax / d1 - 1)^(1/n).
#   8m: K = (4.174 / 0.75 - 1)^(1/1.92) = 4.565^0.5208 = 2.205 (spike-peak units).
#   8f: K = (3.190 / 0.37 - 1)^(1/2.08) = 7.622^0.4808 = 2.655.   8s: K = (4.001 / 1.10 - 1)^(1/2.20) = 2.637^0.4545 = 1.554.
# ASSUMPTIONS beyond the paper: zero resting calcium in the Hill curve (dF/F = 0 at no spikes); culture kinetics at room
# temperature stand in for fly neurons in vivo (the paper's fly L2 assay gives 8m half-rise 58 ms, half-decay 137 ms at a
# 0.5 Hz visual stimulus, Fig. 2 legend, which is not a single-AP measure); field stimulation assumed 1 AP per pulse at 83 Hz.
# Fit residuals (got vs published): 8m 10AP 3.90 vs 3.64, 160AP 4.14 vs 4.42; 8s 3.93 vs 3.88, 4.00 vs 4.05;
#   8f 2.92 vs 2.45, 3.15 vs 3.70 (8f fits worst); half-rise and half-decay within 0.1 ms for all three.
PARAMS = {
    "8f": {"d1": 0.37, "d10": 2.45, "d160": 3.70, "rise_ms": 6.6, "decay_ms": 87.5, "hill_n": 2.08,
           "hill": {"tau_r": 6.43, "tau_d": 222.2, "dmax": 3.190},
           "linear": {"tau_r": 13.57, "tau_d": 105.3}},
    "8m": {"d1": 0.75, "d10": 3.64, "d160": 4.42, "rise_ms": 7.4, "decay_ms": 134.0, "hill_n": 1.92,
           "hill": {"tau_r": 7.80, "tau_d": 303.3, "dmax": 4.174},
           "linear": {"tau_r": 13.86, "tau_d": 172.4}},
    "8s": {"d1": 1.10, "d10": 3.88, "d160": 4.05, "rise_ms": 10.2, "decay_ms": 330.7, "hill_n": 2.20,
           "hill": {"tau_r": 9.79, "tau_d": 814.2, "dmax": 4.001},
           "linear": {"tau_r": 17.27, "tau_d": 451.7}},
}
SOURCE = "Zhang et al. 2023 Nature 615:884, Extended Data Table 3 (PMC10060165); kernels and Dmax fitted here"


def hill_k(dmax, d1, n):
    """K such that one spike (x = 1) gives d1."""
    return (dmax / d1 - 1.0) ** (1.0 / n)


def model(variant, saturate=True):
    """(tau_r, tau_d, f) for a variant: f maps the calcium trace x (spike-peak units) to dF/F."""
    p = PARAMS[variant]
    if not saturate:
        d1 = p["d1"]
        return p["linear"]["tau_r"], p["linear"]["tau_d"], lambda x: d1 * x
    h, n = p["hill"], p["hill_n"]
    dmax, K = h["dmax"], hill_k(h["dmax"], p["d1"], n)
    Kn = K ** n
    def f(x):
        xn = np.power(np.maximum(x, 0.0), n)
        return dmax * xn / (xn + Kn)
    return h["tau_r"], h["tau_d"], f


def kernel_gains(tau_r, tau_d, dt=1.0):
    """Per-step decay of the two IIR filters and the scale that makes a single spike peak at exactly 1 on the grid."""
    ar, ad = np.exp(-dt / tau_r), np.exp(-dt / tau_d)
    m = np.arange(1, int(20 * tau_d / dt) + 2)
    return ar, ad, 1.0 / (ad ** m - ar ** m).max()


def dff_frames(counts, bin_ms, frames_ms, variant=PRIMARY, saturate=True, dt=1.0):
    """Noise-free mean dF/F per frame: list (one per frame length) of (frames, riders, neurons) float32.

    counts is (bins, riders, neurons); spikes go to the bin centre on a dt grid. Only complete frames are returned.
    """
    tau_r, tau_d, f = model(variant, saturate)
    ar, ad, c = kernel_gains(tau_r, tau_d, dt)
    nb = counts.shape[0]
    n_t = int(round(nb * bin_ms / dt))
    t = np.arange(n_t) * dt
    spike_at = np.full(n_t, -1)
    spike_at[np.round((np.arange(nb) + 0.5) * bin_ms / dt).astype(int)] = np.arange(nb)
    shape = counts.shape[1:]
    xr, xd = np.zeros(shape), np.zeros(shape)
    accs, idx = [], []
    for fm in frames_ms:
        n_f = int(np.floor(nb * bin_ms / fm + 1e-9))
        accs.append(np.zeros((n_f,) + shape)); idx.append(np.floor(t / fm + 1e-9).astype(int))
    for i in range(n_t):
        xr *= ar; xd *= ad
        b = spike_at[i]
        if b >= 0:
            s = counts[b]
            xr += s; xd += s
        y = f(c * (xd - xr))
        for acc, ix in zip(accs, idx):
            if ix[i] < len(acc):
                acc[ix[i]] += y
    out = []
    for acc, ix, fm in zip(accs, idx, frames_ms):
        n = np.bincount(ix, minlength=len(acc))[:len(acc)]
        out.append((acc / n[:, None, None]).astype(np.float32))
    return out


def add_noise(F, n0, frame_ms, rng):
    """Poisson photon noise: N0 photons per neuron per 33.3 ms at baseline, scaled by the frame length."""
    if n0 is None:
        return F
    lam = n0 * frame_ms / T30
    return (rng.poisson(lam * np.maximum(1.0 + F, 0.0)) / lam - 1.0).astype(np.float32)


def average_frames(F, k=3):
    """Average consecutive groups of k frames (the 30 Hz movie read at 10 Hz); an incomplete tail is dropped."""
    n = F.shape[0] // k
    return F[:n * k].reshape(n, k, *F.shape[1:]).mean(1)


def bin_frames(n_bins, bin_ms, frame_ms):
    """Frame of each bin (or 10 ms control step), by its centre."""
    return np.floor((np.arange(n_bins) + 0.5) * bin_ms / frame_ms + 1e-9).astype(int)


def spike_frames(counts, bin_ms, frame_ms):
    """Spike counts summed into frames by bin centre (the matched spike baseline): (frames, riders, neurons)."""
    fr = bin_frames(counts.shape[0], bin_ms, frame_ms)
    n_f = int(np.floor(counts.shape[0] * bin_ms / frame_ms + 1e-9))
    out = np.zeros((n_f,) + counts.shape[1:], dtype=np.float32)
    keep = fr < n_f
    np.add.at(out, fr[keep], counts[keep].astype(np.float32))
    return out


def frame_targets(phi_dot, done, ctrl_ms, frame_ms, n_frames):
    """Per-frame roll-rate target and validity, both (frames, riders).

    Target: mean phi_dot over the steps whose centres fall in the frame. Invalid: `done` in any step overlapping the frame,
    or the frame has no step centre.
    """
    n_s = phi_dot.shape[0]
    fr = bin_frames(n_s, ctrl_ms, frame_ms)
    y = np.zeros((n_frames, phi_dot.shape[1])); ok = np.zeros((n_frames, phi_dot.shape[1]), dtype=bool)
    lo = np.arange(n_s) * ctrl_ms
    for k in range(n_frames):
        sel = fr == k
        over = (lo < (k + 1) * frame_ms - 1e-9) & (lo + ctrl_ms > k * frame_ms + 1e-9)
        if not sel.any():
            continue
        y[k] = phi_dot[sel].mean(0)
        ok[k] = ~done[over].any(0)
    return y, ok


def stack(F, y, ok, frame_ms, burn_ms=BURN_MS):
    """(samples, neurons) features, targets and riders from unmasked frames starting at or after burn_ms."""
    n = min(F.shape[0], y.shape[0])
    first = int(np.ceil(burn_ms / frame_ms - 1e-9))
    X, Y, R = [], [], []
    for k in range(first, n):
        m = ok[k]
        X.append(F[k, m]); Y.append(y[k, m]); R.append(np.flatnonzero(m))
    if not X:
        return np.zeros((0, F.shape[2])), np.zeros(0), np.zeros(0, dtype=int)
    return np.concatenate(X).astype(np.float64), np.concatenate(Y).astype(np.float64), np.concatenate(R)


class LagView:
    """Frames k..k+L-1 of each neuron as features; indexing [:, cols] selects whole neurons, so n90 still counts neurons."""

    def __init__(self, A):  # A: (samples, neurons, lags)
        self.A = A
        self.shape = A.shape[:2]

    def __getitem__(self, key):
        rows, cols = key
        a = self.A[rows][:, cols]
        return a.reshape(a.shape[0], -1)


def stack_lagged(F, y, ok, frame_ms, lags, burn_ms=BURN_MS):
    """Like stack, with frames k..k+lags-1 per neuron; a sample needs all of them unmasked. Returns (samples, neurons, lags)."""
    n = min(F.shape[0], y.shape[0]) - lags + 1
    first = int(np.ceil(burn_ms / frame_ms - 1e-9))
    X, Y, R = [], [], []
    for k in range(first, n):
        m = ok[k:k + lags].all(0)
        X.append(np.stack([F[k + j, m] for j in range(lags)], -1)); Y.append(y[k, m]); R.append(np.flatnonzero(m))
    return np.concatenate(X).astype(np.float64), np.concatenate(Y).astype(np.float64), np.concatenate(R)


def score_site(X, y, rider, folds, order, refs, n_random=20):
    """Full R^2, lambda and N90 (screen order, and n_random random orders) against each reference R^2 (None = own)."""
    lagged = isinstance(X, LagView)
    flat = X[:, np.arange(X.shape[1])] if lagged else X
    active = (X.A.std(0) > 0).any(-1) if lagged else X.std(0) > 0  # silent (constant) neurons stay in N, not in the lambda fit
    lam = track_c.pick_lambda(X[:, np.flatnonzero(active)], y, rider, folds)
    full = track_c.cv_r2(flat, y, rider, folds, lam)
    res = {"neurons": int(X.shape[1]), "active": int(active.sum()), "lambda": lam, "r2_all": round(full, 4), "references": {}}
    for name, value in refs.items():
        target = 0.9 * (full if value is None else value)
        n_screen, curve = track_c.n90(X, y, rider, folds, lam, order, target)
        r = {"target_r2": round(target, 4), "n90_screen": n_screen, "r2_screen_curve": curve}
        if n_random:
            v = [track_c.n90(X, y, rider, folds, lam, np.random.default_rng(100 + i).permutation(X.shape[1]), target)[0]
                 for i in range(n_random)]
            ok = [x for x in v if x is not None]
            r["n90_random_all_site_neurons"] = {"reached": len(ok), "median": float(np.median(ok)) if ok else None,
                                                "q25_q75": [float(x) for x in np.percentile(ok, [25, 75])] if ok else None}
        res["references"][name] = r
    return res, full


def score_row(F, y, ok, frame_ms, site, screen_r, n_random, lags=1):
    """Both sites for one feature movie: the descending site first, its R^2 is the wing-motor second reference."""
    if lags > 1:
        A, Y, R = stack_lagged(F, y, ok, frame_ms, lags)
    else:
        A, Y, R = stack(F, y, ok, frame_ms)
    riders = np.unique(R)
    folds = np.array_split(np.random.default_rng(0).permutation(riders), 5)
    out = {"samples": int(len(Y)), "riders": int(len(riders)), "roll_rate_sd": float(Y.std()), "sites": {}}
    desc = None
    for name in ("descending", "wing_motor"):
        m = site == name
        X = LagView(A[:, m]) if lags > 1 else A[:, m]
        order = np.argsort(-np.abs(np.nan_to_num(screen_r[m])), kind="stable")
        refs = {"site": None} if name == "descending" else {"site": None, "descending": desc}
        res, full = score_site(X, Y, R, folds, order, refs, n_random)
        if name == "descending":
            desc = full
        out["sites"][name] = res
    return out


def fit_variant(variant, saturate=True, iters=150):
    """Refit the kernel (and Dmax) to the published culture numbers; returns the fitted dict and the achieved values."""
    p = PARAMS[variant]
    d1, n = p["d1"], p["hill_n"]
    tgt = np.array([p["rise_ms"], p["decay_ms"], p["d10"], p["d160"]])
    def vals(tr, td, dmax):
        f = (lambda x: d1 * x) if not saturate else \
            (lambda x: dmax * x ** n / (x ** n + hill_k(dmax, d1, n) ** n))
        return np.array(culture_metrics(tr, td, f))
    def loss(q):
        tr, td = np.exp(q[0]), np.exp(q[1])
        if tr >= td:
            return 1e9
        v = vals(tr, td, d1 + np.exp(q[2]) if saturate else None)
        k = 4 if saturate else 2
        return float((np.log(v[:k] / tgt[:k]) ** 2).sum())
    x0 = [np.log(5.0), np.log(1.5 * p["decay_ms"])] + ([np.log(p["d160"])] if saturate else [])
    q = _nelder_mead(loss, x0, 0.3, iters)
    tr, td = float(np.exp(q[0])), float(np.exp(q[1]))
    if not saturate:
        return {"tau_r": tr, "tau_d": td}, vals(tr, td, None)
    dmax = float(d1 + np.exp(q[2]))
    return {"tau_r": tr, "tau_d": td, "dmax": dmax}, vals(tr, td, dmax)


def culture_metrics(tau_r, tau_d, f, dt=0.1, hz=83.0):
    """Single-spike fluorescence half-rise (from the spike) and half-decay (from the peak), and peak dF/F for 10 and 160
    spikes at hz, in continuous time on a fine grid."""
    t = np.arange(0, 8 * tau_d + 50, dt)
    k = np.exp(-t / tau_d) - np.exp(-t / tau_r)
    norm = k.max()
    g = f(k / norm)
    p = int(g.argmax()); half = g[p] / 2
    out = [t[np.argmax(g >= half)], t[p + np.argmax(g[p:] <= half)] - t[p]]
    for n_ap in (10, 160):
        tt = np.arange(0, 1000 * n_ap / hz + 50, dt)
        kk = (np.exp(-tt / tau_d) - np.exp(-tt / tau_r)) / norm
        x = np.zeros_like(tt)
        for j in range(n_ap):
            s = int(round(j * 1000 / hz / dt))
            x[s:] += kk[:len(tt) - s]
        out.append(float(f(x).max()))
    return out


def _nelder_mead(fun, x0, step, iters):
    n = len(x0)
    S = [np.array(x0, float)] + [np.array(x0, float) + step * np.eye(n)[i] for i in range(n)]
    F = [fun(s) for s in S]
    for _ in range(iters):
        o = np.argsort(F); S = [S[i] for i in o]; F = [F[i] for i in o]
        c = np.mean(S[:-1], 0); r = 2 * c - S[-1]; fr = fun(r)
        if fr < F[0]:
            e = 3 * c - 2 * S[-1]; fe = fun(e)
            S[-1], F[-1] = (e, fe) if fe < fr else (r, fr)
        elif fr < F[-2]:
            S[-1], F[-1] = r, fr
        else:
            k = (c + S[-1]) / 2; fk = fun(k)
            if fk < F[-1]:
                S[-1], F[-1] = k, fk
            else:
                S = [S[0]] + [(S[0] + s) / 2 for s in S[1:]]; F = [F[0]] + [fun(s) for s in S[1:]]
    return S[int(np.argmin(F))]


def main():
    ap = argparse.ArgumentParser(description="Track C from simulated jGCaMP8 dF/F at 30 and 10 Hz.")
    ap.add_argument("counts"); ap.add_argument("trace"); ap.add_argument("screen"); ap.add_argument("out")
    ap.add_argument("--variants", default="8m,8f,8s", help=f"saturating variants to score; the primary row is {PRIMARY} wherever it appears")
    ap.add_argument("--n0", default=",".join(map(str, N0_GRID)), help="photons per neuron per 33.3 ms frame")
    ap.add_argument("--random-orders", type=int, default=20, help="random orders for the primary rows only")
    ap.add_argument("--no-linear", action="store_true", help="skip the 8m linear (no saturation) contrast row")
    ap.add_argument("--lags", action="store_true", help="also score lagged frames (k..k+3 at 30 Hz, k..k+1 at 10 Hz)")
    ap.add_argument("--seed", type=int, default=0, help="photon noise seed")
    a = ap.parse_args()
    import pandas as pd
    z = np.load(a.counts)
    counts, bin_ms = z["counts"], float(z["bin_ms"])
    if abs(bin_ms - 10.0) > 1e-6:
        raise SystemExit(f"needs a 10 ms recording (--brain-bin-ms 10); this file has {bin_ms:g} ms bins")
    trace = json.load(open(a.trace))
    log = trace["trace"]
    phi = np.array([r["state"] for r in log], dtype=np.float32)[:, :, trace["state_names"].index("phi_dot")]
    done = np.array([r["done"] for r in log], dtype=bool)
    ctrl_ms = 1000.0 * (log[1]["t"] - log[0]["t"])
    if abs(ctrl_ms - bin_ms) > 1e-6:
        raise SystemExit(f"control step {ctrl_ms:g} ms differs from the {bin_ms:g} ms bins")
    nb = min(counts.shape[0], phi.shape[0])
    counts, phi, done = counts[:nb], phi[:nb], done[:nb]
    del trace, log
    site, rows = z["site"].astype(str), z["rows"]
    screen_r = pd.read_parquet(a.screen).set_index("row").loc[rows, "r_phi_dot"].to_numpy()
    n0s = [int(x) for x in a.n0.split(",")]
    targets = {fm: frame_targets(phi, done, ctrl_ms, fm, int(np.floor(nb * bin_ms / fm + 1e-9))) for fm in (T30, T10)}
    out = {"counts": a.counts, "trace": a.trace, "screen": a.screen, "source": SOURCE, "params": PARAMS,
           "n0_primary": N0_PRIMARY, "burn_ms": BURN_MS, "frame_ms": {"30": T30, "10": T10}, "rows": []}
    def emit(row, F, fm, n_random, lags=1):
        y, ok = targets[fm]
        r = dict(row, frame_ms=fm, lags=lags, **score_row(F, y, ok, fm, site, screen_r, n_random, lags))
        out["rows"].append(r)
        print(json.dumps({k: v for k, v in r.items() if k != "sites"}),
              {s: (v["r2_all"], {k: x["n90_screen"] for k, x in v["references"].items()}) for s, v in r["sites"].items()},
              flush=True)
    for fm, hz in ((T30, 30), (T10, 10)):  # matched spike baseline on the same frames and burn-in
        emit({"kind": "spikes", "rate_hz": hz}, spike_frames(counts, bin_ms, fm), fm, 0)
    rows_to_run = [(v, True) for v in a.variants.split(",")] + ([] if a.no_linear else [(PRIMARY, False)])
    for vi, (variant, sat) in enumerate(rows_to_run):
        F30, F10 = dff_frames(counts, bin_ms, (T30, T10), variant, sat)
        for n0 in n0s:
            primary = variant == PRIMARY and sat and n0 == N0_PRIMARY
            nr = a.random_orders if primary else 0
            row = {"kind": "calcium", "variant": variant, "saturation": sat, "n0": n0, "primary": primary}
            rng = np.random.default_rng([a.seed, vi, n0])
            N30 = add_noise(F30, n0, T30, rng)
            emit(dict(row, rate_hz=30, acquisition="own"), N30, T30, nr)
            N10 = add_noise(F10, n0, T10, rng)
            emit(dict(row, rate_hz=10, acquisition="own"), N10, T10, nr)
            emit(dict(row, rate_hz=10, acquisition="avg3_of_30hz"), average_frames(N30), T10, 0)
            if a.lags and primary:
                emit(dict(row, rate_hz=30, acquisition="own"), N30, T30, 0, lags=4)
                emit(dict(row, rate_hz=10, acquisition="own"), N10, T10, 0, lags=2)
        del F30, F10
    json.dump(out, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()

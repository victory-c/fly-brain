#!/usr/bin/env python3
"""Track C decodability from one replay (preregistration section 7): ridge regression from spike counts in 100 ms bins
to the bike's roll rate, and N90, the number of neurons needed to reach 90% of the R^2 of the whole site.

Input: `runs/ride.py --replay ... --counts-out COUNTS.npz --trace TRACE.json` (best run with --offroad 0, so that every
rider gives 15 s) and that brain's passenger screen. Needs pandas with pyarrow (the compute node's venv). From fly_brain/:

    PYTHONPATH=. python ../tools/track_c.py COUNTS.npz TRACE.json results/rungs/screens/r0.parquet OUT.json

Cross-validation is 5 folds over riders, so a test rider's bins never train the model. The ridge penalty is chosen once
per site, by an inner split of the training riders with all of the site's neurons, and kept for the smaller subsets.
Screen order is decreasing |r_phi_dot| in the brain's own screen; random order is 20 shuffles. Only neurons that spiked
during the replay count as candidates. Simulated calcium imaging and the probe-distance sweep are not done here.
"""
import json
import sys

import numpy as np
import pandas as pd

LAMBDAS = 10.0 ** np.arange(-1, 6.01, 1.0)
SIZES = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512, 768, 1024]


def align(counts, bin_ms, trace):
    """Stack (samples, neurons) of counts, the bin-mean roll rate, and each sample's rider."""
    log = trace["trace"]
    phi_dot = trace["state_names"].index("phi_dot")
    state = np.array([r["state"] for r in log], dtype=np.float32)  # (steps, riders, 8)
    done = np.array([r["done"] for r in log], dtype=bool)
    ctrl_ms = 1000.0 * (log[1]["t"] - log[0]["t"])
    per_bin = int(round(bin_ms / ctrl_ms))
    n_bins = min(counts.shape[0], state.shape[0] // per_bin)
    X, y, rider = [], [], []
    for b in range(n_bins):
        lo, hi = b * per_bin, (b + 1) * per_bin
        ok = ~done[lo:hi].any(0)  # the rider was riding for the whole bin
        X.append(counts[b, ok]); y.append(state[lo:hi, ok, phi_dot].mean(0)); rider.append(np.flatnonzero(ok))
    return np.concatenate(X).astype(np.float64), np.concatenate(y).astype(np.float64), np.concatenate(rider)


def ridge_r2(Xtr, ytr, Xte, yte, lam):
    mu, sd = Xtr.mean(0), Xtr.std(0)
    sd[sd == 0] = 1.0
    A, B = (Xtr - mu) / sd, (Xte - mu) / sd
    y0 = ytr.mean()
    w = np.linalg.solve(A.T @ A + lam * np.eye(A.shape[1]), A.T @ (ytr - y0))
    return B @ w + y0


def cv_r2(X, y, rider, folds, lam):
    """Pooled out-of-fold R^2."""
    pred = np.zeros_like(y)
    for f in folds:
        te = np.isin(rider, f)
        pred[te] = ridge_r2(X[~te], y[~te], X[te], y[te], lam)
    return float(1.0 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum())


def pick_lambda(X, y, rider, folds):
    """The penalty with the best R^2 on an inner split of each fold's training riders."""
    score = np.zeros(len(LAMBDAS))
    for f in folds:
        tr_r = np.setdiff1d(np.unique(rider), f)
        inner = tr_r[::5]
        tr, va = np.isin(rider, np.setdiff1d(tr_r, inner)), np.isin(rider, inner)
        for i, lam in enumerate(LAMBDAS):
            p = ridge_r2(X[tr], y[tr], X[va], y[va], lam)
            score[i] -= ((y[va] - p) ** 2).sum()
    return float(LAMBDAS[int(np.argmax(score))])


def n90(X, y, rider, folds, lam, order, target):
    """Curve of R^2 against neurons added in `order`, and the smallest count reaching target."""
    sizes = [s for s in SIZES if s < len(order)] + [len(order)]
    curve = {}
    r2 = lambda k: curve.setdefault(k, cv_r2(X[:, order[:k]], y, rider, folds, lam))
    lo = 0
    for s in sizes:
        if r2(s) >= target:
            while s - lo > 1:  # the curve is close to monotone: bisect between the two grid points
                m = (lo + s) // 2
                if r2(m) >= target:
                    s = m
                else:
                    lo = m
            return s, {int(k): round(v, 4) for k, v in sorted(curve.items())}
        lo = s
    return None, {int(k): round(v, 4) for k, v in sorted(curve.items())}


def main():
    counts_path, trace_path, screen_path, out_path = sys.argv[1:5]
    z = np.load(counts_path)
    trace = json.load(open(trace_path))
    screen = pd.read_parquet(screen_path).set_index("row")
    X_all, y, rider = align(z["counts"], float(z["bin_ms"]), trace)
    rows, site = z["rows"], z["site"].astype(str)
    riders = np.unique(rider)
    rng = np.random.default_rng(0)
    folds = np.array_split(rng.permutation(riders), 5)
    out = {"counts": counts_path, "trace": trace_path, "screen": screen_path, "samples": int(len(y)), "riders": int(len(riders)),
           "roll_rate_sd": float(y.std()), "sites": {}}
    for name in ("descending", "wing_motor"):
        m = (site == name) & (X_all.sum(0) > 0)
        X, r = X_all[:, m], rows[m]
        lam = pick_lambda(X, y, rider, folds)
        full = cv_r2(X, y, rider, folds, lam)
        target = 0.9 * full
        by_screen = np.argsort(-np.abs(np.nan_to_num(screen.loc[r, "r_phi_dot"].to_numpy())), kind="stable")
        n_screen, curve = n90(X, y, rider, folds, lam, by_screen, target)
        rand = [n90(X, y, rider, folds, lam, np.random.default_rng(100 + i).permutation(X.shape[1]), target)[0] for i in range(20)]
        rand = [x for x in rand if x is not None]
        out["sites"][name] = {"neurons": int((site == name).sum()), "active": int(m.sum()), "lambda": lam, "r2_all": round(full, 4),
                              "target_r2": round(target, 4), "n90_screen": n_screen, "n90_random_median": float(np.median(rand)),
                              "n90_random_q25_q75": [float(x) for x in np.percentile(rand, [25, 75])], "r2_screen_curve": curve}
    print(json.dumps({k: v for k, v in out.items() if k != "sites"}))
    for k, v in out["sites"].items():
        print(k, {a: b for a, b in v.items() if a != "r2_screen_curve"})
    json.dump(out, open(out_path, "w"), indent=1)


if __name__ == "__main__":
    main()

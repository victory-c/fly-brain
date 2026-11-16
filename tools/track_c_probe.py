#!/usr/bin/env python3
"""Track C probe-distance sweep (preregistration section 7): R^2 of roll rate decoded from a ball-shaped probe that misses
a named target soma by d um.

A probe is a ball of radius r in {10, 25, 50} um that records every neuron whose soma (web_data/atlas.npz `xyz_um`, um)
lies inside it, all with the same weight; neurons without a position are never recorded. The targets are named somata,
fixed on the real wiring and the same on every rung (positions do not change across rungs):

    descending   DNp20_R (primary), DNp20_L (mirror replicate)
    wing_motor   hg4 MN_L (primary), hg4 MN_R (mirror replicate)

The probe centre is target + d * u, d = 0, 5, ..., 50 um, u one of 20 fixed unit directions (a Fibonacci sphere). R^2 is
track_c's: ridge on 100 ms counts, the same 5 rider folds, pooled out-of-fold R^2. The penalty is chosen once per
(target, r), on the d = 0 ball's active neurons, and kept for every d and u. A ball with no neuron in it scores 0.

Two modes, from ~/flybrain (pandas with pyarrow: venv/bin/python):

    python tools/track_c_probe.py rows ROWS.json
        every row within max(d) + max(r) = 100 um of any target, for runs/ride.py --probe-rows (the json is a dict
        whose "rows" ride.py reads), with each row's position, the targets, counts per target and the site neurons
        that have no position
    python tools/track_c_probe.py fit PROBE100.npz TRACE.json ROWS.json TRACK_C.json OUT.json
        PROBE100.npz from ride.py --probe-counts-out (rows saved in it), TRACK_C.json the brain's tools/track_c.py output
        (its sites' r2_all is the full-site R^2 each probe is also reported as a fraction of)
"""
import argparse
import json
from pathlib import Path

import numpy as np

from track_c import align, cv_r2, pick_lambda, sum_bins

FLY = Path(__file__).resolve().parents[1] / "fly_brain"
ATLAS, META = FLY / "web_data" / "atlas.npz", FLY / "brain_meta.parquet"
TARGETS = {"descending": ["DNp20_R", "DNp20_L"], "wing_motor": ["hg4 MN_L", "hg4 MN_R"]}  # primary, replicate
RADII = (10.0, 25.0, 50.0)
DISTANCES = tuple(float(d) for d in range(0, 51, 5))
N_DIRECTIONS = 20
REACH = max(DISTANCES) + max(RADII)  # 100 um


def directions(n=N_DIRECTIONS):
    """n unit vectors spread evenly on the sphere (Fibonacci lattice), the same on every brain."""
    i = np.arange(n) + 0.5
    z = 1.0 - 2.0 * i / n
    phi = np.pi * (3.0 - np.sqrt(5.0)) * np.arange(n)
    s = np.sqrt(1.0 - z ** 2)
    return np.stack([s * np.cos(phi), s * np.sin(phi), z], 1)


def site_labels(meta):
    """CountRecorder's site of every row: descending / wing_motor / ''."""
    sc, sub = meta["superclass"].to_numpy(), meta["subclass"].to_numpy()
    return np.where(sc == "descending_neuron", "descending", np.where((sc == "vnc_motor") & (sub == "wm"), "wing_motor", ""))


def load_geometry(atlas=ATLAS, meta=META):
    """(n, 3) soma positions in um (NaN: none) and the per-neuron table, in simulator row order."""
    import pandas as pd
    m = pd.read_parquet(meta, columns=["row", "type", "instance", "superclass", "subclass"]).sort_values("row")
    assert np.array_equal(m["row"].to_numpy(), np.arange(len(m))), "brain_meta.parquet is not in row order"
    xyz = np.full((len(m), 3), np.nan)
    with np.load(atlas) as z:
        xyz[z["row"]] = z["xyz_um"]
    return xyz, m.reset_index(drop=True)


def target_rows(meta, xyz):
    """{name: row} of the named targets; each name must be exactly one neuron of its site, with a position."""
    inst, lab = meta["instance"].fillna("").to_numpy(), site_labels(meta)
    out = {}
    for site, names in TARGETS.items():
        for name in names:
            hit = np.flatnonzero(inst == name)
            if len(hit) != 1:
                raise SystemExit(f"{name!r} names {len(hit)} neurons, not one")
            row = int(hit[0])
            if lab[row] != site:
                raise SystemExit(f"{name!r} (row {row}) is not in the {site} site")
            if np.isnan(xyz[row]).any():
                raise SystemExit(f"{name!r} (row {row}) has no position")
            out[name] = row
    return out


def rows_mode(a):
    xyz, meta = load_geometry(a.atlas, a.meta)
    tg = target_rows(meta, xyz)
    inst, lab = meta["instance"].fillna("").to_numpy(), site_labels(meta)
    has = ~np.isnan(xyz).any(1)
    dist = {name: np.linalg.norm(xyz - xyz[row], axis=1) for name, row in tg.items()}  # NaN compares False below
    keep = np.zeros(len(xyz), dtype=bool)
    targets = {}
    for site, names in TARGETS.items():
        for k, name in enumerate(names):
            row, d = tg[name], dist[name]
            keep |= d <= REACH
            targets[name] = {"site": site, "role": "primary" if k == 0 else "replicate", "row": row,
                             "xyz_um": [round(float(v), 3) for v in xyz[row]],
                             "within_um": {f"{r:g}": int((d <= r).sum()) for r in (10, 25, 50, 75, REACH)},
                             "site_neurons_within_um": {f"{r:g}": int(((d <= r) & (lab == site)).sum()) for r in (10, 25, 50, 75, REACH)}}
    rows = np.flatnonzero(keep)
    unplaced = {site: [{"row": int(r), "instance": inst[r]} for r in np.flatnonzero((lab == site) & ~has)] for site in TARGETS}
    out = {"rows": rows.tolist(), "xyz_um": np.round(xyz[rows], 3).tolist(), "site": lab[rows].tolist(),
           "atlas": str(a.atlas), "units": "um (atlas.npz xyz_um = 8 nm voxels * 0.008)", "reach_um": REACH,
           "radii_um": list(RADII), "distances_um": list(DISTANCES), "directions": np.round(directions(), 6).tolist(),
           "targets": targets, "union": int(len(rows)),
           "neurons": int(len(xyz)), "neurons_without_position": int((~has).sum()),
           "site_neurons_without_position": unplaced}
    Path(a.out).write_text(json.dumps(out))
    for name, t in targets.items():
        print(f"{name:9s} row {t['row']:6d} {t['site']:10s} at {t['xyz_um']}  within {t['within_um']}  site neurons {t['site_neurons_within_um']}")
    print(f"union within {REACH:g} um: {len(rows):,} rows -> {a.out}")
    print(f"{int((~has).sum()):,} of {len(xyz):,} neurons have no position; site neurons without one:",
          {s: [u["instance"] or u["row"] for u in v] for s, v in unplaced.items()})


def fit_mode(a):
    z = np.load(a.probe)
    counts, bin_ms, prow = z["counts"], float(z["bin_ms"]), z["rows"].astype(np.int64)
    if a.sum_to_ms is not None:
        counts, bin_ms = sum_bins(counts, bin_ms, a.sum_to_ms)
    if abs(bin_ms - 100.0) > 1e-6:
        print(f"warning: the probe counts are in {bin_ms:g} ms bins, not 100 ms", flush=True)
    geo = json.loads(Path(a.rows).read_text())
    trace = json.loads(Path(a.trace).read_text())
    ref = json.loads(Path(a.track_c).read_text())
    X_all, y, rider = align(counts, bin_ms, trace)
    riders = np.unique(rider)
    folds = np.array_split(np.random.default_rng(0).permutation(riders), 5)  # track_c's folds
    pos = dict(zip(geo["rows"], np.asarray(geo["xyz_um"], dtype=float)))
    col = {int(r): i for i, r in enumerate(prow)}
    missing = sorted(set(geo["rows"]) - set(col))
    if missing:
        print(f"warning: {len(missing):,} geometry rows are not in {a.probe}; probes cannot see them", flush=True)
    rec = np.array([r for r in prow if r in pos], dtype=np.int64)  # recorded rows with a position
    rxyz = np.array([pos[r] for r in rec]).reshape(-1, 3)
    rcol = np.array([col[r] for r in rec], dtype=np.int64)
    active_col = X_all.sum(0) > 0
    U = np.asarray(geo["directions"], dtype=float) if geo.get("directions") else directions()  # the rows json's grid
    radii = [float(r) for r in (a.radii or geo.get("radii_um", RADII))]
    dists = [float(d) for d in (a.distances or geo.get("distances_um", DISTANCES))]
    reach = float(geo.get("reach_um", REACH))
    if max(radii) + max(dists) > reach + 1e-9:
        print(f"warning: r + d reaches {max(radii) + max(dists):g} um, past the {reach:g} um the rows json holds; "
              "far balls miss neurons", flush=True)
    out = {"probe": a.probe, "trace": a.trace, "rows": a.rows, "track_c": a.track_c, "bin_ms": bin_ms,
           "samples": int(len(y)), "riders": int(len(riders)), "recorded_rows": int(len(prow)),
           "recorded_rows_with_position": int(len(rec)), "geometry_rows_not_recorded": len(missing),
           "radii_um": radii, "distances_um": dists, "directions": int(len(U)),
           "lambda_rule": "once per (target, r): track_c pick_lambda on the d = 0 ball's active neurons",
           "empty_ball": "R^2 = 0", "site_neurons_without_position": geo.get("site_neurons_without_position"),
           "targets": {}}
    cache = {}  # the same set of neurons and penalty is fitted once

    def score(cols, lam):
        if len(cols) == 0:
            return 0.0
        key = (cols.tobytes(), lam)
        if key not in cache:
            cache[key] = cv_r2(X_all[:, cols], y, rider, folds, lam)
        return cache[key]

    for name, t in geo["targets"].items():
        site = t["site"]
        site_r2 = ref["sites"][site]["r2_all"] if site in ref.get("sites", {}) else None
        c0 = np.asarray(t["xyz_um"], dtype=float)
        res = {"site": site, "role": t.get("role"), "row": t["row"], "site_r2": site_r2, "radii": {}}
        for r in radii:
            def ball(centre):
                return rcol[np.linalg.norm(rxyz - centre, axis=1) <= r]
            b0 = ball(c0)
            act0 = b0[active_col[b0]]
            lam_from = f"{r:g}"
            if not len(act0):  # a silent d = 0 ball: borrow the penalty of the largest d = 0 ball that has an active neuron
                for rr in sorted(radii, reverse=True):
                    bb = rcol[np.linalg.norm(rxyz - c0, axis=1) <= rr]
                    act0, lam_from = bb[active_col[bb]], f"{rr:g}"
                    if len(act0):
                        break
            lam = pick_lambda(X_all[:, act0], y, rider, folds) if len(act0) else None
            if lam is None:  # no d = 0 ball of any radius has an active neuron: no penalty, every ball is scored 0
                lam_from = None
                print(f"warning: {name} r={r:g}: no active neuron in any d = 0 ball, every ball scored 0", flush=True)
            act0 = b0[active_col[b0]]
            per_d = {}
            for d in dists:
                r2, n, n_act = [], [], []
                for u in (U[:1] if d == 0 else U):  # every direction gives the same ball at d = 0
                    b = ball(c0 + d * u)
                    r2.append(score(b, lam) if lam is not None else 0.0); n.append(len(b)); n_act.append(int(active_col[b].sum()))
                if d == 0:
                    r2, n, n_act = r2 * len(U), n * len(U), n_act * len(U)
                r2 = np.array(r2)
                row = {"r2_median": round(float(np.median(r2)), 4),
                       "r2_q25_q75": [round(float(v), 4) for v in np.percentile(r2, [25, 75])],
                       "neurons_median": float(np.median(n)), "active_median": float(np.median(n_act)),
                       "empty": int(sum(k == 0 for k in n)), "r2": [round(float(v), 4) for v in r2], "neurons": n}
                if site_r2 is not None and site_r2 > 0:  # a site that decodes nothing (R^2 <= 0) has no fraction
                    f = r2 / site_r2
                    row["fraction_median"] = round(float(np.median(f)), 4)
                    row["fraction_q25_q75"] = [round(float(v), 4) for v in np.percentile(f, [25, 75])]
                per_d[f"{d:g}"] = row
            res["radii"][f"{r:g}"] = {"lambda": lam, "lambda_from_radius": lam_from, "neurons_d0": int(len(b0)), "active_d0": int(len(act0)), "d": per_d}
            print(f"{name:9s} r={r:g} lambda={lam} d=0: {len(b0)} neurons ({len(act0)} active); median R^2 by d:",
                  " ".join(f"{d}:{v['r2_median']:.3f}" for d, v in per_d.items()), flush=True)
        out["targets"][name] = res
    Path(a.out).write_text(json.dumps(out, indent=1))
    print(f"-> {a.out}  ({len(cache)} distinct fits)")


def main():
    ap = argparse.ArgumentParser(description="Track C probe-distance sweep.")
    sub = ap.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("rows", help="the rows within 100 um of the targets, for runs/ride.py --probe-rows")
    p.add_argument("out")
    p.add_argument("--atlas", default=str(ATLAS)); p.add_argument("--meta", default=str(META))
    p = sub.add_parser("fit", help="R^2 per (target, r, d, direction) from a probe recording")
    p.add_argument("probe"); p.add_argument("trace"); p.add_argument("rows"); p.add_argument("track_c"); p.add_argument("out")
    p.add_argument("--sum-to-ms", type=float, default=None, help="sum the file's bins into bins of this length first")
    p.add_argument("--radii", type=float, nargs="+", default=None, help="override the rows json's radii (testing)")
    p.add_argument("--distances", type=float, nargs="+", default=None, help="override the rows json's distances (testing)")
    a = ap.parse_args()
    (rows_mode if a.mode == "rows" else fit_mode)(a)


if __name__ == "__main__":
    main()

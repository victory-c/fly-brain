"""Whole-brain replays of Shiu et al.'s stimulation experiments for the activity dashboard -> dashboard/data/.

Each experiment drives named neuron groups (brain/stimuli.py) with Poisson input for 1 s in `--trials` flies and
keeps every neuron's spikes in 50 ms bins:
  <id>.bin    uint8 (n_bins, n_points) firing rate of each 3D point (brain/atlas.py), 255 = CLOUD_HZ
  <id>.json   traces: MN9 L/R, each driven group, brain regions, population; the most active cell types
plus index.json listing experiments, regions and bins, the point positions (points.f32) and each point's region
(point_region.bin). export/pack_dashboard.py then turns the .bin files into the PNGs and the .js the page loads.

    python -m export.export_dashboard [--trials 8] [--only sugar,bitter]
"""
import argparse
import json

import numpy as np

from brain import stimuli
from brain.atlas import CLOUD_HZ, REGIONS, point_cloud, regions
from brain.connectome import ROOT, Brain
from brain.engine import W_SYN, experiment

OUT = ROOT / "dashboard" / "data"
BIN_MS = 50.0
HZ = stimuli.SHIU_HZ

# (id, name, {group: Hz}, what Shiu et al. 2024 found for it)
EXPERIMENTS = [
    ("sugar", "Sugar taste neurons", {"sugar": HZ}, "Sugar GRNs alone drive MN9: the proboscis extends"),
    ("sugar_weak", "Sugar, weak (40 Hz)", {"sugar": 40.0}, "Below about 50 Hz sugar input, MN9 barely responds"),
    ("water", "Water taste neurons", {"water": HZ}, "Water GRNs also drive MN9, through partly separate paths"),
    ("sugar_water", "Sugar + water", {"sugar": HZ, "water": HZ}, "The two appetitive inputs add up"),
    ("bitter", "Bitter taste neurons", {"bitter": HZ}, "Bitter GRNs alone do not move MN9"),
    ("sugar_bitter", "Sugar + bitter", {"sugar": HZ, "bitter": HZ}, "Bitter input suppresses sugar-evoked feeding"),
    ("ir94e", "Ir94e taste neurons", {"ir94e": HZ}, "Ir94e GRNs alone do not move MN9"),
    ("sugar_ir94e", "Sugar + Ir94e", {"sugar": HZ, "ir94e": HZ}, "Ir94e input mildly suppresses feeding"),
    ("jo_ce", "Antenna: JO-CE neurons", {"jo_ce": HZ}, "Johnston's organ C/E neurons start antennal grooming"),
    ("jo_f", "Antenna: JO-F neurons", {"jo_f": HZ}, "Johnston's organ F neurons, also grooming-related"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=8)
    ap.add_argument("--ms", type=float, default=1000.0)
    ap.add_argument("--only", default="")
    ap.add_argument("--device", default="cuda")
    a = ap.parse_args()
    only = [s for s in a.only.split(",") if s]
    OUT.mkdir(parents=True, exist_ok=True)

    brain = Brain()
    meta = stimuli.neurons()
    mn9 = stimuli.mn9()
    xyz, point_idx = point_cloud()
    xyz.tofile(OUT / "points.f32")
    reg = regions(meta)
    reg_ids = [r for r, _ in REGIONS]
    reg_masks = {r: reg == r for r in reg_ids}
    np.array([reg_ids.index(r) for r in reg[point_idx]], dtype=np.uint8).tofile(OUT / "point_region.bin")
    n_bins = int(round(a.ms / BIN_MS))
    index = {"binMs": BIN_MS, "bins": n_bins, "trials": a.trials, "cloudHz": CLOUD_HZ, "points": int(len(point_idx)),
             "neurons": int(brain.n), "wSyn": W_SYN, "pointRegion": "point_region.bin",
             "regions": [{"id": r, "label": lab, "n": int(reg_masks[r].sum())} for r, lab in REGIONS],
             "groups": {g: {"types": t, "n": int(len(stimuli.group(g)))} for g, t in stimuli.shiu_groups().items()},
             "experiments": []}
    old = OUT / "index.json"
    if only and old.exists():  # keep the experiments that are not rerun
        index["experiments"] = [e for e in json.loads(old.read_text())["experiments"] if e["id"] not in only]

    for eid, name, drive, finding in EXPERIMENTS:
        if only and eid not in only:
            continue
        groups = {g: stimuli.group(g) for g in drive}
        stim = np.concatenate(list(groups.values()))
        hz_in = np.concatenate([np.full(len(groups[g]), drive[g], np.float32) for g in drive])
        print(f"== {name}: " + ", ".join(f"{g} {len(groups[g])} neurons at {drive[g]:.0f} Hz" for g in drive), flush=True)
        r = experiment(brain, stim, hz_in, flies=a.trials, ms=a.ms, bin_ms=BIN_MS, record_neurons=np.arange(brain.n),
                       params={"w_syn": W_SYN}, device=a.device)
        hz = r["binned"].mean(0) / (BIN_MS / 1000.0)  # (N, bins)
        cloud = np.clip(hz[point_idx].T / CLOUD_HZ * 255, 0, 255).astype(np.uint8)  # (bins, points)
        cloud.tofile(OUT / f"{eid}.bin")
        driven = np.zeros(brain.n, bool)
        driven[stim] = True
        per_fly = r["binned"][:, mn9[0]].sum(1) / (a.ms / 1000.0)
        lit = meta.loc[(hz.mean(1) > 10) & ~driven & (reg != "visual")].groupby("type").size()
        lit = lit.sort_values(ascending=False)
        rec = {
            "id": eid, "name": name, "finding": finding, "drive": drive,
            "inputNeurons": int(driven.sum()),
            "mn9Hz": float(per_fly.mean()), "mn9Trials": per_fly.round(0).tolist(),
            "mn9": {"L": hz[mn9[0]].round(1).tolist(), "R": hz[mn9[1]].round(1).tolist()},
            "groups": {g: hz[idx].mean(0).round(1).tolist() for g, idx in groups.items()},
            "regions": {rid: hz[reg_masks[rid] & ~driven].mean(0).round(2).tolist() for rid in reg_ids},
            "activeCount": {rid: (hz[reg_masks[rid] & ~driven] > 10).sum(0).astype(int).tolist() for rid in reg_ids},
            "pop": (r["undriven_hz"] / 1000.0).round(1).tolist(),  # thousand spikes per second
            "lit": int(((hz.mean(1) > 2) & ~driven).sum()),
            "topTypes": [{"type": k, "n": int(v)} for k, v in lit.head(10).items()],
            "seconds": round(r["wall_s"], 1), "file": f"{eid}.bin",
        }
        (OUT / f"{eid}.json").write_text(json.dumps(rec), encoding="utf-8")
        index["experiments"] = [e for e in index["experiments"] if e["id"] != eid] + [
            {k: rec[k] for k in ("id", "name", "mn9Hz", "lit", "file")}]
        order = [e[0] for e in EXPERIMENTS]
        index["experiments"].sort(key=lambda e: order.index(e["id"]) if e["id"] in order else len(order))
        (OUT / "index.json").write_text(json.dumps(index, indent=1), encoding="utf-8")
        print(f"   MN9_L {rec['mn9Hz']:.1f} Hz, MN9_R {np.mean(rec['mn9']['R']):.1f} Hz, lit {rec['lit']:,}, "
              f"{rec['seconds']}s", flush=True)


if __name__ == "__main__":
    main()

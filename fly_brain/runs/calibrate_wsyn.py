"""Derive the male-CNS synaptic weight scale (W_SYN_SCALE in brain/engine.py) from Shiu et al.'s own FlyWire model.

Shiu's w_syn = 0.275 mV was fit on FlyWire (138,639 neurons, 393 synapses per neuron); the male CNS has 745
synapses per neuron, so the same weight overdrives it. The scale is chosen to reproduce Shiu's model, not tuned:

  1. reference  Shiu's network (FlyWire v783, Connectivity_783.parquet from their repository) at w_syn = 0.275 mV,
                their 21 labellar sugar GRNs driven at 0-200 Hz -> MN9 rate (the feeding curve of their Fig. 1)
  2. male CNS   one labellum's sugar GRNs (stimuli.group("sugar", side)), same rates, w_syn = 0.275 mV * scale
                -> the stronger MN9's rate, averaged over the two sides
  3. stability  at each scale, strong broad drive (both sides at 200 Hz: sugar, bitter, sugar + bitter, sugar +
                water, JO-CE) for 1 s; stable if in no condition the undriven activity of the last 200 ms exceeds
                that of either of the first two 200 ms windows by more than 25% (runaway growth, slow or fast)
  W_SYN_SCALE = the stable scale whose MN9 curve is closest to the reference (least squares over the rates).

    python -m runs.calibrate_wsyn [--scales 0.3,0.35,...] [--flies 12]  -> results/calibrate_wsyn.json
"""
import argparse
import json
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from brain import stimuli
from brain.connectome import Brain
from brain.engine import PARAMS, Engine

ROOT = Path(__file__).resolve().parents[1]
SHIU = ROOT / "data" / "shiu"
SHIU_URL = "https://raw.githubusercontent.com/philshiu/Drosophila_brain_model/main/"
SHIU_SUGAR = [  # neu_sugar of Shiu's figures.ipynb: labellar sugar GRNs (FlyWire root IDs)
    720575940624963786, 720575940630233916, 720575940637568838, 720575940638202345, 720575940617000768,
    720575940630797113, 720575940632889389, 720575940621754367, 720575940621502051, 720575940640649691,
    720575940639332736, 720575940616885538, 720575940639198653, 720575940620900446, 720575940617937543,
    720575940632425919, 720575940633143833, 720575940612670570, 720575940628853239, 720575940629176663,
    720575940611875570]
SHIU_MN9 = 720575940660219265
FREQS = np.arange(0, 201, 20, dtype=np.float32)
STRESS = ["sugar", "bitter", "sugar+bitter", "sugar+water", "jo_ce"]


def flywire_brain():
    """Shiu's FlyWire v783 network as a Brain (cached in data/shiu/)."""
    npz = SHIU / "flywire_783.npz"
    if not npz.exists():
        SHIU.mkdir(parents=True, exist_ok=True)
        for f in ("Connectivity_783.parquet", "Completeness_783.csv"):
            if not (SHIU / f).exists():
                urllib.request.urlretrieve(SHIU_URL + f, SHIU / f)
        ids = pd.read_csv(SHIU / "Completeness_783.csv", index_col=0).index.to_numpy(np.int64)
        c = pd.read_parquet(SHIU / "Connectivity_783.parquet",
                            columns=["Presynaptic_Index", "Postsynaptic_Index", "Excitatory x Connectivity"])
        c = c.sort_values(["Presynaptic_Index", "Postsynaptic_Index"])
        ptr = np.zeros(len(ids) + 1, np.int64)
        np.cumsum(np.bincount(c["Presynaptic_Index"], minlength=len(ids)), out=ptr[1:])
        np.savez(npz, body_ids=ids, ptr=ptr, post=c["Postsynaptic_Index"].to_numpy(np.int32),
                 syn=c["Excitatory x Connectivity"].to_numpy(np.float32))
    return Brain(npz)


def run(brain, inputs, rates, flies, w_syn, device, ms=1000.0, seed=0):
    """rates: (conditions, n_inputs) Hz. Returns spike counts (conditions, flies, N) and undriven spikes per
    200 ms window (conditions, flies, windows)."""
    C = len(rates)
    eng = Engine(brain, C * flies, inputs, params={"w_syn": w_syn}, device=device, seed=seed)
    eng.drive(np.repeat(np.asarray(rates, np.float32), flies, axis=0))
    undriven, windows, last = ~eng.is_input, [], torch.zeros_like(eng.count)
    for _ in range(int(ms // 200)):
        eng.run(200.0)
        windows.append((eng.count - last)[:, undriven].sum(1))
        last = eng.count.clone()
    return (eng.count.view(C, flies, -1).cpu().numpy(),
            torch.stack(windows, 1).view(C, flies, -1).cpu().numpy(), eng.seconds)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scales", default="0.3,0.35,0.4,0.45,0.46,0.47,0.48,0.49,0.5,0.55,0.6")
    ap.add_argument("--flies", type=int, default=12)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--out", default="results/calibrate_wsyn.json")
    a = ap.parse_args()
    out = {"freqs_hz": FREQS.tolist(), "flies": a.flies, "w_syn_shiu": PARAMS["w_syn"], "scales": {}}

    fw = flywire_brain()
    sugar_fw = fw.index_of(SHIU_SUGAR)
    mn9_fw = int(fw.index_of([SHIU_MN9])[0])
    counts, _, sec = run(fw, sugar_fw, np.repeat(FREQS[:, None], len(sugar_fw), 1), a.flies, PARAMS["w_syn"], a.device)
    ref = counts[:, :, mn9_fw].mean(1)  # Hz (1 s runs)
    out["reference"] = {"neurons": fw.n, "sugar_grns": len(sugar_fw), "mn9_hz": ref.round(2).tolist()}
    print(f"FlyWire (Shiu): {len(sugar_fw)} sugar GRNs -> MN9 " + " ".join(f"{f:.0f}:{r:.0f}" for f, r in zip(FREQS, ref))
          + f"   ({sec:.0f}s)", flush=True)
    del fw

    brain = Brain()
    mn9 = stimuli.mn9()
    g = {k: stimuli.group(k) for k in ("sugar", "bitter", "water", "jo_ce")}
    inputs = np.unique(np.concatenate(list(g.values())))
    pos = {int(n): i for i, n in enumerate(inputs)}

    def rates_for(groups, hz, side=None):
        r = np.zeros(len(inputs), np.float32)
        for k in groups:
            for n in (stimuli.group(k, side) if side else g[k]):
                r[pos[int(n)]] = hz
        return r

    conds = [("sugar", side, f) for side in ("L", "R") for f in FREQS]
    stress = {"sugar": ["sugar"], "bitter": ["bitter"], "sugar+bitter": ["sugar", "bitter"],
              "sugar+water": ["sugar", "water"], "jo_ce": ["jo_ce"]}
    rates = np.stack([rates_for(["sugar"], f, side) for _, side, f in conds] +
                     [rates_for(stress[s], 200.0) for s in STRESS])
    for scale in [float(s) for s in a.scales.split(",")]:
        counts, win, sec = run(brain, inputs, rates, a.flies, PARAMS["w_syn"] * scale, a.device)
        n = len(conds)
        mn9_hz = counts[:n][:, :, mn9].mean(1)                   # (conds, 2)
        curve = mn9_hz.max(1).reshape(2, len(FREQS)).mean(0)      # stronger MN9, mean of the two sides
        w = win[n:].mean(1)                                      # (stress, windows) undriven spikes per fly
        growth = w[:, -1] / np.maximum(np.minimum(w[:, 0], w[:, 1]), 1.0)
        rec = {"mn9_hz": curve.round(2).tolist(),
               "mn9_by_side": {s: mn9_hz[i * len(FREQS):(i + 1) * len(FREQS)].round(1).tolist()
                               for i, s in enumerate(("L", "R"))},
               "rmse_vs_reference": float(np.sqrt(np.mean((curve - ref) ** 2))),
               "stress": {s: {"undriven_hz_per_window": (w[i] * 5).round(0).tolist(), "growth": float(growth[i])}
                          for i, s in enumerate(STRESS)},
               "stable": bool((growth < 1.25).all()), "seconds": sec}
        out["scales"][f"{scale:g}"] = rec
        print(f"scale {scale:.2f}: MN9 " + " ".join(f"{c:.0f}" for c in curve) + f"  rmse {rec['rmse_vs_reference']:.1f}"
              f"  growth " + " ".join(f"{s} {x:.2f}" for s, x in zip(STRESS, growth))
              + f"  {'stable' if rec['stable'] else 'RUNAWAY'}  ({sec:.0f}s)", flush=True)

    stable = {s: r for s, r in out["scales"].items() if r["stable"]}
    best = min(stable, key=lambda s: stable[s]["rmse_vs_reference"]) if stable else None
    out["chosen_scale"] = float(best) if best else None
    (ROOT / a.out).write_text(json.dumps(out, indent=1))
    print(f"-> {a.out}: W_SYN_SCALE = {best}")


if __name__ == "__main__":
    main()

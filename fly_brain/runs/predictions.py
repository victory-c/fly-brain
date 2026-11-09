"""Track B scoring pilot: decoder-free predictions on the real wiring and on rewired brains.

Runs the conditions of scrambled-brains docs/track_b_predictions.csv, at Shiu's 150 Hz unless the row sets a rate
(sugar dose 20 and 100 Hz, as flybench's dose_response), for 1 s in 30 flies. The looming detectors are LPLC2 and LC4 on both sides. Taste groups are driven on one side (Shiu's one
labellum; --taste-side), Johnston's organ groups on both. With no input the network is silent, so "no stimulus" is 0 Hz.

    python -m runs.predictions --out results/track_b/r0.json
    python -m runs.predictions --brain results/variants/r1_s1.npz --out results/track_b/r1_s1.json
"""
import argparse
import json

import numpy as np

from brain import stimuli
from brain.connectome import Brain
from brain.engine import PARAMS, W_SYN, experiment

SIGNED = [("sugar_mn9", "mn9", "sugar", None, 1), ("bitter_suppression", "mn9", "sugar+bitter", "sugar", -1),
          ("ir94e_suppression", "mn9", "sugar+ir94e", "sugar", -1), ("dose_response", "mn9", "sugar@100", "sugar@20", 1),
          ("loom_gf", "gf", "loom", None, 1), ("loom_dnp02_dnp11", "dnp", "loom", None, 1)]
NULL = [("bitter_alone_mn9", "mn9", "bitter"), ("sugar_gf_crosstalk", "gf", "sugar")]
TASTE = {"sugar", "water", "bitter", "ir94e"}
LOOM_TYPES = ["LPLC2", "LC4"]


def rate(cond):
    """A condition is groups joined by '+', with an optional '@Hz'; the default rate is Shiu's 150 Hz."""
    return float(cond.split("@")[1]) if "@" in cond else stimuli.SHIU_HZ


def inputs(cond, taste_side):
    m = stimuli.neurons()
    groups = [m.loc[m["type"].isin(LOOM_TYPES), "row"].to_numpy(np.int64) if g == "loom" else
              stimuli.group(g, side=(None if taste_side == "both" else taste_side) if g in TASTE else None)
              for g in cond.split("@")[0].split("+")]
    return np.unique(np.concatenate(groups))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain", default=None)
    ap.add_argument("--w-syn-scale", type=float, default=None, help="default: the calibrated W_SYN (scale 0.47)")
    ap.add_argument("--flies", type=int, default=30)
    ap.add_argument("--ms", type=float, default=1000.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--taste-side", default="R", choices=["L", "R", "both"], help="the side of the taste groups (at scale 0.47 the left side barely drives MN9 on the real wiring)")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    brain = Brain(a.brain) if a.brain else Brain()
    w = W_SYN if a.w_syn_scale is None else PARAMS["w_syn"] * a.w_syn_scale
    m = stimuli.neurons()
    read = {"mn9": stimuli.mn9(), "mdn": m.loc[m["type"] == "MDN", "row"].to_numpy(np.int64),
            "gf": np.array([stimuli.instance("DNp01(GF)_L"), stimuli.instance("DNp01(GF)_R")], dtype=np.int64),
            "dnp": m.loc[m["type"].isin(["DNp02", "DNp11"]), "row"].to_numpy(np.int64)}
    conds = sorted({r[2] for r in SIGNED} | {r[3] for r in SIGNED if r[3]} | {r[2] for r in NULL})
    rec = np.unique(np.concatenate(list(read.values())))
    rates = {}
    for c in conds:
        r = experiment(brain, inputs(c, a.taste_side), rate(c), flies=a.flies, ms=a.ms, bin_ms=a.ms, record_neurons=rec,
                       params={"w_syn": w}, seed=a.seed, device=a.device)
        rates[c] = {k: float(r["mean_hz"][v].mean()) for k, v in read.items()}
        print(c, {k: round(v, 2) for k, v in rates[c].items()}, f"network {float(np.mean(r['undriven_hz'])):,.0f}", flush=True)
    signed = []
    for name, ro, c, ref, sign in SIGNED:
        d = rates[c][ro] - (rates[ref][ro] if ref else 0.0)
        signed.append({"id": name, "difference_hz": round(d, 3), "expected_sign": sign, "as_expected": bool(np.sign(d) == sign)})
    nulls = [{"id": name, "rate_hz": round(rates[c][ro], 3)} for name, ro, c in NULL]
    out = {"brain": a.brain or "brain.npz", "w_syn": w, "flies": a.flies, "ms": a.ms, "seed": a.seed, "taste_side": a.taste_side, "rates": rates, "signed": signed,
           "score": sum(s["as_expected"] for s in signed) / len(signed), "null_rows": nulls}
    print("score", out["score"], [s["id"] for s in signed if not s["as_expected"]])
    json.dump(out, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()

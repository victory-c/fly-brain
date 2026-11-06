#!/usr/bin/env python3
"""Where the sign flips of an R1 draw (brain/variants.py r1) fall: over the whole brain, among the driven
sensory neurons, among the hand-picked `lane` readout, and by synapse count.

Needs pandas with pyarrow (the compute node's venv, not the login VM). Run from fly_brain/:

    PYTHONPATH=. python ../tools/r1_flips.py results/variants/r1_s1.npz results/rungs/r1_s1_cpu/sign_flips.json
"""
import json
import sys

import numpy as np
import pandas as pd

from bike.readout import READOUTS
from bike.senses import sensory_populations
from brain.variants import CHLORIDE_TRANSMITTERS


def strings(col):
    return np.array([str(x) for x in col.to_numpy()])


def main():
    variant, out_path = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else None)
    meta = pd.read_parquet("brain_meta.parquet")
    z = np.load(variant, allow_pickle=True)
    flipped, relabelled = z["sign_flipped"].astype(bool), z["relabelled"].astype(bool)
    n = len(flipped)
    assert (meta["row"].to_numpy() == np.arange(n)).all(), "brain_meta rows are not in matrix order"
    old, new = strings(meta["transmitter"]), np.array([str(x) for x in z["transmitter"]])
    inh = np.isin(old, list(CHLORIDE_TRANSMITTERS))
    pre = np.repeat(np.arange(n), np.diff(z["ptr"]))
    w = np.abs(z["syn"].astype(np.float64))  # synapse counts; the sign is the presynaptic neuron's
    post = z["post"]
    new_inh = inh ^ flipped
    out = {
        "variant": variant, "neurons": int(n), "relabelled": int(relabelled.sum()), "sign_flipped": int(flipped.sum()),
        "inhibitory_to_excitatory": int((flipped & inh).sum()), "excitatory_to_inhibitory": int((flipped & ~inh).sum()),
        "synapses": float(w.sum()), "synapses_from_flipped_frac": float(w[flipped[pre]].sum() / w.sum()),
        "inhibitory_synapse_frac_before": float(w[inh[pre]].sum() / w.sum()),
        "inhibitory_synapse_frac_after": float(w[new_inh[pre]].sum() / w.sum()),
    }
    # the driven sensory neurons (the populations runs/ride.py drives with --lane hs)
    senses, rows_all = {}, []
    for name, rows in sensory_populations(meta, goal="none", lane="hs").items():
        rows = np.asarray(rows, dtype=np.int64)
        rows_all.append(rows)
        senses[name] = {"neurons": int(len(rows)), "sign_flipped": int(flipped[rows].sum())}
    rows_all = np.unique(np.concatenate(rows_all))
    out["senses"] = senses
    out["sense_neurons"], out["sense_sign_flipped"] = int(len(rows_all)), int(flipped[rows_all].sum())
    # the hand-picked readout: its neurons' own signs do not change what the decoder reads (it reads their
    # spikes), only what they send back into the brain; the share of their input that changed sign does
    ty, side = strings(meta["type"]), strings(meta["somaSide"])
    types = [t for t in READOUTS["lane"] if (ty == t).any()]
    ro = np.isin(ty, types) & np.isin(side, ["L", "R"])
    out["readout_types"], out["readout_neurons"] = len(types), int(ro.sum())
    out["readout_sign_flipped"] = int((ro & flipped).sum())
    out["readout_sign_flipped_neurons"] = [f"{ty[i]}_{side[i]}: {old[i]} -> {new[i]}" for i in np.flatnonzero(ro & flipped)]
    into_ro = ro[post]
    out["readout_input_synapses_from_flipped_frac"] = float(w[into_ro & flipped[pre]].sum() / w[into_ro].sum())
    into_sense = np.zeros(n, bool)
    into_sense[rows_all] = True
    into_sense = into_sense[post]
    out["sense_input_synapses_from_flipped_frac"] = float(w[into_sense & flipped[pre]].sum() / max(w[into_sense].sum(), 1.0))
    print(json.dumps(out, indent=1))
    if out_path:
        json.dump(out, open(out_path, "w"), indent=1)


if __name__ == "__main__":
    main()

"""CPU vs GPU benchmark of the whole-CNS simulator: sugar GRNs at 150 Hz (Shiu), 1 s, growing trial batches.

usage: python -m runs.bench_gpu --devices cpu cuda --trials 1 8 32 128
"""
import argparse
import json
from pathlib import Path

import numpy as np
import torch

from brain import stimuli
from brain.connectome import Brain
from brain.engine import W_SYN, experiment
from brain.graph_engine import graph_experiment

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--devices", nargs="+", default=["cpu", "cuda"])
    ap.add_argument("--trials", nargs="+", type=int, default=[1, 8, 32, 128])
    ap.add_argument("--ms", type=float, default=1000.0)
    ap.add_argument("--out", default="results/bench_gpu.json")
    ap.add_argument("--graph", action="store_true", help="use the CUDA-Graph simulator")
    ap.add_argument("--steps-per-graph", type=int, default=None)
    args = ap.parse_args()
    brain = Brain()
    mn9, sugar = stimuli.mn9(), stimuli.group("sugar")
    hz = np.full(len(sugar), stimuli.SHIU_HZ, np.float32)
    print(f"torch {torch.__version__}  cpu threads {torch.get_num_threads()}  "
          f"gpu {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none'}", flush=True)
    rows = []
    for dev in args.devices:
        if dev == "cuda" and not torch.cuda.is_available():
            print("cuda not available, skipping"); continue
        run = (lambda **k: graph_experiment(brain, sugar, hz, steps_per_graph=args.steps_per_graph, **k)) if args.graph \
            else (lambda **k: experiment(brain, sugar, hz, **k))
        run(record_neurons=mn9, flies=1, ms=100.0, bin_ms=50.0, params={"w_syn": W_SYN}, device=dev)  # warm-up
        for n in args.trials:
            if dev == "cpu" and n > 32:
                continue
            if dev == "cuda":
                torch.cuda.reset_peak_memory_stats()
            r = run(record_neurons=mn9, flies=n, ms=args.ms, bin_ms=50.0, params={"w_syn": W_SYN}, device=dev)
            mn9_hz = r["binned"][:, 0].sum(1) / (args.ms / 1000.0)
            mem = torch.cuda.max_memory_allocated() / 1e9 if dev == "cuda" else float("nan")
            row = {"device": dev + ("+graph" if args.graph else ""), "trials": n, "seconds": round(r["wall_s"], 2),
                   "s_per_trial_s": round(r["wall_s"] / n / (args.ms / 1000.0), 3),
                   "mn9_hz": round(float(mn9_hz.mean()), 1), "spikes_per_s": round(float(r["mean_hz"].sum())),
                   "gpu_gb": round(mem, 2)}
            rows.append(row)
            print(f"{row['device']:10s} trials {n:4d}  {row['seconds']:8.1f} s  {row['s_per_trial_s']:7.2f} s per simulated second  "
                  f"MN9 {row['mn9_hz']:5.1f} Hz  gpu {row['gpu_gb']} GB", flush=True)
            (ROOT / args.out).write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()

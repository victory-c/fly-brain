"""Rewired versions of the connectome, for the Scrambled Brains wiring ladder (docs/GLOSSARY.md section 7).

    python -m brain.variants r4 --seed 1      # -> results/variants/r4_s1.npz (same neurons, rewired)
    python -m brain.variants r5 --seed 1

Every rung keeps the neurons, their rows and each connection's signed synapse count. The sign belongs to the
presynaptic neuron's transmitter (brain/connectome.py), and each connection stays in its presynaptic row, so every
neuron keeps its transmitter, its out-degree and its total output synapses. Degrees are kept up to merged
duplicates (below; 0.34% of connections in r4, 0.13% in r5). The rungs differ in where the connections go:

- r4, degree-preserving: the targets of all connections are shuffled together, so every neuron also keeps its
  in-degree (number of incoming connections), but who connects to whom is random. Not kept: how many synapses a
  neuron receives and its excitatory/inhibitory input mix, because synapse counts and signs stay with the sender.
  In the male CNS this breaks the convergence of sensory input: neurons that receive 200 or more synapses from
  the bike's 789 driven sensory neurons go from 417 to 26.
- r5, random: every connection gets a target drawn uniformly from all neurons, so in-degrees are random too.

A shuffle can make two connections from one neuron hit the same target; they are merged into one connection with
the summed synapse count (the engine would add them anyway). The result loads with Brain(path), shares
brain_meta.parquet and the atlas, and is passed to runs.ride / runs.probe with --brain.
"""
import argparse
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RUNGS = ("r4", "r5")


def rewire(ptr, post, syn, rung, seed):
    """(ptr, post, syn) of the rewired CSR matrix; rows (presynaptic neurons) and per-row syn are kept."""
    rng = np.random.default_rng(seed)
    n = len(ptr) - 1
    pre = np.repeat(np.arange(n, dtype=np.int64), np.diff(ptr))
    if rung == "r4":
        new_post = post[rng.permutation(len(post))]
    elif rung == "r5":
        new_post = rng.integers(0, n, size=len(post), dtype=np.int64)
    else:
        raise ValueError(f"unknown rung {rung!r}, expected one of {RUNGS}")
    key = pre * n + new_post
    order = np.argsort(key, kind="stable")
    key, w = key[order], syn[order].astype(np.float64)
    uniq, first = np.unique(key, return_index=True)
    w = np.add.reduceat(w, first)
    out_pre, out_post = uniq // n, uniq % n
    out_ptr = np.zeros(n + 1, dtype=np.int64)
    np.add.at(out_ptr, out_pre + 1, 1)
    return np.cumsum(out_ptr), out_post.astype(post.dtype), w.astype(syn.dtype)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rung", choices=RUNGS)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--brain", default=str(ROOT / "brain.npz"))
    ap.add_argument("--out", default=None, help="default results/variants/<rung>_s<seed>.npz")
    a = ap.parse_args()
    with np.load(a.brain, allow_pickle=False) as stored:
        arrays = {k: stored[k] for k in stored.files}
    ptr, post, syn = arrays["ptr"], arrays["post"], arrays["syn"]
    new_ptr, new_post, new_syn = rewire(ptr, post, syn, a.rung, a.seed)
    out = Path(a.out or ROOT / "results" / "variants" / f"{a.rung}_s{a.seed}.npz")
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, **dict(arrays, ptr=new_ptr, post=new_post, syn=new_syn))
    n = len(ptr) - 1
    kept = np.isin(np.repeat(np.arange(n), np.diff(ptr)) * n + post,
                   np.repeat(np.arange(n), np.diff(new_ptr)) * n + new_post).mean()
    print(f"{a.rung} seed {a.seed}: {len(post):,} connections -> {len(new_post):,} after merging; "
          f"synapses {np.abs(syn).sum():,.0f} -> {np.abs(new_syn).sum():,.0f}; "
          f"{kept:.2%} of the original connections survive; written {out}")


if __name__ == "__main__":
    main()

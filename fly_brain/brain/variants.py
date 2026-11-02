"""Perturbed versions of the connectome: the Scrambled Brains wiring ladder (docs/GLOSSARY.md section 7).

    python -m brain.variants r1 --seed 1      # -> results/variants/r1_s1.npz   transmitter errors
    python -m brain.variants r2 --seed 1      #    synapse-count jitter
    python -m brain.variants r3 --seed 1      #    type-preserving shuffle
    python -m brain.variants r35 --seed 1     #    strength-preserving shuffle (R3.5)
    python -m brain.variants r4 --seed 1      #    degree-preserving shuffle
    python -m brain.variants r5 --seed 1      #    random wiring

Every rung keeps the neurons and their rows, and every connection stays in its presynaptic row, so every neuron
keeps its out-degree. The sign of a connection belongs to the presynaptic neuron's transmitter
(brain/connectome.py). Which else is kept, from most to least detailed:

- r1, transmitter errors: the wiring is untouched. A fraction of neurons (default 6%, Eckstein et al. 2024: 94%
  of FlyWire neurons get the right transmitter by majority vote) is given another transmitter, drawn in
  proportion to how common the other transmitters are. Only neurons whose new transmitter changes their class
  (chloride: GABA, glutamate, histamine; everything else excitatory) change the sign of their outputs, so the
  GABA-glutamate confusion that Eckstein reports as the most common one does nothing here. `--rates` takes a
  JSON of per-transmitter error rates, for the measured confusion rates once Track B has extracted them.
- r2, synapse-count jitter: every connection's count is multiplied by an independent lognormal factor with
  median 1 and sigma = ln(1.25), so one standard deviation is a factor 1.25 either way (flybench's
  "jittered +/-25% (lognormal)" wiring-robustness task). Counts stay fractional; the engine multiplies them by
  w_syn anyway. Targets, signs and in/out-degrees are unchanged.
- r3, type-preserving shuffle: each connection's target is replaced by a random neuron of the same cell type on
  the same side (brain_meta.parquet `type` and `side`; neurons without a type are their own group and keep
  their inputs). The synapse matrix between (type, side) groups is kept exactly, and so is every neuron's
  out-degree and output. A neuron's own inputs are kept only when its group has one member, which is the case
  for most descending neurons and not for Kenyon cells.
- r35 (R3.5), strength-preserving shuffle: targets are permuted among connections with the same sign and the
  same synapse count, so every neuron keeps its in-degree, its incoming synapse total and its excitatory /
  inhibitory input mix exactly, as well as everything the sender keeps. Who connects to whom is otherwise
  random. Connections whose (sign, count) is unique cannot move; the generator prints how many could.
- r4, degree-preserving: the targets of all connections are shuffled together, so every neuron also keeps its
  in-degree (number of incoming connections), but who connects to whom is random. Not kept: how many synapses a
  neuron receives and its excitatory/inhibitory input mix, because synapse counts and signs stay with the sender.
  In the male CNS this breaks the convergence of sensory input: neurons that receive 200 or more synapses from
  the bike's 789 driven sensory neurons go from 417 to 26.
- r5, random: every connection gets a target drawn uniformly from all neurons, so in-degrees are random too.

A shuffle can make two connections from one neuron hit the same target; they are merged into one connection with
the summed synapse count (the engine would add them anyway; 0.34% of connections in r4, 0.13% in r5). The result
loads with Brain(path), shares brain_meta.parquet and the atlas, and is passed to runs.ride / runs.probe /
runs.pretest with --brain. r1 also stores which neurons were relabelled (`relabelled`) and which changed sign
(`sign_flipped`); r2 stores the jitter factors (`jitter`).
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RUNGS = ("r1", "r2", "r3", "r35", "r4", "r5")
NEEDS_META = ("r1", "r3")
CHLORIDE_TRANSMITTERS = {"gaba", "glutamate", "histamine"}  # as brain/connectome.py
DEFAULTS = {"rate": 0.06, "jitter": 0.25}


def _merge(pre, new_post, syn, n, post_dtype, syn_dtype):
    """CSR (ptr, post, syn) from edge lists, targets sorted per row, duplicate (pre, post) pairs summed."""
    key = pre * n + new_post
    order = np.argsort(key, kind="stable")
    key, w = key[order], syn[order].astype(np.float64)
    uniq, first = np.unique(key, return_index=True)
    w = np.add.reduceat(w, first)
    out_pre, out_post = uniq // n, uniq % n
    out_ptr = np.zeros(n + 1, dtype=np.int64)
    np.add.at(out_ptr, out_pre + 1, 1)
    return np.cumsum(out_ptr), out_post.astype(post_dtype), w.astype(syn_dtype)


def _groups(meta):
    """One integer per neuron: its (type, side) group; neurons without a type are groups of their own.
    Side is somaSide, else rootSide (the side the root enters), else blank, as Brain.meta's `side`."""
    side = pd.Series("", index=meta.index, dtype=object)
    for col in ("rootSide", "somaSide"):
        if col in meta:
            side = meta[col].where(meta[col].notna(), side)
    key = meta["type"].astype(str) + "|" + side.astype(str)
    key = key.where(meta["type"].notna(), "body:" + meta["bodyId"].astype(str))
    return pd.factorize(key)[0].astype(np.int64)


def relabel_transmitters(transmitter, rng, rate=DEFAULTS["rate"], rates=None):
    """New transmitter per neuron: with probability rate (or rates[transmitter]), another transmitter drawn in
    proportion to its frequency among the brain's neurons. Returns (new_transmitter, relabelled mask)."""
    tr = np.asarray(transmitter).astype(str)
    labels, counts = np.unique(tr, return_counts=True)
    per_neuron_rate = np.full(len(tr), rate, dtype=np.float64)
    if rates:
        for label, r in rates.items():
            per_neuron_rate[tr == label] = r
    relabelled = rng.random(len(tr)) < per_neuron_rate
    new = tr.copy()
    for label, _ in zip(labels, counts):
        rows = np.flatnonzero(relabelled & (tr == label))
        if len(rows) == 0:
            continue
        others = labels != label
        p = counts[others] / counts[others].sum()
        new[rows] = rng.choice(labels[others], size=len(rows), p=p)
    return new, relabelled


def rewire(ptr, post, syn, rung, seed, meta=None, **opts):
    """(ptr, post, syn[, extras]) of the perturbed CSR matrix. Rows (presynaptic neurons) are kept. `meta` is the
    brain_meta DataFrame (needed for r1 and r3). Returns a dict of extra arrays as a fourth value."""
    rng = np.random.default_rng(seed)
    n = len(ptr) - 1
    pre = np.repeat(np.arange(n, dtype=np.int64), np.diff(ptr))
    extras = {}
    if rung in NEEDS_META and meta is None:
        raise ValueError(f"rung {rung!r} needs brain_meta (transmitter, type, side)")
    if rung == "r1":
        new_tr, relabelled = relabel_transmitters(meta["transmitter"].to_numpy(), rng,
                                                 rate=opts.get("rate", DEFAULTS["rate"]), rates=opts.get("rates"))
        old_inh = np.isin(meta["transmitter"].to_numpy().astype(str), list(CHLORIDE_TRANSMITTERS))
        new_inh = np.isin(new_tr, list(CHLORIDE_TRANSMITTERS))
        flipped = old_inh != new_inh
        new_syn = np.where(flipped[pre], -syn, syn).astype(syn.dtype)
        extras = {"relabelled": relabelled, "sign_flipped": flipped, "transmitter": new_tr}
        return ptr.copy(), post.copy(), new_syn, extras
    if rung == "r2":
        sigma = np.log1p(opts.get("jitter", DEFAULTS["jitter"]))
        factor = rng.lognormal(0.0, sigma, size=len(syn))
        extras = {"jitter": factor.astype(np.float32)}
        return ptr.copy(), post.copy(), (syn * factor).astype(syn.dtype), extras
    if rung == "r3":
        g = _groups(meta)
        order = np.argsort(g, kind="stable")
        gstart = np.searchsorted(g[order], np.arange(g.max() + 1))
        gsize = np.bincount(g, minlength=g.max() + 1)
        gp = g[post]
        new_post = order[gstart[gp] + (rng.random(len(post)) * gsize[gp]).astype(np.int64)]
    elif rung == "r35":
        strata = np.unique(syn, return_inverse=True)[1]           # same sign and same count
        by_stratum = np.lexsort((np.arange(len(syn)), strata))
        shuffled = np.lexsort((rng.random(len(syn)), strata))
        new_post = np.empty_like(post)
        new_post[by_stratum] = post[shuffled]
    elif rung == "r4":
        new_post = post[rng.permutation(len(post))]
    elif rung == "r5":
        new_post = rng.integers(0, n, size=len(post), dtype=np.int64)
    else:
        raise ValueError(f"unknown rung {rung!r}, expected one of {RUNGS}")
    new_ptr, new_post, new_syn = _merge(pre, new_post.astype(np.int64), syn, n, post.dtype, syn.dtype)
    return new_ptr, new_post, new_syn, extras


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("rung", choices=RUNGS)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--brain", default=str(ROOT / "brain.npz"))
    ap.add_argument("--meta", default=str(ROOT / "brain_meta.parquet"), help="per-neuron table (r1, r3)")
    ap.add_argument("--out", default=None, help="default results/variants/<rung>_s<seed>.npz")
    ap.add_argument("--rate", type=float, default=DEFAULTS["rate"], help="r1: fraction of neurons relabelled")
    ap.add_argument("--rates", default=None, help='r1: JSON file {"gaba": 0.04, ...} of per-transmitter error rates')
    ap.add_argument("--jitter", type=float, default=DEFAULTS["jitter"], help="r2: one-sigma factor minus one")
    a = ap.parse_args()
    with np.load(a.brain, allow_pickle=False) as stored:
        arrays = {k: stored[k] for k in stored.files}
    ptr, post, syn = arrays["ptr"], arrays["post"], arrays["syn"]
    meta = None
    if a.rung in NEEDS_META:
        meta = pd.read_parquet(a.meta)
        if len(meta) != len(ptr) - 1:
            raise SystemExit(f"{a.meta} has {len(meta):,} rows, the brain has {len(ptr) - 1:,} neurons")
    rates = json.loads(Path(a.rates).read_text()) if a.rates else None
    new_ptr, new_post, new_syn, extras = rewire(ptr, post, syn, a.rung, a.seed, meta,
                                                rate=a.rate, rates=rates, jitter=a.jitter)
    out = Path(a.out or ROOT / "results" / "variants" / f"{a.rung}_s{a.seed}.npz")
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, **dict(arrays, ptr=new_ptr, post=new_post, syn=new_syn), **extras)
    n = len(ptr) - 1
    old_key = np.repeat(np.arange(n), np.diff(ptr)) * n + post
    new_key = np.repeat(np.arange(n), np.diff(new_ptr)) * n + new_post
    kept = np.isin(old_key, new_key).mean()
    print(f"{a.rung} seed {a.seed}: {len(post):,} connections -> {len(new_post):,} after merging; "
          f"synapses {np.abs(syn).sum():,.0f} -> {np.abs(new_syn).sum():,.0f}; "
          f"{kept:.2%} of the original connections survive; written {out}")
    if a.rung == "r1":
        print(f"  {extras['relabelled'].sum():,} neurons relabelled ({extras['relabelled'].mean():.2%}), "
              f"{extras['sign_flipped'].sum():,} changed sign ({extras['sign_flipped'].mean():.2%}); "
              f"{np.abs(new_syn[new_syn < 0]).sum() / np.abs(new_syn).sum():.1%} of synapses now inhibitory "
              f"(was {np.abs(syn[syn < 0]).sum() / np.abs(syn).sum():.1%})")
    if a.rung == "r2":
        f = extras["jitter"]
        print(f"  jitter factors: median {np.median(f):.3f}, 16-84% {np.percentile(f, 16):.3f}-{np.percentile(f, 84):.3f}")
    if a.rung == "r3":
        g = _groups(meta)
        sizes = np.bincount(g)
        print(f"  {len(sizes):,} (type, side) groups, {int((sizes == 1).sum()):,} with one neuron "
              f"({(sizes[g] == 1).mean():.1%} of neurons keep their inputs)")
    if a.rung == "r35":
        _, inv, cnt = np.unique(syn, return_inverse=True, return_counts=True)
        print(f"  {len(cnt):,} (sign, count) strata; {(cnt[inv] > 1).mean():.1%} of connections could move")


if __name__ == "__main__":
    main()

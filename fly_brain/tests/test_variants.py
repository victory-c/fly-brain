"""brain/variants.py: what each rung of the wiring ladder keeps."""
import numpy as np
import pandas as pd
import pytest

from brain.variants import CHLORIDE_TRANSMITTERS, RUNGS, relabel_transmitters, rewire

TRANSMITTERS = ["acetylcholine", "gaba", "glutamate", "acetylcholine", "acetylcholine", "histamine", "serotonin"]


def toy(n=200, edges=3000, seed=0):
    """A small brain: CSR arrays plus a brain_meta-like table (type, somaSide, transmitter)."""
    rng = np.random.default_rng(seed)
    pre, post = rng.integers(0, n - 3, edges), rng.integers(0, n, edges)  # the last 3 neurons send nothing
    key = np.unique(pre * n + post)
    pre, post = key // n, key % n
    transmitter = rng.choice(TRANSMITTERS, n)
    sign = np.where(np.isin(transmitter, list(CHLORIDE_TRANSMITTERS)), -1.0, 1.0)  # one sign per sender
    syn = (rng.integers(1, 20, len(pre)) * sign[pre]).astype(np.float32)
    ptr = np.zeros(n + 1, dtype=np.int64)
    np.add.at(ptr, pre + 1, 1)
    types = np.array([f"T{i}" for i in rng.integers(0, 40, n)], dtype=object)
    types[:10] = [f"U{i}" for i in range(10)]          # 10 types with one neuron each (like most DNs)
    types[10:15] = None                                 # neurons without a type
    meta = pd.DataFrame({"row": np.arange(n), "bodyId": np.arange(n) + 1000, "type": types,
                         "somaSide": rng.choice(["L", "R", None], n), "rootSide": rng.choice(["L", "R"], n),
                         "transmitter": transmitter})
    return np.cumsum(ptr), post.astype(np.int64), syn, sign, meta


def row_totals(ptr, syn):
    return np.bincount(np.repeat(np.arange(len(ptr) - 1), np.diff(ptr)), np.abs(syn), minlength=len(ptr) - 1)


def col_totals(post, syn, n, positive=None):
    w = np.abs(syn)
    if positive is not None:
        w = np.where((syn > 0) == positive, w, 0.0)
    return np.bincount(post, w, minlength=n)


def senders(ptr):
    return np.repeat(np.arange(len(ptr) - 1), np.diff(ptr))


@pytest.mark.parametrize("rung", RUNGS)
def test_every_rung_keeps_rows_out_degree_and_sorted_targets(rung):
    ptr, post, syn, sign, meta = toy()
    n = len(ptr) - 1
    p2, q2, s2, _ = rewire(ptr, post, syn, rung, seed=1, meta=meta)
    assert len(p2) == len(ptr) and p2[-1] == len(q2) == len(s2)
    pre2 = senders(p2)
    assert np.all(np.diff(q2)[np.diff(pre2) == 0] > 0)                           # sorted, no duplicate pairs
    if rung in ("r1", "r2"):
        assert np.array_equal(q2, post) and np.array_equal(p2, ptr)             # wiring untouched
    else:
        assert np.all(np.sign(s2) == sign[pre2])                                 # signs stay with the sender
        assert np.allclose(row_totals(ptr, syn), row_totals(p2, s2))             # output synapses per neuron
        lost = np.diff(ptr) - np.diff(p2)                                        # out-degree, up to merged duplicates
        assert lost.min() >= 0 and lost.sum() == len(post) - len(q2)
        assert np.isclose(np.abs(syn).sum(), np.abs(s2).sum())


def test_r1_flips_whole_rows_and_only_where_the_class_changes():
    ptr, post, syn, sign, meta = toy()
    p2, q2, s2, x = rewire(ptr, post, syn, "r1", seed=3, meta=meta, rate=0.2)
    pre = senders(ptr)
    assert np.allclose(np.abs(s2), np.abs(syn))
    flipped_rows = np.sign(s2) != np.sign(syn)
    assert np.array_equal(flipped_rows, x["sign_flipped"][pre])
    new_inh = np.isin(x["transmitter"], list(CHLORIDE_TRANSMITTERS))
    assert np.array_equal(x["sign_flipped"], new_inh != (sign < 0))
    assert x["relabelled"].sum() >= x["sign_flipped"].sum() > 0
    assert np.all(x["transmitter"][x["relabelled"]] != meta["transmitter"].to_numpy()[x["relabelled"]])
    assert np.all(x["transmitter"][~x["relabelled"]] == meta["transmitter"].to_numpy()[~x["relabelled"]])


def test_r1_rates_per_transmitter():
    rng = np.random.default_rng(0)
    tr = np.array(["gaba"] * 5000 + ["acetylcholine"] * 5000)
    new, relabelled = relabel_transmitters(tr, rng, rate=0.5, rates={"gaba": 0.0})
    assert relabelled[:5000].sum() == 0 and abs(relabelled[5000:].mean() - 0.5) < 0.05
    assert set(new[5000:][relabelled[5000:]]) == {"gaba"}                        # the only other label


def test_r2_jitter_is_lognormal_around_one():
    ptr, post, syn, sign, meta = toy(edges=20000)
    p2, q2, s2, x = rewire(ptr, post, syn, "r2", seed=1, jitter=0.25)
    f = x["jitter"]
    assert np.allclose(s2, syn * f, rtol=1e-5)
    assert np.all(np.sign(s2) == np.sign(syn))
    assert abs(np.median(np.log(f))) < 0.02 and abs(np.std(np.log(f)) - np.log(1.25)) < 0.01


def test_r3_keeps_type_matrix_and_singleton_inputs():
    ptr, post, syn, sign, meta = toy()
    n = len(ptr) - 1
    p2, q2, s2, _ = rewire(ptr, post, syn, "r3", seed=1, meta=meta)
    from brain.variants import _groups
    g = _groups(meta)
    pre, pre2 = senders(ptr), senders(p2)
    G = g.max() + 1

    def type_matrix(pre_, post_, syn_):
        m = np.zeros((G, G))
        np.add.at(m, (g[pre_], g[post_]), np.abs(syn_))
        return m

    assert np.allclose(type_matrix(pre, post, syn), type_matrix(pre2, q2, s2))
    single = np.bincount(g, minlength=G)[g] == 1
    assert single.sum() >= 15                                                    # the U types and untyped neurons
    assert np.allclose(col_totals(post, syn, n)[single], col_totals(q2, s2, n)[single])
    assert not np.array_equal(q2, post)


def test_r3_targets_stay_in_their_type_and_side_group():
    ptr, post, syn, sign, meta = toy()
    from brain.variants import _groups
    g = _groups(meta)
    # replay the draw: the k-th connection's new target must share the k-th old target's group
    rng = np.random.default_rng(1)
    order = np.argsort(g, kind="stable")
    gstart = np.searchsorted(g[order], np.arange(g.max() + 1))
    gsize = np.bincount(g, minlength=g.max() + 1)
    new_post = order[gstart[g[post]] + (rng.random(len(post)) * gsize[g[post]]).astype(np.int64)]
    assert np.all(g[new_post] == g[post])
    # and the generator agrees with the replay once duplicates are merged
    p2, q2, s2, _ = rewire(ptr, post, syn, "r3", seed=1, meta=meta)
    n = len(ptr) - 1
    assert set((senders(p2) * n + q2).tolist()) == set((senders(ptr) * n + new_post).tolist())


def test_r35_keeps_in_degree_in_strength_and_input_sign_mix():
    ptr, post, syn, sign, meta = toy(edges=6000)
    n = len(ptr) - 1
    p2, q2, s2, _ = rewire(ptr, post, syn, "r35", seed=1, meta=meta)
    assert np.allclose(col_totals(post, syn, n, positive=True), col_totals(q2, s2, n, positive=True))
    assert np.allclose(col_totals(post, syn, n, positive=False), col_totals(q2, s2, n, positive=False))
    lost = np.bincount(post, minlength=n) - np.bincount(q2, minlength=n)        # in-degree, up to merged duplicates
    assert lost.min() >= 0 and lost.sum() == len(post) - len(q2)
    assert not np.array_equal(q2, post)


def test_r4_keeps_in_degree():
    ptr, post, syn, sign, meta = toy()
    n = len(ptr) - 1
    p2, q2, s2, _ = rewire(ptr, post, syn, "r4", seed=1)
    lost = np.bincount(post, minlength=n) - np.bincount(q2, minlength=n)
    assert lost.min() >= 0 and lost.sum() == len(post) - len(q2)
    assert not np.array_equal(q2, post)


def test_meta_rungs_need_meta():
    ptr, post, syn, sign, meta = toy()
    with pytest.raises(ValueError):
        rewire(ptr, post, syn, "r3", seed=1)


def test_npz_round_trip(tmp_path):
    from brain.connectome import Brain
    from brain.variants import main
    import sys
    ptr, post, syn, _, meta = toy()
    src, meta_path = tmp_path / "toy.npz", tmp_path / "meta.parquet"
    np.savez(src, body_ids=meta["bodyId"].to_numpy(), ptr=ptr, post=post.astype(np.int32), syn=syn)
    meta.to_parquet(meta_path)
    for rung in RUNGS:
        out = tmp_path / f"{rung}.npz"
        argv, sys.argv = sys.argv, ["variants", rung, "--seed", "2", "--brain", str(src), "--meta", str(meta_path),
                                    "--out", str(out)]
        try:
            main()
        finally:
            sys.argv = argv
        b, r = Brain(src), Brain(out)
        assert r.n == b.n and np.array_equal(r.body_ids, b.body_ids)
        assert r.ptr[-1] == r.n_edges
        if rung != "r2":
            assert np.isclose(r.syn.abs().sum(), b.syn.abs().sum())

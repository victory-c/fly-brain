"""brain/variants.py: what each rewired rung keeps."""
import numpy as np

from brain.variants import rewire


def toy(n=200, edges=3000, seed=0):
    rng = np.random.default_rng(seed)
    pre, post = rng.integers(0, n - 3, edges), rng.integers(0, n, edges)  # the last 3 neurons send nothing
    key = np.unique(pre * n + post)
    pre, post = key // n, key % n
    sign = np.where(rng.random(n) < 0.4, -1.0, 1.0)  # one transmitter sign per presynaptic neuron
    syn = (rng.integers(1, 20, len(pre)) * sign[pre]).astype(np.float32)
    ptr = np.zeros(n + 1, dtype=np.int64)
    np.add.at(ptr, pre + 1, 1)
    return np.cumsum(ptr), post.astype(np.int64), syn, sign


def row_totals(ptr, syn):
    return np.bincount(np.repeat(np.arange(len(ptr) - 1), np.diff(ptr)), np.abs(syn), minlength=len(ptr) - 1)


def test_r4_keeps_degrees_signs_and_synapses():
    ptr, post, syn, sign = toy()
    n = len(ptr) - 1
    p2, q2, s2 = rewire(ptr, post, syn, "r4", seed=1)
    pre2 = np.repeat(np.arange(n), np.diff(p2))
    assert np.all(np.sign(s2) == sign[pre2])                                   # signs stay with the sender
    assert np.allclose(row_totals(ptr, syn), row_totals(p2, s2))                 # output synapses per neuron
    lost = np.bincount(post, minlength=n) - np.bincount(q2, minlength=n)        # in-degree, up to merged duplicates
    assert lost.min() >= 0 and lost.sum() == len(post) - len(q2)
    assert np.all(np.diff(q2)[np.diff(pre2) == 0] > 0)                         # targets sorted, no duplicates per row
    assert not np.array_equal(q2, post)


def test_r5_keeps_rows_and_totals():
    ptr, post, syn, sign = toy()
    n = len(ptr) - 1
    p2, q2, s2 = rewire(ptr, post, syn, "r5", seed=1)
    pre2 = np.repeat(np.arange(n), np.diff(p2))
    assert np.all(np.sign(s2) == sign[pre2])
    assert np.isclose(np.abs(syn).sum(), np.abs(s2).sum())
    assert np.allclose(row_totals(ptr, syn), row_totals(p2, s2))


def test_npz_round_trip(tmp_path):
    from brain.connectome import Brain
    from brain.variants import main
    import sys
    ptr, post, syn, _ = toy()
    src = tmp_path / "toy.npz"
    np.savez(src, body_ids=np.arange(len(ptr) - 1, dtype=np.int64) + 1000, ptr=ptr, post=post.astype(np.int32), syn=syn)
    out = tmp_path / "r4.npz"
    argv, sys.argv = sys.argv, ["variants", "r4", "--seed", "2", "--brain", str(src), "--out", str(out)]
    try:
        main()
    finally:
        sys.argv = argv
    b, r = Brain(src), Brain(out)
    assert r.n == b.n and np.array_equal(r.body_ids, b.body_ids)
    assert r.ptr[-1] == r.n_edges and np.isclose(r.syn.abs().sum(), b.syn.abs().sum())

"""runs/pretest.py: the balanced-relabelling null and the z-score."""
import math

import numpy as np

from runs.pretest import balanced_splits, zscores


def _balanced(m, B):
    h = B // 2
    return bool(m[0]) and m.sum() == 2 * (h // 2) and m[:h].sum() == h // 2


def test_small_B_enumerates_every_balanced_split_once():
    s = balanced_splits(8)
    assert len(s) == 18 == math.comb(3, 1) * math.comb(4, 2)
    assert all(_balanced(m, 8) for m in s)
    assert len({tuple(m) for m in s}) == 18
    assert len(balanced_splits(8, max_splits=1000)) == 18  # the cap only bites when more exist


def test_large_B_samples_distinct_balanced_splits_reproducibly():
    s = balanced_splits(30, max_splits=1000, seed=1)
    assert len(s) == 1000
    assert all(_balanced(m, 30) for m in s)
    assert len({tuple(m) for m in s}) == 1000
    again = balanced_splits(30, max_splits=1000, seed=1)
    assert all((a == b).all() for a, b in zip(s, again))
    other = balanced_splits(30, max_splits=1000, seed=2)
    assert not all((a == b).all() for a, b in zip(s, other))


def test_zscore_sees_a_shift_and_a_balanced_split_does_not():
    rng = np.random.default_rng(0)
    B, N = 8, 50
    hz = rng.poisson(20, (B, N)).astype(float)
    hz[: B // 2, 0] += 40  # neuron 0 fires more in the left-probed brains
    left = np.arange(B) < B // 2
    z = zscores(hz, left, 1000.0)
    assert abs(z[0]) > 3
    assert (np.abs(z[1:]) > 3).sum() <= 2
    null = np.array([np.abs(zscores(hz, m, 1000.0))[0] for m in balanced_splits(B)])
    assert null.max() < abs(z[0])

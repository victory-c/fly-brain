"""Brain.meta, Brain.positions and Brain.select (brain/select.py) on the synthetic brain; CPU, no connectome needed.

    python -m pytest tests/test_select.py
"""
import numpy as np
import pytest

from brain.connectome import Brain
from brain.engine import W_SYN, Engine
from tests.synthetic_brain import write

SUGAR = ["LB3b", "LB3c", "LB3d", "LB4b"]


@pytest.fixture
def brain(tmp_path):
    p = write(tmp_path)
    return Brain(p["npz"], meta=p["meta"], atlas=p["atlas"])


def names(brain, rows, column="instance"):
    return sorted(brain.meta.loc[rows, column])


def test_filters_combine_and_return_sorted_rows(brain):
    mn9 = brain.select(instance=["MN9_L", "MN9_R"])
    assert mn9.dtype == np.int64 and list(mn9) == sorted(mn9)
    assert names(brain, mn9) == ["MN9_L", "MN9_R"]
    left = brain.select(type=SUGAR, side="L")
    assert len(left) == 12 and set(brain.meta.loc[left, "type"]) == set(SUGAR)
    assert (brain.meta.loc[left, "rootSide"] == "L").all()  # GRNs have no somaSide: side falls back to rootSide
    dns = brain.select(superclass="descending_neuron", side="R")
    assert names(brain, dns) == ["DNg46_R", "DNp20_R", "DNp22_R"]
    assert len(brain.select(type=SUGAR, superclass="descending_neuron")) == 0  # valid values, nothing in common


def test_wildcards_class_transmitter_and_region(brain):
    assert names(brain, brain.select(type="DNp*", side="L")) == ["DNp20_L", "DNp22_L"]
    assert names(brain, brain.select(type="LB3?", side="R"), "type") == ["LB3a"] * 3 + ["LB3b"] * 3 + ["LB3c"] * 3 + ["LB3d"] * 3
    assert len(brain.select(class_="gustatory")) == 7 * 2 * 3
    gaba = brain.select(transmitter="gaba")
    assert brain.meta.loc[gaba, "inhibitory"].all()
    assert np.array_equal(brain.select(region="descending"), brain.select(superclass="descending_neuron"))


def test_typos_and_unknown_filters_fail_loudly(brain):
    with pytest.raises(KeyError, match="MN9_L"):
        brain.select(instance="MN9-L")
    with pytest.raises(KeyError, match="no neuron has type='DNx\\*'"):
        brain.select(type="DNx*")
    with pytest.raises(TypeError, match="takes names"):
        brain.select(type=5)
    from brain.select import select
    with pytest.raises(TypeError, match="no filter 'colour'"):
        select(brain, colour="red")


def test_near_by_instance_row_and_point(brain):
    xyz = brain.positions
    assert xyz.shape == (brain.n, 3) and np.isnan(xyz).any(axis=1).sum() > 0
    mn9 = int(brain.select(instance="MN9_L")[0])
    within = brain.select(near=("MN9_L", 150.0))
    distance = np.linalg.norm(xyz - xyz[mn9], axis=1)
    assert np.array_equal(within, np.flatnonzero(distance <= 150.0))
    assert mn9 in within and np.isfinite(xyz[within]).all()      # neurons without a position are never selected
    assert np.array_equal(brain.select(near=(mn9, 150.0)), within)
    assert np.array_equal(brain.select(near=(tuple(xyz[mn9]), 150.0)), within)
    assert np.array_equal(brain.select(near=("MN9_L", 150.0), side="L"),
                          np.intersect1d(within, brain.select(side="L")))
    unplaced = int(np.flatnonzero(np.isnan(xyz).any(axis=1))[0])
    with pytest.raises(ValueError, match="no position"):
        brain.select(near=(unplaced, 10.0))
    with pytest.raises(TypeError):
        brain.select(near=("MN9_L",))


def test_meta_must_match_the_brain(tmp_path):
    p = write(tmp_path)
    (tmp_path / "small").mkdir()
    small = write(tmp_path / "small", background=40)
    brain = Brain(p["npz"], meta=small["meta"], atlas=p["atlas"])
    with pytest.raises(SystemExit, match="does not describe"):
        brain.meta


def test_old_atlas_without_micrometres_says_how_to_fix(tmp_path):
    p = write(tmp_path)
    with np.load(p["atlas"]) as a:
        np.savez(p["atlas"], xyz=a["xyz"], row=a["row"])
    brain = Brain(p["npz"], meta=p["meta"], atlas=p["atlas"])
    with pytest.raises(SystemExit, match="python -m brain.atlas"):
        brain.positions


def test_selected_rows_drive_the_engine(brain):
    """Rows from select() go straight into Engine: right-side sugar GRNs drive MN9_R, not MN9_L."""
    sugar, mn9 = brain.select(type=SUGAR, side="R"), brain.select(instance=["MN9_L", "MN9_R"])
    eng = Engine(brain, 4, sugar, params={"w_syn": W_SYN}, seed=1)
    eng.drive(np.full(len(sugar), 150.0, np.float32))
    eng.run(500.0)
    left, right = eng.spikes()[:, mn9].sum(0).tolist()
    assert left == 0 and right > 20

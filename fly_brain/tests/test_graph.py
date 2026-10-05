"""brain/graph_engine.py (CUDA Graph) against brain/engine.py.

    python -m pytest tests/test_graph.py      # needs a GPU; the whole-brain check needs brain.npz
"""
from pathlib import Path

import numpy as np
import pytest
import torch

from brain.engine import PARAMS, W_SYN, Engine, experiment
from tests.test_engine import INPUTS, N, STEPS, network, toy

pytestmark = pytest.mark.skipif(not torch.cuda.is_available(), reason="no GPU")
ROOT = Path(__file__).resolve().parents[1]


def graph(*args, **kw):
    from brain.graph_engine import graph_experiment
    return graph_experiment(*args, device="cuda", **kw)


def test_same_spikes_as_the_engine_with_deterministic_input(tmp_path):
    edges, _ = network()
    b = toy(tmp_path, N, edges)
    hz = 1000.0 / PARAMS["dt"]  # an event every step: no randomness left
    eng = Engine(b, flies=1, inputs=INPUTS, device="cuda")
    eng.drive([hz] * len(INPUTS))
    ref = np.zeros((N, STEPS), np.int32)
    for t in range(STEPS):
        ref[eng.step().cpu().numpy(), t] = 1
    r = graph(b, INPUTS, [hz] * len(INPUTS), record_neurons=np.arange(N), flies=1, ms=STEPS * PARAMS["dt"],
              bin_ms=PARAMS["dt"])
    assert ref.sum() > 1000
    assert np.array_equal(r["binned"][0], ref)


def test_toy_rates_match_the_engine(tmp_path):
    b = toy(tmp_path, 3, [(0, 1, 200.0), (1, 2, -100.0), (0, 2, 150.0)])
    kw = dict(flies=200, ms=500.0)
    ref = experiment(b, [0], 150.0, device="cuda", **kw)["mean_hz"]
    new = graph(b, [0], [150.0], **kw)["mean_hz"]
    assert np.allclose(ref, new, rtol=0.05)
    silenced = graph(b, [0], [150.0], silenced=[0], **kw)["mean_hz"]
    assert silenced[0] > 100 and silenced[1] == 0


@pytest.mark.skipif(not (ROOT / "brain.npz").exists(), reason="no brain.npz")
def test_whole_brain_matches_the_engine():
    from brain import stimuli
    from brain.connectome import Brain
    brain = Brain()
    sugar, mn9 = stimuli.group("sugar"), stimuli.mn9()
    kw = dict(record_neurons=mn9, flies=16, ms=1000.0, bin_ms=50.0, params={"w_syn": W_SYN})
    ref = experiment(brain, sugar, stimuli.SHIU_HZ, device="cuda", **kw)
    new = graph(brain, sugar, np.full(len(sugar), stimuli.SHIU_HZ), **kw)
    assert abs(new["mean_hz"].sum() / ref["mean_hz"].sum() - 1) < 0.05
    assert abs(new["mean_hz"][mn9[0]] - ref["mean_hz"][mn9[0]]) < 10

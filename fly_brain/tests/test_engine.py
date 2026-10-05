"""brain/engine.py on hand-made networks small enough to check by hand.

    python -m pytest tests/test_engine.py
"""
import math

import numpy as np
import pytest
import torch

from brain.connectome import Brain
from brain.engine import PARAMS, Engine, experiment
from brain.loop import BrainLoop

DELAY = round(PARAMS["t_dly"] / PARAMS["dt"])  # 18 steps
RFC = round(PARAMS["t_rfc"] / PARAMS["dt"])     # 22 steps


def toy(tmp_path, n, edges):
    """A Brain from (pre, post, signed synapse count) triples."""
    edges = sorted(edges)
    ptr = np.zeros(n + 1, np.int64)
    np.cumsum(np.bincount([e[0] for e in edges], minlength=n), out=ptr[1:])
    path = tmp_path / "toy.npz"
    np.savez(path, body_ids=np.arange(100, 100 + n), ptr=ptr, post=np.array([e[1] for e in edges], np.int32),
             syn=np.array([e[2] for e in edges], np.float32))
    return Brain(path)


N, INPUTS, STEPS = 500, [0, 1, 2], 1000  # random test network: 500 neurons, 3 driven, 100 ms


def network(seed=3):
    """Random signed edges among N neurons, and initial potentials (mV) that put some above threshold."""
    rng = np.random.default_rng(seed)
    pre, post = rng.integers(0, N, 6000), rng.integers(0, N, 6000)
    keep = pre != post
    pairs = {(int(i), int(j)) for i, j in zip(pre[keep], post[keep])}
    edges = [(i, j, float(rng.integers(1, 40) * (-1 if rng.random() < 0.3 else 1))) for i, j in sorted(pairs)]
    return edges, rng.uniform(-52.0, -44.0, N)


def fire_now(eng, fly, neuron):
    """Put a neuron above threshold so it spikes on the next step."""
    eng.v[fly, neuron] = eng.v_th + 1.0


def test_one_synaptic_event_matches_the_closed_form(tmp_path):
    """A single event g += w: v - v_0 = w * tau / (tau - t_mbr) * (exp(-t/tau) - exp(-t/t_mbr))."""
    eng = Engine(toy(tmp_path, 1, []), flies=1)
    w = 2.0
    eng.g[0, 0] = w
    p = PARAMS
    for k in range(1, 400):
        eng.step()
        t = k * p["dt"]
        expect = w * p["tau"] / (p["tau"] - p["t_mbr"]) * (math.exp(-t / p["tau"]) - math.exp(-t / p["t_mbr"]))
        assert eng.v[0, 0].item() == pytest.approx(expect, rel=1e-4, abs=1e-6)


def test_spikes_arrive_after_the_synaptic_delay(tmp_path):
    eng = Engine(toy(tmp_path, 2, [(0, 1, 3.0)]), flies=1)
    fire_now(eng, 0, 0)
    assert eng.step().tolist() == [0]           # step 0: neuron 0 fires
    for _ in range(DELAY - 1):                  # steps 1..17: nothing arrives
        eng.step()
        assert eng.g[0, 1].item() == 0.0
    eng.step()                                  # step 18: g += 3 synapses * w_syn
    assert eng.g[0, 1].item() == pytest.approx(3.0 * PARAMS["w_syn"])


def test_reset_refractory_period_and_dropped_input(tmp_path):
    # 0 -> 1 and 2 -> 1 with huge weights; 0 and 1 fire at step 0, 2 fires at step 10
    eng = Engine(toy(tmp_path, 3, [(0, 1, 500.0), (2, 1, 500.0)]), flies=1)
    fire_now(eng, 0, 0)
    fire_now(eng, 0, 1)
    assert eng.step().tolist() == [0, 1]
    assert eng.v[0, 1].item() == eng.v_rst and eng.free_at[0, 1].item() == RFC
    for _ in range(9):
        eng.step()
    fire_now(eng, 0, 2)                         # step 10: neuron 2 fires, arriving at 1 at step 28
    while eng.t < RFC:                          # step 18: the step-0 spike reaches 1 while it is refractory ...
        eng.step()
        assert eng.v[0, 1].item() == eng.v_rst and eng.g[0, 1].item() == 0.0  # ... and is dropped (Brian2)
    for _ in range(10 + DELAY - RFC):           # steps 22..27: 1 integrates again, nothing arrives
        eng.step()
    assert eng.g[0, 1].item() == 0.0
    eng.step()                                  # step 28: the step-10 spike lands
    assert eng.g[0, 1].item() == pytest.approx(500.0 * PARAMS["w_syn"])


def test_poisson_input_sets_the_rate_and_has_no_refractory_period(tmp_path):
    b = toy(tmp_path, 2, [])
    hz = experiment(b, [0], 300.0, flies=50, ms=1000.0)["mean_hz"]
    assert 280 < hz[0] < 305  # every Poisson event makes a spike on the next step
    assert hz[1] == 0
    # with a refractory period, events during it are dropped: mean interval = 1 + rfc + 1 / lam steps
    with_rfc = experiment(b, [0], 300.0, flies=50, ms=1000.0, params={"t_rfc_input": 2.2})["mean_hz"]
    lam = 300.0 * PARAMS["dt"] / 1000.0
    assert with_rfc[0] == pytest.approx(1000.0 / PARAMS["dt"] / (1 + RFC + 1 / lam), rel=0.03)  # ~178 Hz


def test_excitation_inhibition_and_silencing(tmp_path):
    # 0 -> 2 excites (one event peaks at ~0.16 * 200 * w_syn = 8.6 mV > the 7 mV to threshold), 1 -> 2 inhibits
    b = toy(tmp_path, 3, [(0, 2, 200.0), (1, 2, -300.0)])
    excited = experiment(b, [0], 100.0, flies=40, ms=1000.0)["mean_hz"]
    assert excited[2] > 50
    both = experiment(b, [0, 1], [100.0, 100.0], flies=40, ms=1000.0)["mean_hz"]
    assert both[2] < excited[2] / 2
    silenced = experiment(b, [0], 100.0, flies=40, ms=1000.0, silenced=[0])["mean_hz"]
    assert silenced[0] > 90 and silenced[2] == 0  # Shiu's silencing: the neuron fires, its synapses do nothing


def test_flies_are_independent_and_seeded(tmp_path):
    b = toy(tmp_path, 2, [(0, 1, 200.0)])
    eng = Engine(b, flies=3, inputs=[0], seed=7)
    eng.drive([[200.0], [0.0], [200.0]])
    eng.run(500.0)
    c = eng.count[:, 1].tolist()
    assert c[0] > 0 and c[1] == 0 and c[2] > 0 and c[0] != c[2]
    again = Engine(b, flies=3, inputs=[0], seed=7)
    again.drive([[200.0], [0.0], [200.0]])
    again.run(500.0)
    assert torch.equal(again.count, eng.count)


def test_brainloop_windows_add_up(tmp_path):
    b = toy(tmp_path, 3, [(0, 1, 200.0), (1, 2, 200.0)])
    loop = BrainLoop(b, n_run=4, stim_idx=[0], readout_idx=[2])
    loop.set_rates(np.array([[100.0], [100.0], [0.0], [30.0]]))
    total_readout, total_pop = torch.zeros(4, 1, dtype=torch.int32), torch.zeros(4, dtype=torch.int64)
    for _ in range(100):
        counts, pop = loop.run(10.0)
        total_readout += counts
        total_pop += pop
    everything = loop.take_counts()
    assert loop.t == 10000
    assert torch.equal(total_readout[:, 0], everything[:, 2])
    assert torch.equal(total_pop, everything[:, 1:].sum(1).long())
    assert everything[2].sum() == 0 and everything[0, 2] > 0


@pytest.mark.skipif(not torch.cuda.is_available(), reason="no GPU")
def test_cuda_matches_cpu_statistically(tmp_path):
    b = toy(tmp_path, 3, [(0, 1, 200.0), (1, 2, -100.0), (0, 2, 150.0)])
    cpu = experiment(b, [0], 150.0, flies=200, ms=500.0)["mean_hz"]
    gpu = experiment(b, [0], 150.0, flies=200, ms=500.0, device="cuda")["mean_hz"]
    assert np.allclose(cpu, gpu, rtol=0.05)

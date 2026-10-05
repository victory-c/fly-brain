"""brain/engine.py against Shiu et al.'s own Brian2 model, spike for spike (needs `pip install brian2`).

A random 500-neuron network with Shiu's equations, constants and update schedule, built once in Brian2
(model.py of github.com/philshiu/Drosophila_brain_model) and once with Engine. The Poisson inputs run at
1/dt so they are deterministic in both, and the two must produce the same spikes at the same steps.

    python -m pytest tests/test_brian2.py
"""
import numpy as np
import pytest

from brain.engine import PARAMS, Engine
from tests.test_engine import INPUTS, N, STEPS, network, toy

b2 = pytest.importorskip("brian2")


def brian2_spikes(edges, v0):
    from brian2 import Hz, Network, NeuronGroup, PoissonInput, SpikeMonitor, Synapses, defaultclock, mV, ms, prefs

    prefs.codegen.target = "numpy"
    defaultclock.dt = PARAMS["dt"] * ms
    p = {k: PARAMS[k] * mV for k in ("v_0", "v_rst", "v_th", "w_syn")}
    p.update({k: PARAMS[k] * ms for k in ("t_mbr", "tau")})
    neu = NeuronGroup(N, """dv/dt = (v_0 - v + g) / t_mbr : volt (unless refractory)
                            dg/dt = -g / tau : volt (unless refractory)
                            rfc : second""",
                      method="linear", threshold="v > v_th", reset="v = v_rst; g = 0 * mV", refractory="rfc",
                      namespace=p)
    neu.v = v0 * mV
    neu.g = 0 * mV
    neu.rfc = PARAMS["t_rfc"] * ms
    syn = Synapses(neu, neu, "w : volt", on_pre="g += w", delay=PARAMS["t_dly"] * ms)
    syn.connect(i=[e[0] for e in edges], j=[e[1] for e in edges])
    syn.w = np.array([e[2] for e in edges]) * PARAMS["w_syn"] * mV
    pois = []
    for i in INPUTS:
        pois.append(PoissonInput(neu[i:i + 1], "v", N=1, rate=(1000.0 / PARAMS["dt"]) * Hz,
                                 weight=PARAMS["w_syn"] * PARAMS["f_poi"] * mV))
        neu.rfc[i] = 0 * ms
    mon = SpikeMonitor(neu)
    net = Network(neu, syn, mon, *pois)
    net.run(STEPS * PARAMS["dt"] * ms)
    steps = np.round(np.asarray(mon.t / ms) / PARAMS["dt"]).astype(int)
    return sorted(zip(steps.tolist(), np.asarray(mon.i).tolist()))


def engine_spikes(brain, v0):
    eng = Engine(brain, flies=1, inputs=INPUTS)
    eng.drive([1000.0 / PARAMS["dt"]] * len(INPUTS))
    eng.v[0] = __import__("torch").as_tensor(v0 - PARAMS["v_0"], dtype=eng.v.dtype)
    out = []
    for t in range(STEPS):
        out += [(t, int(i)) for i in eng.step().tolist()]
    return sorted(out)


def test_engine_reproduces_brian2(tmp_path):
    edges, v0 = network()
    ref = brian2_spikes(edges, v0)
    ours = engine_spikes(toy(tmp_path, N, edges), v0)
    assert len(ref) > 500, "the test network should be active"
    first_diff = next((k for k, (a, b) in enumerate(zip(ref, ours)) if a != b), min(len(ref), len(ours)))
    assert ours == ref, f"{len(ours)} vs {len(ref)} spikes; first difference at spike {first_diff}"

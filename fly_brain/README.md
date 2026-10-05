# fly_brain

A whole male fruit-fly central nervous system as a spiking network: 166,700 neurons and 124 million synapses of
the male CNS v1.0 connectome, each neuron a leaky integrate-and-fire unit, stepped every 0.1 ms on a GPU.

## The model

| Piece | Where | Source |
|---|---|---|
| Neurons, synapse counts, transmitter signs | `brain/connectome.py` | male CNS v1.0 (Janelia FlyEM / Google, 2026); GABA, glutamate and histamine inhibit |
| Neuron and synapse dynamics | `brain/engine.py` | Shiu et al., *Nature* 2024 ([philshiu/Drosophila_brain_model](https://github.com/philshiu/Drosophila_brain_model), MIT), re-implemented in PyTorch |
| Synaptic weight for the male CNS | `runs/calibrate_wsyn.py` | scaled so Shiu's feeding experiment comes out as in his FlyWire model, within the stable range |
| Stimulus groups (sugar, water, bitter, Ir94e GRNs; JO-CE, JO-F) | `brain/stimuli.py` | Shiu's neuron sets, carried over by cell type (`../tools/derive_shiu_groups.py`) |
| 3D positions and display regions | `brain/atlas.py` | soma locations from the male-CNS annotations; regions by sensory modality, circuit, then superclass |

`brain/engine.py` follows Brian2's schedule for Shiu's equations step by step, including two details that are easy
to miss: Poisson-driven neurons have no refractory period, and synaptic or Poisson input that reaches a neuron
while it is refractory is dropped (Brian2 makes `(unless refractory)` variables conditional-write).
`tests/test_brian2.py` runs a random 500-neuron network in Brian2 with Shiu's code and in the engine and requires
the same spikes at the same steps (2,101 spikes over 100 ms). One `Engine` holds many flies at once; `experiment()`
runs a fixed experiment, `brain/loop.py` keeps a brain running inside a body (the bike), and `brain/graph_engine.py`
is a static-shape CUDA Graph version of the same model (`tests/test_graph.py` checks it against the engine spike
for spike). On an RTX A6000 one fly takes 2.1 s per simulated second with the graph engine and 7.5 s without; for
batches the step cost is dominated by the work itself and the plain engine is as fast (128 flies: 34 s vs 47 s;
1,024 flies with the graph engine: 0.36 s per fly-second; `logs/rewrite/bench_*.json`).

**Weight scale.** Shiu's `w_syn = 0.275 mV` was fit on FlyWire (393 synapses per neuron); the male CNS has 745,
so the same weight overdrives it. `runs/calibrate_wsyn.py` first runs Shiu's own FlyWire network with his 21
sugar GRNs at 0-200 Hz (MN9, the proboscis motor neuron, reaches 92 Hz at 200 Hz, as in his Fig. 1), then
sweeps the male-CNS scale: the MN9 curve of one labellum's sugar GRNs, and whether strong drive (both sides at
200 Hz: sugar, bitter, sugar + bitter, sugar + water, JO-CE) runs away. See `results/calibrate_wsyn.json`.

| scale | MN9 at 100 / 200 Hz sugar | strong drive |
|---|---|---|
| FlyWire, Shiu's model | 63 / 92 Hz | |
| 0.45 | 5 / 27 Hz | stable |
| **0.47** (used) | 9 / 35 Hz | stable |
| 0.48 | 11 / 40 Hz | JO-CE runs away |
| 0.60 | 49 / 91 Hz | bitter, sugar + bitter and JO-CE run away |

So the male CNS cannot reproduce Shiu's feeding gain and stay stable at the same time: matching his MN9 curve
(0.60) makes bitter drive explode. `W_SYN_SCALE = 0.47` is the stable scale closest to his curve, the rule fixed
in the script before the sweep.

## Layout

```
brain/      connectome.py  engine.py  loop.py  graph_engine.py  stimuli.py  atlas.py  shiu_groups.json
runs/       calibrate_wsyn.py, bench_gpu.py, profile_step.py; the bike: screen.py, probe.py, ride.py
bike/       bicycle dynamics (Whipple / Meijaard 2007), senses, readout; see bike/README.md
export/     export_dashboard.py + pack_dashboard.py (Fly Brain Live), export_ride*.py, export_attempts.py (/ride/)
dashboard/  Fly Brain Live page and its data
tests/      test_engine.py, test_brian2.py (needs brian2), test_graph.py (needs a GPU), test_bike.py, test_ride.py
results/    small JSON summaries of every run; the attempts page under results/attempts_page/
```

## Running

Python 3.11+ with `numpy pandas pyarrow torch` (and `pytest`; `brian2` for the Brian2 check). Put the three
male CNS v1.0 tables (minconf 0.5, ~1.1 GB, [male-cns.janelia.org/download](https://male-cns.janelia.org/download))
in `data/`, then from this directory:

```bash
python -m brain.connectome                 # -> brain.npz, brain_meta.parquet (~30 s, ~20 GB RAM)
python -m brain.atlas                      # -> web_data/atlas.npz (3D point cloud)
python -m pytest tests                     # engine, Brian2 and CUDA Graph checks, bike
python -m runs.calibrate_wsyn              # the weight-scale sweep (GPU, ~30 min)
python -m export.export_dashboard && python export/pack_dashboard.py   # Fly Brain Live data (GPU, ~5 min)
```

A one-off experiment from Python:

```python
from brain import stimuli
from brain.connectome import Brain
from brain.engine import W_SYN, experiment

brain = Brain()
r = experiment(brain, stimuli.group("sugar"), 150.0, flies=16,
               params={"w_syn": W_SYN}, device="cuda")
print(r["mean_hz"][stimuli.mn9()])         # MN9 left, right in Hz
```

The bike experiments are described in [bike/README.md](bike/README.md).

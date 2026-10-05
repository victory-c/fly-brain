# fly-brain

A fruit fly's whole central nervous system, 166,700 neurons and every synapse between them, run as
a spiking network. We replay classic stimulation experiments on it, record every neuron, and put it in
charge of a road bike.

**Live demos: https://fly-brain.vercel.app**

| Demo | What you see |
|---|---|
| [The fly learns to ride](https://fly-brain.vercel.app/ride/) | From a blank decoder, the whole brain learns to ride a Colnago V4Rs down a 7 m road in side gusts by trial and error; every attempt of the search is replayable, one rider at a time (falls, off-road exits, records), with his brain firing in the side panel. Also: [3D replay of the best decoder, 16 riders](https://fly-brain.vercel.app/ride/3d), [charts](https://fly-brain.vercel.app/ride/charts), [PD rider without a brain](https://fly-brain.vercel.app/ride/oracle), [brain in the loop but not steering](https://fly-brain.vercel.app/ride/open-loop) |
| [Fly Brain Live](https://fly-brain.vercel.app/dashboard/) | Brain activity in 50 ms frames (all 140,638 neurons with a known position) while his sugar, water, bitter or Ir94e taste neurons, or his antennal JO-CE / JO-F neurons, are driven as in Shiu et al. 2024; whether the feeding motor neuron MN9 fires, next to what Shiu found on FlyWire |

## The simulator

`fly_brain/brain/` is our implementation of the whole-brain leaky integrate-and-fire model of Shiu et al.,
*Nature* 2024 ([philshiu/Drosophila_brain_model](https://github.com/philshiu/Drosophila_brain_model), MIT),
in PyTorch, on the male CNS v1.0 connectome (Janelia FlyEM / Google, 2026):

- **Same model as Shiu's Brian2 code, spike for spike.** `tests/test_brian2.py` builds a random network once
  with Shiu's equations in Brian2 and once in our engine and requires identical spikes at identical steps.
  Getting there meant matching two Brian2 details: neurons driven by Poisson input have no refractory period,
  and input arriving during a refractory period is dropped, not held.
- **Many flies at once on a GPU.** One engine steps a batch of independent flies (event-driven delivery, 0.1 ms
  steps), plus a static-shape CUDA Graph version (`graph_engine.py`), checked against the engine spike for spike: 2.1 s
  per simulated second for one fly instead of 7.5 s; from ~100 flies on the plain engine is as fast (128 flies: 34 s).
- **Calibrated, not tuned.** The synaptic weight is scaled for the male CNS's denser wiring by rerunning Shiu's
  own FlyWire feeding experiment (sugar taste neurons → MN9) and taking the closest stable scale: 0.47
  (`runs/calibrate_wsyn.py`, `results/calibrate_wsyn.json`). The male CNS cannot match Shiu's feeding gain
  and stay stable at once: at the scale that matches it (0.60), bitter drive makes the brain run away.
- **Stimuli from the paper.** Shiu's sets of taste and antennal neurons, carried over to the male CNS by
  cell type (`tools/derive_shiu_groups.py` → `brain/shiu_groups.json`).

Details and commands: [fly_brain/README.md](fly_brain/README.md).

## The bike

`fly_brain/bike/`, `brain/loop.py`, `runs/screen.py`, `runs/ride.py`; details in
[fly_brain/bike/README.md](fly_brain/bike/README.md). Bike state becomes firing of real balance, wind,
optic-flow and leg sensory neurons; descending-neuron firing is decoded into steering torque, pedalling and
braking; the connectome is never changed, only the decoder is learned. The walking command neurons of the
literature do not track the lean, but flight-steering descending neurons (DNp20, DNg46, DNp22, ...) track roll
rate with opposite sign left and right, so the fly steers the bike with its flight-stabilisation reflex.

On the rewritten simulator the fly learns to ride from a blank decoder in 37 generations of 48 riders (1,776
attempts, `ride-relearn.sbatch`): in the last generation 35 of 48 ride the full 15 s on a 7 m road in side gusts
and none falls. The final decoder, replayed for 20 s, keeps all 16 riders upright and on the road 19.2 s on
average. The decoders learned on the earlier simulator do not carry over (the two Brian2 rules lower the brain's
activity), so this run replaced them on the /ride/ pages; see the bike README's "Simulator change".

```
fly-brain/
├── fly_brain/        brain/ (simulator), runs/, bike/, export/, dashboard/, tests/, results/
├── site/             landing page and build script for the Vercel site
├── tools/            jobs_ledger.py (JOBS.md from sacct), derive_shiu_groups.py
├── *.sbatch          Slurm jobs (calibrate-wsyn, ride-*, bench, cuda-venv, dashboard)
├── sync.sh           commit + push everything that changed (code, results, logs, JOBS.md)
├── JOBS.md           every Slurm job (sbatch and srun) with its exact command line and outputs
└── logs/             Slurm output files; logs/inline/ has scripts fed to srun on stdin
```

## Running it

The web demos need nothing but a browser; `bash site/build.sh` collects them into `site/dist`.

To run the simulations you need Python 3.11+ with `numpy pandas pyarrow torch` and the male CNS v1.0 files
(~1.1 GB, [male-cns.janelia.org/download](https://male-cns.janelia.org/download)) in `fly_brain/data/`; then,
from `fly_brain/`, `python -m brain.connectome` builds `brain.npz` (~30 s) and `python -m pytest tests` checks
the engine. The sbatch scripts are written for the OCF `corruption` node (partition `ocf-hpc`); the newer ones
(`calibrate-wsyn`, `ride-relearn`) are submitted from the repo root, the older ones use absolute
`/home/s/st/stevejobs/flybrain` paths.

Not committed (too large, or rebuildable): the connectome download, `brain.npz`, virtualenvs, raw per-bin
arrays (`*.parquet`, `dashboard/data/*.bin`, `results/*_brain.npz`).

## Other fly-brain projects we looked at

Cloned next to our work for reference and not copied here:

| Project | What it is |
|---|---|
| [Lulzx/fly-brain](https://github.com/Lulzx/fly-brain) | male CNS as a spiking brain in a physics-simulated body, in the browser (MIT) |
| [solomonsealed/flybrain](https://github.com/solomonsealed/flybrain) | FlyWire brain driving flies in a 3D garden, in a Web Worker (MIT) |
| [eonsystemspbc/fly-brain](https://github.com/eonsystemspbc/fly-brain) | Shiu et al. FlyWire LIF model: activate / silence neurons (GPL-2.0) |

## Credits

Connectome: male CNS v1.0, HHMI Janelia FlyEM and Google Research. Neuron model and stimulus sets: Shiu et al.,
*Nature* 2024. FlyWire cell types: Schlegel et al. / Dorkenwald et al., *Nature* 2024. Bicycle model: Meijaard
et al., *Proc. R. Soc. A* 2007.

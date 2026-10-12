# Getting started

This repository runs the whole male fruit-fly central nervous system (166,700 neurons, male CNS v1.0) as a
spiking network and puts it in closed loop with a bicycle. This page gets you from nothing to running code in
under an hour, whichever way you work: Colab, your laptop, or the OCF GPU node.

## 1. First 15 minutes

1. Open the quickstart in Colab: [notebooks/00_quickstart.ipynb](https://colab.research.google.com/github/victory-c/fly-brain/blob/main/notebooks/00_quickstart.ipynb).
   Set *Runtime > Change runtime type > T4 GPU*, then *Runtime > Run all*. It downloads the prebuilt brain,
   replays Shiu et al.'s feeding experiment, silences a cell type and draws a spike raster.
2. Keep [GLOSSARY.md](GLOSSARY.md) open while you read code. Row vs bodyId is the one that bites everyone.
3. Before you quote any number from the READMEs or `results/`, check [CURRENT_NUMBERS.md](CURRENT_NUMBERS.md):
   some results come from the earlier simulator and were not re-run.
4. When you write your own experiment, pass `params={"w_syn": W_SYN}` (from `brain.engine`) to `Engine`,
   `experiment()` or `BrainLoop`. Without it they use Shiu's unscaled FlyWire weight, which overdrives the
   male CNS.

## 2. Running it yourself

### Laptop (macOS or Linux, Python 3.11+)

The full repository is large (about 600 MB of history and a 1.9 GB working tree, mostly ride traces under
`fly_brain/results/`). A sparse clone of the code is about 1 MB:

```bash
git clone --filter=blob:none --sparse https://github.com/victory-c/fly-brain.git
cd fly-brain
git sparse-checkout set fly_brain/brain fly_brain/bike fly_brain/runs fly_brain/tests notebooks docs tools
bash make-venv.sh                 # venv/ with CPU torch and requirements.txt
source venv/bin/activate
cd fly_brain
python -m brain.fetch             # the prebuilt brain, about 220 MB, checksummed
python -m pytest tests            # about 15 s on CPU; GPU and Brian2 tests skip
```

Add more later with `git sparse-checkout add <path>`. `fly_brain/results/` is 1.9 GB on its own; add single
files you need (for example a decoder to replay) rather than the whole directory.

The simulator runs on a CPU, slowly: roughly 9 s of wall time per simulated second for one fly on a 32-core
node (old simulator, `results/bench_gpu.json`), more on a laptop. That is enough for a few flies and short
runs. Use a GPU for sweeps.

No data? `tests/synthetic_brain.py` writes a 454-neuron made-up brain in the real file layout. Use it to develop
and test code without the download.

### OCF GPU node (`corruption`: 4x RTX A6000)

Cluster docs: [OCF HPC](https://bestdocs.ocf.io/user-docs/services/hpc/). Ask Victor for access first; the node
is shared.

```bash
git clone --filter=blob:none --sparse https://github.com/victory-c/fly-brain.git && cd fly-brain
git sparse-checkout set fly_brain/brain fly_brain/bike fly_brain/runs fly_brain/tests docs tools
sbatch cuda-venv.sbatch           # builds venv-cuda/ on the GPU node and checks the GPU
bash make-venv.sh                 # venv/ (CPU) for light work on the login node
(cd fly_brain && ../venv/bin/python -m brain.fetch)
```

House rules on the cluster:

- Submit every `*.sbatch` from the repository root. The scripts `cd` into `fly_brain/` themselves, write logs to
  `logs/` and use `venv-cuda/` next to them; set `PY=/path/to/python` to use another interpreter.
- Ask for the memory you need, not more (`sacct -j <id> -o MaxRSS` after a test run), and keep at most two or
  three jobs at a time. Long matrices run overnight.
- Do **not** run `sync.sh`. It is the owner's cron job; it commits everything and pushes straight to `main`.

## 3. Reading pack

| Read | Why |
|---|---|
| Shiu et al., *Nature* 2024, [A Drosophila computational brain model reveals sensorimotor processing](https://www.nature.com/articles/s41586-024-07763-9) | The neuron model this simulator implements, spike for spike, and the experiments the quickstart replays |
| The Transmitter, [Digital sphinx raises questions about connectome models](https://www.thetransmitter.org/systems-neuroscience/digital-sphinx-raises-questions-about-connectome-models/) | The open objection: a worm connectome plus a trained decoder can also drive a fly body. How much does the wiring matter? |
| [FLY-lab README](https://github.com/Recluse/FLY-lab) | Shuffled fly wiring breaks signal flow; on easy tasks, simple controllers match the connectome |
| [flybench README](https://github.com/brandoncho369/flybench) and [CONTROLS.md](https://github.com/brandoncho369/flybench/blob/master/docs/CONTROLS.md) | Open-loop benchmark tasks with rewired, random and sign-flip controls |
| Eon Systems, [Embodied brain emulation](https://eon.systems/updates/embodied-brain-emulation) | A whole-brain fly model driving a simulated body; Eon also maintains a version of Shiu's model ([eonsystemspbc/fly-brain](https://github.com/eonsystemspbc/fly-brain)) |

## 4. Sending changes

- Work on a branch and open a pull request to `main`. GitHub Actions runs the CPU tests on every pull request;
  they have to pass.
- Add a test for new behaviour. The synthetic brain makes most tests possible without the connectome.
- Never commit data: the male CNS tables (`fly_brain/data/`), `brain.npz`, `brain_meta.parquet`,
  `web_data/`, `*.parquet`, whole-brain recordings (`results/*_brain.npz`). `.gitignore` covers them. GitHub
  rejects files over 100 MB.
- Commit small JSON summaries of runs under `fly_brain/results/`, and the exact command that produced them in
  the pull request description.
- `JOBS.md` is generated from Slurm's `sacct` by `tools/jobs_ledger.py`; do not edit it by hand.

## 5. Where things are

| Path | What |
|---|---|
| `fly_brain/brain/connectome.py` | `Brain`: the wiring as CSR arrays, `brain.meta` (one row per neuron), `brain.select(...)`; `python -m brain.connectome` builds it from the male CNS tables |
| `fly_brain/brain/select.py` | Finding neurons by type, instance, side, superclass, class, transmitter, region or position |
| `fly_brain/brain/engine.py` | The spiking model (Shiu's equations), many flies at once; `experiment()` for one-shot runs |
| `fly_brain/brain/stimuli.py` | Shiu's stimulus groups (sugar, water, bitter, Ir94e, JO-CE, JO-F) and MN9 |
| `fly_brain/brain/loop.py` | The brain inside a body, read out in windows |
| `fly_brain/brain/atlas.py` | Soma positions and display regions |
| `fly_brain/brain/fetch.py` | Downloads the prebuilt brain from the GitHub release |
| `fly_brain/bike/` | Bicycle dynamics (Whipple / Meijaard 2007), senses, readout; see `bike/README.md` |
| `fly_brain/runs/` | Experiments: weight calibration, sensory screen, probe, closed-loop learning (`ride.py`) |
| `fly_brain/tests/` | Tests; `synthetic_brain.py` is the made-up brain |
| `notebooks/` | Colab notebooks, starting with `00_quickstart.ipynb` |
| `tools/` | `publish_brain.sh` (release the prebuilt brain), `jobs_ledger.py`, `derive_shiu_groups.py` |

## 6. Licence and credit

The code is MIT-licensed ([LICENSE](../LICENSE)). The connectome data, including the prebuilt files `brain.fetch`
downloads, is derived from the male CNS v1.0 (HHMI Janelia FlyEM, Cambridge Connectomics Group, Google
Research) and licensed CC-BY 4.0. Cite Berg et al., *Cell* 189, 5504 (2026),
[doi:10.1016/j.cell.2026.08.015](https://doi.org/10.1016/j.cell.2026.08.015), and Shiu et al. 2024 for the
model. [CITATION.cff](../CITATION.cff) has the full references.

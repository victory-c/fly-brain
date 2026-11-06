# Which numbers are current

The simulator was rewritten on 2026-10-04. The new engine (`fly_brain/brain/engine.py`, first committed in
`0588bd1`) follows two Brian2 rules that the earlier port missed: neurons driven by Poisson input have no
refractory period, and input that reaches a refractory neuron is dropped. The synaptic weight scale also moved
from 0.45 to 0.47. The two rules lower the brain's activity (the higher scale wins part of it back), so decoders
fitted on the earlier simulator do not carry over. The learning-from-blank run was repeated on the new simulator;
the passenger screen and the two lane-keeping rounds were not (`fly_brain/bike/README.md`, "Simulator change").

## Rule of thumb for quoting numbers

- A bike result that involves the brain is current only if it comes from the learn-from-blank run (job 36555,
  `results/relearn/`) or its replays (job 36626: `results/ride_road_trace.json`,
  `results/ride_pilot_road_trace.json`).
  The passenger screen, the "flight-stabilisation reflex" finding, both lane-keeping rounds, the gain sweep and
  DAgger come from the earlier simulator. Say so when you quote them, or leave them out.
- Bike physics and connectome counts do not depend on the simulator: the self-stable speed range, the Whipple
  check, neuron and synapse counts, and the PD rider without a brain.
- Most current riding numbers come from one run at 5.5 m/s with 5 Nm gusts. That speed is inside the bike's
  self-stable range (4.70 to 7.74 m/s), where the bike balances itself, so say "stays on the road", not
  "balances the bike". The exceptions are the balance-gate runs at 4.0 and 4.5 m/s (below), where the bike falls
  without steering. Always give the job id, because a rerun will not reproduce a number exactly (see the last
  section).
- For simulator speed, use `logs/rewrite/bench_*.json`, not `fly_brain/results/bench_*.json` or the landing page.

## How the status was decided

- **Run logs.** Every bike run (`runs/ride.py`) prints its weight. `w_syn 0.1238 mV` is 0.275 x 0.45 (earlier simulator) and
  `w_syn 0.1293 mV` is 0.275 x 0.47 (current). Of the bike logs in `logs/`, only `ride-relearn-36543.out` and
  `ride-relearn-36555.out` print the second value.
- **Dates.** The first rewrite job is 36533 (2026-10-04 05:35 in `JOBS.md`). Every job before it ran on the
  earlier simulator (`brain/sim.py`, never committed to this repo). The rewrite jobs ran in a worktree and were
  committed at 21:15 the same day.
- **Result JSONs.** `config.w_syn_scale` is `null` in both eras (null meant 0.45 before the rewrite and 0.47
  after), so a JSON's config cannot tell you which simulator made it. `dashboard/data/index.json` records
  `wSyn: 0.12925` (scale 0.47). For every other file, use the job that wrote it and its last commit.

`README.md` is the top-level README; the other two are `fly_brain/README.md` and `fly_brain/bike/README.md`. Other
paths are relative to `fly_brain/` unless they start with `logs/`, `site/` or `JOBS.md`, which sit at the repo root.

## Model, data and calibration

| Claim | Value | Source | Status |
|---|---|---|---|
| Neurons in the model | 166,700 | `fly_brain/README.md:3`; `logs/rewrite/connectome-build-36533.out` (job 36533) | simulator-independent |
| Synapses, connected pairs, inhibitory share | 124,177,617; 25,582,938; 38.4% | same log | simulator-independent |
| Synapses per neuron, male CNS vs FlyWire | 745 vs 393 | `fly_brain/README.md:27`; `brain/engine.py:47` | simulator-independent |
| Neurons with a 3D position (brain maps) | 140,638 | `dashboard/data/index.json` | simulator-independent |
| Bike's sensory and read-out neurons | 789 driven; 112 read out (42 types) by the current decoder, 92 (33 types) by the base readout | `logs/ride-relearn-36555.out`, `logs/flyride-36091.out` | simulator-independent |
| Engine matches Shiu's Brian2 code spike for spike | 2,101 spikes over 100 ms, 500-neuron network | `fly_brain/README.md:19-20`; `tests/test_brian2.py` | current. Passed 2026-10-29 on the login VM with brian2 2.9.0 and numpy 2.2 (`logs/rewrite/test-brian2-parity-local.out`). The three logged cluster test runs (jobs 36627, 36631, 36637) skipped it because brian2 is not installed, and brian2 2.9.0 does not import under numpy 2.4 (`np.ndarray.ptp` was removed) |
| Graph engine matches the engine spike for spike | test passes | `tests/test_graph.py`; `logs/rewrite/tests3-36637.out` | current |
| Synaptic weight scale | `W_SYN_SCALE` 0.47, `w_syn` 0.129 mV | `results/calibrate_wsyn.json` (job 36539) | current |
| MN9 at 100 / 200 Hz, one labellum's sugar GRNs | Shiu's FlyWire model, rerun here with 20 of his 21 sugar GRNs: 63 / 92 Hz; scale 0.45: 5 / 27; 0.47: 9 / 35; 0.48: 11 / 40, JO-CE runs away; 0.60: 49 / 91, bitter, sugar + bitter and JO-CE run away | same | current |

## Speed

| Claim | Value | Source | Status |
|---|---|---|---|
| One fly, wall time per simulated second | 2.1 s graph engine, 7.5 s plain engine | `logs/rewrite/bench_graph_engine.json` (job 36627), `logs/rewrite/bench_engine.json` (job 36551) | current |
| 128 flies for 1 s | 34 s plain, 47.5 s graph | same | current |
| 1,024 flies, graph engine | 0.36 s per fly-second, 7.2 GB GPU memory | `logs/rewrite/bench_graph_engine.json` | current |
| Benchmarks in `results/` | 1 fly 8.4 s (GPU); 128 flies 34.6 s; 1,024 flies 0.21 s per fly-second | `results/bench_gpu*.json` (jobs 36078, 36082), `results/bench_graph*.json` (jobs 36138-36146) | old simulator, not re-run. That brain fired about 84,500 spikes/s on this test against about 19,400 now, so the speeds do not transfer |
| Landing page: "~8 s per simulated second; 128 trials take 35 s" | | `site/index.html` | old simulator (matches `results/bench_gpu.json`); current values are 7.5 s and 34 s |
| Bike loop: 48 riders at ~20 s wall per bike second; 15-generation search ~51 min; 16-rider replay ~13.4 s per bike second | | `fly_brain/bike/README.md:245-247` (jobs 36091, 36092); `site/index.html` | old simulator. The current search took about 275 s per 15 s generation (job 36555), roughly 18 s per bike second |

### The node after the upgrade (2026-11-05): no CUDA, CPU speeds

The Slurm node came back from its Debian 13 upgrade with `nvidia-smi` working but CUDA unable to initialise: the
`nvidia_uvm` kernel module is not loaded and `/dev/nvidia-uvm` is missing, so `cuInit` returns 999 and torch falls
back to the CPU without failing (the log says "48 riders on cpu"). The module is built as `nvidia-current-uvm`, but
`/etc/modprobe.d/nvidia.conf` on the node is an old local file where Debian expects the symlink that maps
`nvidia-uvm` to it, so `modprobe nvidia-uvm` fails. Loading the module needs root. Until that is
fixed every job is a CPU job (`sbatch --gres=none -c N` overrides a script's GPU request). Python 3.11 also left
the node; `venv` and `venv-cuda` now point at a conda-forge Python 3.11.18 in the home directory, with the packages
untouched (torch 2.5.1+cu121, numpy 2.4.6, pandas 3.0.6).

| Claim | Value | Source |
|---|---|---|
| Pre-test cell, 30 brains x 1.3 s, CPU | about 290 s per probe at 8 threads on the real wiring (36,000 spikes/s per brain); 1,224 s at 8 million spikes/s (16 threads) | `logs/pretest-37928.out`, `logs/pretest-37936.out` |
| Balance-gate generation on CPU, 48 threads, node shared with other jobs | 2,003 s, 1,695 s and 1,373 s for generations 0 to 2 of R3 (riders up 1 to 2 s on average), against 167 s and 134 s for generations 0 and 1 of the real wiring on the GPU | `logs/ride-rung-37938.out`, `results/gate/v4.5_s201/cem.json` |
| One job | at most 24 h (partition limit), so a CPU search continues with `runs/ride.py --resume` | `ride-rung.sbatch` |
| CPU step with the C kernel (`brain/lif_kernel.c`, from 2026-11-05 18:00), full brain, 48 flies, 16 threads | 5.5, 10.1 and 6.9 ms per step against 34.7, 66.3 and 40.2 ms with the torch ops, at 1,600, 81,000 and 280 undriven spikes/s per brain; the same spikes and the same `v`, `g`, `free_at`, `count` after 2,500 steps in all three | `notes/kern/bench3.py` run by hand on corruption (not in the repo); `tests/test_engine.py::test_c_kernel_and_torch_ops_agree_bit_for_bit` on the small network |
| Balance-gate generation on CPU with the C kernel, 48 threads | 681 s and 705 s for generations 14 and 15 of R3 seed 201, against 3,590 to 4,036 s for generations 8 to 13 with the torch ops (riders up about 7 s in both) | `logs/ride-rung-37946.out`, `logs/ride-rung-37938.out` |

## Fly Brain Live (`/dashboard/`)

| Claim | Value | Source | Status |
|---|---|---|---|
| MN9_L rate, groups on both sides at 150 Hz, 8 flies x 1 s | sugar 62 Hz; sugar + water 58; JO-F 5.6; JO-CE 0.4; water, bitter, sugar + bitter, Ir94e, sugar + Ir94e and weak sugar 0. MN9_R is 0 Hz in all ten. Water alone does not drive MN9 here, although Shiu found it does | `dashboard/data/index.json`; `logs/rewrite/dashboard3-36635.out` (job 36635) | current |

## Bike physics

| Claim | Value | Source | Status |
|---|---|---|---|
| Self-stable speed, road bike model + 70 kg rider | 4.70 to 7.74 m/s (16.9 to 27.8 km/h) | `fly_brain/bike/README.md:33`; `python -m bike.tarmac` | simulator-independent |
| Whipple matrices vs Meijaard et al. 2007 | max error below 1e-8; benchmark bicycle self-stable 4.29 to 6.02 m/s | `tests/test_bike.py` | simulator-independent |
| PD rider, no brain (`/ride/oracle`), 16 x 20 s at 5.5 m/s, 5 Nm | all 16 upright and on the road; largest lateral offset 0.19 m | `results/ride_oracle_trace.json` (job 36488) | simulator-independent |

## Learning to ride from a blank decoder (`/ride/`)

All from one CEM run, job 36555 (`ride-relearn.sbatch`, seed 101), 48 riders x 15 s per generation, 5.5 m/s,
5 Nm gusts, leaving the 7 m road ends a run. `python -m runs.attempts_stats` recomputes these from
`results/relearn/attempts/`.

| Claim | Value | Source | Status |
|---|---|---|---|
| Size of the search | 37 generations x 48 = 1,776 attempts, 165 min on one A6000 | `fly_brain/bike/README.md:183`; `README.md:45-46` | current |
| Generation 0 | 36 of 48 down within 1 s; mean 1.0 s; record 26 m | `fly_brain/bike/README.md:183-184` | current |
| Generation 10 | mean 10.9 s on the bike | `fly_brain/bike/README.md:184` | current |
| Generation 36 (last) | 35 of 48 ride the full 15 s, 0 fall, 13 leave the road; mean 13.8 s | `fly_brain/bike/README.md:184-185`; `README.md:46-47` | current |
| Distance records | 20; the last 87.5 m at attempt 1,700 | `fly_brain/bike/README.md:185-186` | current |
| All attempts | 836 finished, 162 fell, 778 left the road, 0 bailed | `fly_brain/bike/README.md:186` | current |
| Decoder size | 90 numbers: 84 steering weights (42 types x L/R), steering bias, lane-filter gain, 4 pedal/brake terms (frozen) | `results/relearn/cem_mu.json`; `fly_brain/bike/README.md:26` | current |
| An identical earlier run of the same search (job 36543) | 35 of 48 finish in the last generation; 885 finished overall | `fly_brain/bike/README.md:186-188` | current (a different run; see the last section) |

## Learning to ride below the self-stable speed (balance gate)

`ride-gate.sbatch V0 SEED`, jobs 37491-37494 (2026-10-17/18). The setup matches the relearn run, with two
changes: the speed is held at V0 by fixed pedalling (23.1 W at 4.0 m/s, 29.6 W at 4.5) and the brake is off. Each
run is 48 riders x 15 s per generation with 5 Nm gusts, and leaving the road ends a run. Every run stopped at its
5 h cap. "Riding time" is time until a fall or leaving the road (`upright_mean` in `cem.json` "history").
Generation 0 is the blank decoder plus the search's first random spread. It is not a hands-off replay; no
hands-off replay at these speeds is committed.

| Run | Generations | Gen 0 mean riding time | Last gen mean riding time | Last gen riding all 15 s | Source | Status |
|---|---|---|---|---|---|---|
| 4.0 m/s, seed 201 | 61 | 0.75 s | 11.8 s | 42% | `results/gate/v4.0_s201/cem.json`, `logs/ride-gate-37491.out` | current |
| 4.0 m/s, seed 202 | 63 | 0.75 s | 9.6 s | 23% | `results/gate/v4.0_s202/cem.json`, `logs/ride-gate-37493.out` | current |
| 4.5 m/s, seed 201 | 58 | 1.01 s | 13.7 s | 77% | `results/gate/v4.5_s201/cem.json`, `logs/ride-gate-37492.out` | current |
| 4.5 m/s, seed 202 | 57 | 0.87 s | 11.9 s | 52% | `results/gate/v4.5_s202/cem.json`, `logs/ride-gate-37494.out` | current |

The `ride_slow_mu_trace.json` in each run directory replays an earlier-simulator decoder whose pedalling was not
held, so it rode at about 4.85 m/s. It is not a baseline at V0.

The hands-off floor is a replay of each run's `init_hold.json`: no steering, the same held pedalling, senses,
gusts and off-road rule, 16 riders x 15 s, seed 201. It ran on the login VM's CPU on 2026-10-29 while the GPU
node was drained, so it has no job id (`logs/local/handsoff-v*.out`).

| Hands-off | Mean riding time | Longest | Riding all 15 s | Source | Status |
|---|---|---|---|---|---|
| 4.0 m/s | 3.5 s (13 of 16 fell, 3 left the road) | 6.5 s | 0 of 16 | `results/gate/v4.0_s201/handsoff_trace.json` | current |
| 4.5 m/s | 5.7 s (3 of 16 fell, 13 left the road) | 10.0 s | 0 of 16 | `results/gate/v4.5_s201/handsoff_trace.json` | current |

At 4.0 m/s the hands-off bike mostly falls; at 4.5 m/s it mostly drifts off the road first, so that floor is
partly a lane-keeping floor. Generation 0 of the search (0.75-1.0 s) did worse than hands-off, because small random steering weights
destabilise the bike. Compare learned decoders against these floors, not against generation 0.

## The wiring ladder: what each generated rung changes

`brain/variants.py` now writes every rung (R1, R2, R3, R3.5, R4, R5; `docs/GLOSSARY.md` section 7). Seed 1 of
each, generated on the login VM on 2026-11-02 (no job id; about 30-50 s and 3.2 GB each), from the 25,582,938
connections carrying 124,177,616 synapses of the real wiring:

| Rung | Connections after merging duplicates | Original connections kept | Synapses | What else the run reports |
|---|---|---|---|---|
| R1 transmitter errors | unchanged | 100% | unchanged | 9,907 neurons relabelled (5.9%), 8,584 change sign (5.1%); inhibitory share of synapses 38.4% -> 40.2% |
| R2 count jitter | unchanged | 100% | 127,344,656 (+2.6%: a lognormal with median 1 has mean exp(sigma^2/2)) | factors median 1.000, 16-84% range 0.80-1.25 |
| R3 type-preserving | 24,008,062 (-6.2%) | 39.4% | unchanged | 25,267 (type, side) groups, 13,611 of one neuron; 8.2% of neurons keep their inputs |
| R3.5 strength-preserving | 25,489,803 (-0.4%) | 0.6% | unchanged | 1,358 (sign, count) strata, every connection could move |
| R4 degree-preserving | -0.34% | 0.58% | unchanged | see the pre-test below |
| R5 random | -0.13% | 0.27% | unchanged | see the pre-test below |

R3 keeps 39% of the real connections because many (type, side) groups are small: a target drawn from a group of
two or three often lands on the original neuron.

### Pre-test on the new rungs at the calibrated scale (2026-11-02, login VM CPU, 8 brains, draw 1)

Same protocol as the pilot below (`runs/pretest.py --pop VS HALT`, scale 0.47; `logs/local/pretest-r{1,2,3,35}_s1-w0.47.out`,
`results/rungs/pretest_r*_s1_w0.47.json`). Cells as in the pilot table: network spikes/s (network neurons
firing); lateralised outputs VS / haltere (largest null mean); largest |z| VS / haltere (largest null).

| Rung at 0.47 | Network | Lateralised outputs | Largest abs z |
|---|---|---|---|
| R0 real wiring (pilot) | 21,500 (1,550) | 28 / 18 (0.9) | 37 / 16 (5) |
| R1 transmitter errors | 13,700 (1,180) | 15 / 16 (1.8; VS null max 24) | 25 / 23 (12) |
| R1 transmitter errors, 30 brains (confirmatory, 2026-11-03) | 13,000 (1,380) | 35 / 31 (0.1; null max 4 / 13, p95 1) | 43 / 29 (4.5) |
| R2 count jitter | 25,300 (1,670) | 23 / 28 (1.3) | 34 / 23 (5) |
| R3 type-preserving | 15,900 (1,220) | 25 / 20 (0.6) | 31 / 16 (4) |
| R3.5 strength-preserving | 890 (430) | 0 / 0 (0.0) | 2.5 / 1.8 (2.6) |
| R4 degree-preserving (pilot) | 262 (80) | 1 / 1 (0.0) | 5 / 4 (2) |
| R5 random (pilot) | 251 (79) | 0 / 0 (0.0) | 0 / 0 (2) |

What it shows, with one draw and 8 brains per cell:
- R2 is indistinguishable from the real wiring. R3 keeps the left/right channel (25 and 20 lateralised outputs)
  at 74% of the real network rate: cell-type-level wiring is enough to carry the bike's roll signal.
- R3.5 is as silent as R4 and R5: 4% of the real network activity and no lateralised output, even though every
  neuron keeps its in-degree, its incoming synapse total and its excitatory/inhibitory input mix. The right amount
  of input from the wrong partners does not transmit. The transition therefore lies between R3 and R3.5, as the
  preregistration predicts, and it is a matter of partner identity rather than input statistics.
- R1 (5% of neurons with flipped sign) halves the network rate. With 8 brains its VS channel was noisy (15 outputs
  against a null max of 24 from one balanced split); the 30-brain confirmatory run (2026-11-03, login VM CPU,
  `logs/local/pretest-r1_s1-b30-w0.47.out`, `results/rungs/pretest_r1_s1_b30_w0.47.json`, 1,000 random balanced
  relabellings) gives 35 and 31 lateralised outputs against null maxima of 4 and 13 (95th percentile 1), at
  13,000-14,300 network spikes/s. R1 passes the transmission gate at 0.47.
The balance gate has not yet run on R1-R3.5 (the GPU node is drained); the tables below are R0, R4 and R5 only.

### The ladder with 30 brains per cell, and where each rung stops transmitting (2026-11-05)

`pretest-rungs.sbatch` (jobs 37927, 37928, 37936, 37937, 37940-37942, 37947; `logs/pretest-*.out`,
`results/rungs/pretest_*_b30_w*.json`): VS and haltere probes, 30 brains, null = 1,000 random balanced relabellings.
All of it ran on CPU, because CUDA does not initialise on the node since its Debian 13 upgrade (see "The node after
the upgrade" above). The table is `python3 tools/pretest_table.py`; "Gate" applies the transmission gate to both
probes: lateralised outputs above the largest null count, and a network rate of 10,750 to 43,000 spikes/s (within
2x of the real wiring's 21,500). One rewiring draw and one simulation seed per cell.

| Rung | Scale | Network spikes/s, VS / haltere probe | Lateralised outputs VS / haltere | Null max | Largest abs z (null) | Gate |
|---|---|---|---|---|---|---|
| R0 real wiring | 0.47 | 21,345 / 21,641 | 38 / 39 | 11 / 5 | 37 / 29 (5.9) | pass |
| R1 transmitter errors | 0.47 | 12,985 / 14,326 | 35 / 31 | 4 / 13 | 43 / 29 (4.5) | pass |
| R2 count jitter | 0.47 | 24,674 / 25,806 | 50 / 38 | 8 / 6 | 37 / 31 (4.8) | pass |
| R3 type-preserving | 0.47 | 15,665 / 16,171 | 37 / 39 | 5 / 4 | 41 / 36 (4.8) | pass |
| R3.5 strength-preserving | 0.47 | 2,777 / 1,591 | 0 / 3 | 1 / 1 | 3 / 4 (3.7) | fail: no signal, too quiet |
| R3.5 strength-preserving | 0.5 | 15,320 / 16,301 | 1 / 1 | 162 / 158 | 3 / 3 (4.7) | fail: no signal |
| R3.5 strength-preserving | 0.53 | 47,583 / 49,147 | 3 / 4 | 198 / 155 | 5 / 6 (6.0) | fail: no signal, runaway |
| R3.5 strength-preserving | 0.56 | 83,082 / 81,049 | 7 / 9 | 91 / 8 | 10 / 8 (4.6) | fail: no signal, runaway |
| R3.5 strength-preserving | 0.6 | 116,998 / 117,282 | 11 / 24 | 5 / 4 | 13 / 13 (4.9) | fail: runaway |
| R3.5 strength-preserving | 0.8 | 261,194 / 262,441 | 13 / 16 | 5 / 5 | 11 / 11 (5.2) | fail: runaway |
| R3.5 strength-preserving | 1 | 425,010 / 426,448 | 11 / 15 | 7 / 5 | 10 / 12 (6.0) | fail: runaway |
| R3.5 strength-preserving | 1.5 | 981,006 / 983,973 | 7 / 17 | 10 / 8 | 4 / 8 (5.6) | fail: no signal, runaway |
| R3.5 strength-preserving | 2 | 1,630,943 / 1,638,750 | 6 / 9 | 9 / 9 | 4 / 5 (6.7) | fail: no signal, runaway |
| R4 degree-preserving | 0.47 | 277 / 231 | 1 / 2 | 0 / 0 | 9 / 8 (1.9) | fail: too quiet |
| R4 degree-preserving | 0.6 | 462 / 419 | 3 / 3 | 1 / 0 | 13 / 10 (3.1) | fail: too quiet |
| R4 degree-preserving | 0.8 | 824 / 812 | 7 / 6 | 0 / 1 | 19 / 13 (3.1) | fail: too quiet |
| R4 degree-preserving | 1 | 1,569 / 1,702 | 9 / 11 | 1 / 1 | 23 / 17 (3.6) | fail: too quiet |
| R4 degree-preserving | 1.2 | 2,995 / 3,508 | 11 / 14 | 1 / 1 | 23 / 17 (3.7) | fail: too quiet |
| R4 degree-preserving | 1.3 | 4,088 / 5,026 | 11 / 19 | 1 / 1 | 24 / 19 (4.4) | fail: too quiet |
| R4 degree-preserving | 1.5 | 9,275 / 14,342 | 21 / 35 | 2 / 8 | 24 / 18 (4.2) | fail: too quiet |
| R4 degree-preserving | 1.6 | 233,977 / 2,125,070 | 2 / 7 | 2 / 1395 | 13 / 7 (5.0) | fail: no signal, runaway |
| R5 random | 0.47 | 265 / 227 | 0 / 0 | 0 / 0 | 1 / 1 (2.0) | fail: no signal, too quiet |
| R5 random | 0.6 | 451 / 404 | 0 / 0 | 0 / 0 | 0 / 0 (2.6) | fail: no signal, too quiet |
| R5 random | 0.8 | 781 / 707 | 0 / 0 | 1 / 1 | 1 / 1 (3.0) | fail: no signal, too quiet |
| R5 random | 1 | 1,347 / 1,262 | 0 / 0 | 1 / 1 | 2 / 1 (3.7) | fail: no signal, too quiet |
| R5 random | 1.5 | 4,279 / 4,116 | 2 / 2 | 1 / 1 | 11 / 4 (4.1) | fail: too quiet |
| R5 random | 2 | 11,998 / 11,209 | 7 / 8 | 4 / 4 | 15 / 15 (3.9) | pass |

What it shows:
- R0, R1, R2 and R3 pass at 0.47 with 30 brains (31 to 50 lateralised outputs against null maxima of 4 to 13).
- R3.5 fails at every one of the nine scales run. The fine scan finds a scale inside the rate window (0.50: 15,300
  and 16,300 spikes/s, about three quarters of the real rate) and there it carries no left/right signal: 1 output
  per probe, while the null reaches 160 because single brains burst. Below 0.6 it never beats the null on both
  probes (the haltere probe alone does at 0.47 and 0.56, by 3 against 1 and 9 against 8). From 0.6 both probes
  beat the null, at 5.4 times the real rate or more. Between 0.47 and 0.6 the rate goes from 2,800 to 117,000.
- R4 carries a signal at every scale from 0.6 to 1.5 (3 to 35 outputs, null at most 8) but stays below the rate
  window (9,300 on the VS probe at 1.5), and at 1.6 it runs away (234,000 and 2.1 million spikes/s, no signal on
  the VS probe). None of the scales run puts it inside the window on both probes; the crossing lies between 1.5
  and 1.6. The 2.0 cell has only its VS probe (8.05 million spikes/s, 8 outputs against a null maximum of 14;
  `logs/pretest-37936.out`, cancelled during the haltere probe), so it is not in the table.
- R5 (random targets) passes at 2.0: 12,000 and 11,200 spikes/s, 7 and 8 lateralised outputs against a null
  maximum of 4. The signal is weak (the real wiring has 38 and 39), but it contradicts the draft preregistration's
  prediction that R5 fails at every scale.

### R4 in closed loop: the upright pre-test under-drives the network

`ride-rung.sbatch` at scale 1.5 (job 37943, cancelled) replays the reference decoder before the search. In that
replay every R4 brain went from about 10,000 to 4 million spikes/s within a second of setting off (first reached
at 0.49 to 0.96 s, median 0.58 s), each before its own bike fell; 13 of the 16 had reached it before the first fall
at 0.72 s (`results/rungs/r4_s1_w1.5_cpu/v4.5_s201/ride_slow_mu_trace.json`). The same replay was then run at
1.0 to 1.4 (16 riders, job 37944, `logs/r4-stability-37944.out`; those traces are not in the repository, their
summary is `results/rungs/closed_loop_rates.json`, made by `tools/replay_rate.py`):

| Brain, synapse scale | First 0.6 s of riding, spikes/s per brain | Relative to the real wiring | Whole replay (its length) | First fall |
|---|---|---|---|---|
| R0 real wiring, 0.47 | 23,388 | 1.00 | 59,098 (20.00 s) | 2.26 s |
| R3, 0.47 | 17,252 | 0.74 | 61,004 (18.50 s) | 1.75 s |
| R4, 1.0 | 12,720 | 0.54 | 16,289 (0.72 s) | 0.60 s |
| R4, 1.2 | 39,396 | 1.68 | 48,094 (0.70 s) | 0.54 s |
| R4, 1.2 (ride job 37945) | 38,723 | 1.66 | 90,759 (1.14 s) | 0.48 s |
| R4, 1.3 | 79,613 | 3.40 | 167,442 (1.02 s) | 0.55 s |
| R4, 1.4 | 326,775 | 13.97 | 1,609,072 (1.39 s) | 0.75 s |
| R4, 1.5 (ride job 37943) | 1,233,955 | 52.76 | 2,487,027 (1.14 s) | 0.72 s |

- The replay's own summary rate ("whole replay") averages every brain until the last rider has fallen, fallen
  riders included, so it grows with the length of the replay and is not comparable between rows: R4 at 1.2 reads
  48,094 in the scan (0.70 s) and 90,759 in the ride job (1.14 s), while over the first 0.6 s the two runs agree
  (39,396 and 38,723). The first 0.6 s, when nearly every rider is still up, is the comparable window.
- Upright, before the bike moves, the real wiring fires 10,000 to 12,800 spikes/s per brain (warm-up lines of
  `logs/ride-gate-3749*.out`) and R4 fires 1,207, 2,543, 3,644, 5,354 and 8,980 at 1.0 to 1.5. So the first 0.6 s
  of riding roughly doubles the real wiring's rate and multiplies R4's by 10 to 22 at 1.0 to 1.3. The upright
  pre-test does not tell whether a rung is stable while riding.
- 1.2 is the highest scanned scale within 2x of the real rate on that window (1.7 times), and the R4 pilot ride
  uses it. The search itself runs hotter than that: R4 at 1.2 averages 173,000 to 212,000 spikes/s per brain in
  generations 0 to 3 (`logs/ride-rung-37945.out`), against 68,800 and 59,500 for the real wiring in generations
  0 and 1 (`results/gate/v4.5_s201/cem.json`), about 3 times, because most of an early generation is spent on
  bikes that have already fallen and whose senses are saturated. No scale has been shown to match the real
  brain's rate throughout a generation.

### Pilot rides on rewired brains (CPU; R3 in progress, table as of 2026-11-05 14:50)

The balance gate unchanged (`ride-rung.sbatch`: the hand-picked `lane` readout, CEM from a blank decoder, 48 riders
x 15 s, 4.5 m/s, 5 N·m gusts) on rewiring draw 1. R3 at scale 0.47 with CEM seeds 201 (jobs 37938, 37946, 37949)
and 202 (jobs 37948, 37952, 37953); R4 at scale 1.2 with seed 201 (job 37945). They run on CPU at 30 to 75 min
per generation; each job stops after 22 h and the next one continues the search (`--resume`), up to 60
generations. `python3 tools/ride_table.py` prints the table; mean riding time in seconds:

| Generation | R0 seed 201 | R0 seed 202 | r3_s1_cpu seed 201 | r3_s1_cpu seed 202 | r4_s1_w1.2_cpu seed 201 |
|---|---|---|---|---|---|
| 0 | 1.01 | 0.87 | 0.97 | 0.95 | 0.76 |
| 1 | 1.45 | 1.14 | 1.32 | 1.46 | 0.56 |
| 2 | 3.18 | 1.82 | 2.18 | 2.12 | 0.65 |
| 3 | 5.42 | 3.11 | 3.24 | 3.50 | 0.68 |
| 5 | 6.83 | 4.93 | 4.46 | 5.88 | 0.74 |
| 8 | 8.94 | 7.30 | 6.23 |  | 1.35 |
| 10 | 9.03 | 10.07 | 7.04 |  | 1.45 |
| 15 | 10.95 | 9.22 |  |  | 1.58 |
| 20 | 10.98 | 9.39 |  |  | 1.73 |
| 24 | 10.46 | 11.74 |  |  | 1.69 |
| 25 | 10.75 | 10.87 |  |  |  |
| 30 | 11.77 | 12.23 |  |  |  |
| 35 | 11.83 | 10.97 |  |  |  |
| 40 | 10.99 | 12.53 |  |  |  |
| 45 | 13.35 | 11.69 |  |  |  |
| 50 | 13.68 | 12.37 |  |  |  |
| 55 | 12.55 | 10.89 |  |  |  |
| 56 | 13.15 | 11.89 |  |  |  |
| 57 | 13.71 |  |  |  |  |
| generations done | 58 | 57 | 11 | 6 | 25 |
| finishing 15 s, last generation | 77% | 52% | 2% | 4% | 0% |
| spikes/s per brain, last generation | 35,727 | 38,101 | 47,176 | 52,749 | 90,007 |
| device | cuda | cuda | cpu | cpu | cpu |

Reading so far, one rewiring draw and early generations only:
- R3 learns to ride. Both blank decoders start at the real wiring's level (0.95 to 0.97 s). Seed 201 is at 7.0 s
  after generation 10, where the real wiring's two seeds were at 9.0 and 10.1 s (70 to 78% of them); it passed
  the hands-off bike (5.7 s) in generation 8 and had its first full 15 s rides in generation 7. Seed 202 is at
  5.9 s after generation 5, inside the real wiring's range there (6.8 and 4.9 s).
- R4 at 1.2 did not learn in 25 generations: 0.76 s at generation 0, 0.56 s at generation 1, then 1.25 to 1.84 s
  from generation 8 on (1.69 s at generation 24), where the real wiring was at about 10 s. No rider rode the full
  15 s; the longest single ride was 8.2 s. That is below the hands-off bike: with this readout a searched decoder
  on R4 steers the bike into a fall sooner than no steering does. Its network ran at 86,000 to 212,000 spikes/s
  per brain (the real wiring: 36,000 to 69,000). Job 37945 was cancelled at that point (2026-11-05 14:07) to free
  CPU cores for another project; `results/rungs/r4_s1_w1.2_cpu/v4.5_s201/cem.json` holds the search state and the
  same `ride-rung.sbatch` command continues it.
- These are pilots: they started before the preregistration was tagged, with the hand-picked readout, on one
  rewiring draw. A CPU run does not repeat a GPU run (see "GPU runs do not repeat exactly"), so the comparison with
  the real wiring's GPU runs is between samples, not between identical noise.

## Rewired brains: transmission pre-test (Scrambled Brains pilot)

`brain/variants.py` rewires the connectome. R4 shuffles every connection's target, which keeps each neuron's
out-degree, in-degree, transmitter and total output synapses. It does not keep a neuron's input synapses or its
excitatory/inhibitory input mix. R5 picks each target at random and keeps out-degree, transmitter and output
synapses. Duplicate targets are merged and their synapse counts summed: 0.34% of connections in R4 and 0.13% in
R5. Total synapses are unchanged. With seed 1, 0.58% (R4) and 0.27% (R5) of the real connections survive.

`runs/pretest.py` holds the bike upright at 4.5 m/s with every sensory population at cruise rate. It adds 30 Hz
to the left VS or haltere input in 4 brains and to the right in 4 others: 300 ms of warm-up, then 1 s.
- "Network" counts only neurons outside the 789 driven sensory neurons.
- "Lateralised outputs" counts descending and motor neurons (2,129) whose left-vs-right difference has |z| > 3.
  z uses a Welch SE with ddof=1 and a floor of 1 spike per window.
- "Null" repeats the count over the balanced relabellings that put half of the left-probed and half of the
  right-probed brains in each group, so the probe side cancels: all 18 of them with 8 brains; with 30 brains
  19.3 million exist, so `--null-splits` (default 1,000) random ones are used and the 95th percentile is stored
  alongside the max.

Runs were on CPU on 2026-10-29 with no job id (`logs/local/pretest-*-w*.out`, `results/rungs/pretest_*_w*.json`).
This is one rewiring seed and 8 brains per cell; treat it as a pilot.

Each cell: network spikes/s (network neurons firing), VS probe; lateralised outputs VS / haltere (largest null
mean); largest |z| VS / haltere (largest null).

| Synapse scale | 0.47 (calibrated) | 0.60 | 0.80 | 1.0 | 1.5 |
|---|---|---|---|---|---|
| R0 real wiring | 21,500 (1,550); 28 / 18 (0.9); 37 / 16 (5) | 65,400 (3,330); 28 / 23 (1.9); 42 / 16 (5) | 310,000 (15,900); 18 / 28 (4.8); 37 / 23 (5) | 684,000 (19,200); 33 / 25 (29.4); 32 / 8 (155): runaway, null as large as the signal | 1,650,000 (23,600); 83 / 51 (6.4); 34 / 14 (6) |
| R4 degree-preserving | 262 (80); 1 / 1 (0.0); 5 / 4 (2) | 444 (178); 2 / 1 (0.1); 7 / 8 (4) | 805 (411); 5 / 6 (0.0); 8 / 9 (2) | 1,550 (910); 7 / 10 (0.0); 13 / 12 (2) | 9,960 (7,470); 14 / 17 (0.3); 13 / 15 (4) |
| R5 random | 251 (79); 0 / 0 (0.0); 0 / 0 (2) | 438 (182); 0 / 0 (0.1); 0 / 0 (4) | 772 (380); 0 / 0 (0.0); 0 / 0 (3) | 1,340 (694); 0 / 0 (0.0); 1 / 1 (2) | 4,250 (2,060); 2 / 0 (0.1); 6 / 2 (4) |

The haltere probe gives network activity within about 40% of the VS values. At R4 scale 1.5 it gives 13,900
spikes/s from 9,920 neurons.

What it shows:
- At the calibrated scale both rewired brains are close to silent, about 1% of the real network activity, with
  at most one lateralised output.
- R4 needs about three times the synaptic weight (scale 1.5) to reach 46% (VS) to 63% (haltere) of the real
  brain's calibrated activity and 14-17 lateralised outputs (real: 18-28). That activity is spread over 5-6
  times as many neurons.
- R5 stays near chance at every scale tested.

The likely cause is lost convergence. Neurons that receive 200 or more synapses from the 789 driven sensory
neurons number 417 in the real wiring, 26 in R4 and 23 in R5; the largest such input falls from 2,143 synapses to
about 500. The planned pre-test range of 0.35-0.60 (`docs/GLOSSARY.md` section 7) is too narrow for these rungs.
Only 0.47 and 0.60 were tested in that range.

## Replays on the 3D and open-loop pages

`ride-page.sbatch`, last run job 36626: 16 riders x 20 s, seed 7, 5.5 m/s, 5 Nm gusts, no cut-off.

| Claim | Value | Source | Status |
|---|---|---|---|
| Final decoder (CEM population mean), `/ride/3d` | all 16 upright for 20 s; on the road 19.2 s on average; 12 of 16 the whole time | `results/ride_road_trace.json`; `README.md:47-48`; `fly_brain/bike/README.md:191-193` | current |
| Same brains hands-off, `/ride/open-loop` | all 16 upright, at 5.4 m/s; on the road 5.1 s on average; 0 of 16 the whole time; mean final distance from the center line 42.8 m | `results/ride_pilot_road_trace.json`; `fly_brain/bike/README.md:193-194` | current |
| Round-2 decoder replayed on the new simulator | 10.0 s upright at scale 0.47, 57,000 spikes/s (job 36540); 12.1 s at 0.45, 49,000 spikes/s (job 36542) | `fly_brain/bike/README.md:42-45`; `logs/rewrite/ride-replay-*.out` | current |
| Same replay on the earlier simulator | 18.1 s upright, 11.6 s on the road, 4 of 16 the whole time, 71,000 spikes/s | `fly_brain/bike/README.md:42-45, 193, 236` (job 36494) | old simulator, not re-run |

## Passenger screen and probe

| Claim | Value | Source | Status |
|---|---|---|---|
| Walking command DNs stay silent; MDN fires without following the lean | MDN 5-19 Hz, abs(r) < 0.02 | `results/screen.json` (job 36089); `fly_brain/bike/README.md:55-56` | old simulator, not re-run |
| Flight-steering DNs track roll rate, opposite sign left and right ("the fly steers the bike with its flight-stabilisation reflex") | abs(r) up to 0.78 (DNp20_R 0.783) | `results/screen.json`; `fly_brain/bike/README.md:57-61`; `README.md:41-43` | old simulator, not re-run. The top-level `README.md` states it without this caveat |
| Neuron lists the current decoder reads (`ROLL_RATE_DNS`, `LEAN_DNS`, `LANE_DNS`) | 42 types | `bike/readout.py:19-29` | old simulator, not re-run: chosen by the old screen and probe, still read by the current decoder. Only the lane-filter weights were remade (`results/relearn/probe.json`, job 36543) |
| Odor goal saturates the brain | APL 436 Hz, ~500,000 spikes/s; ~35,000 spikes/s without the odor | `fly_brain/bike/README.md:62-64`; `logs/inline/36088.py` (job 36088) | old simulator, not re-run |
| Balance neurons carry no heading | r_psi about -0.85 r_phi_dot | `results/screen_lane_psi.json`, `results/screen_physio.json` (jobs 36110, 36111) | old simulator, not re-run |
| A separate yaw/lane channel (DNa16, DNb03, DNa06, DNp15, ...) | | `results/probe.json` (job 36112); `fly_brain/bike/README.md:96-99` | old simulator, not re-run |

## Lane keeping, rounds 1 and 2

| Claim | Value | Source | Status |
|---|---|---|---|
| Lane-gain sweep, 48 x 15 s | hands-off 5.0 s, 0%; gain 0: 4.7 s, 2%; -0.29 (learned): 8.4 s, 17%; -0.5: 6.8 s, 6%; -1 / -2 / -4: 3.7 / 1.7 / 0.8 s; +1: 1.2 s | `results/sweep/` (job 36128); `fly_brain/bike/README.md:109-116` | old simulator, not re-run |
| Round-1 final decoder, 16 x 20 s | 9.1 s on the road, 2 of 16 the whole time | `results/ride_slow_mu_trace.json` (job 36129) | old simulator, not re-run |
| Round-1 hands-off comparison | 5.4 s | `fly_brain/bike/README.md:119` | old simulator, not re-run; no committed trace gives 5.4 s (the nearest give 4.9 and 5.0 s) |
| DAgger imitation of the PD rider | ~4.5 s upright | `results/ride_dagger.json` (job 36107) | old simulator, not re-run |
| Round 2, seed-31 paired replays | 8.46 / 8.88 / 7.35 s vs 8.69 s | `results/lane/c31_*.log` (job 36493) | old simulator, not re-run |
| Round-2 CEM | 96 riders x 12 s, 22 generations, 135 min; lane gain -0.34 | `results/lane/cem_mu.json` (job 36493) | old simulator, not re-run |
| Round-2 held-out test, seed 59, 48 x 15 s | 8.45 / 9.95 / 11.32 s; 9 / 12 / 21 of 48 for all 15 s; +2.87 s (paired SE 0.76) | `results/lane/v59_*.log` (job 36493); `fly_brain/bike/README.md:149-157` | old simulator, not re-run |

## Everything else

| Claim | Value | Source | Status |
|---|---|---|---|
| Learn-from-blank on the earlier simulator | 35 generations, 1,680 attempts, 29 of 48 finishing at the end, 580 finished overall | `fly_brain/bike/README.md:196-197` (job 36521) | old simulator, not re-run (recordings not kept) |
| `ride.json`, `ride_b.json`, `ride_lane.json`, `ride_road*.json`, `ride_easy*.json`, `ride_slow*.json`, `ride_fast.json`, `ride_filter.json`, `ride_lanedn*.json`, `ride_dagger.json`, `ride_pilot_trace.json`, `zero_theta.json`, `dagger_smoke.json` and their traces | | jobs 36085-36129 and 36487 (2026-09-27 to 10-03) | old simulator, not re-run. `JOBS.md` still calls `ride_b.json` "the best decoder" and "the /ride/ demo" |

Pages on fly-brain-bike.vercel.app (`site/build.sh`): `/ride/`, `/ride/3d`, `/ride/charts`, `/ride/open-loop` and
`/dashboard/` show current runs; `/ride/oracle` has no brain. The landing page's ride numbers are current and its
speed line is from the earlier simulator.

## GPU runs do not repeat exactly

The engine adds synaptic input with `index_add_` (`brain/engine.py:116`). On a GPU those additions happen in no
fixed order, so floating-point sums differ in the last bits, a neuron close to threshold fires one step earlier or
later, and two runs drift apart. The seed fixes the Poisson draws and the gusts, not the summation order. Jobs
36543 and 36555 ran the same search with the same seed: both ended with 35 of 48 finishing, but with 885 and 836
finished attempts overall (`fly_brain/bike/README.md:186-188`). A CPU run does not reproduce a GPU run either,
since the random streams differ by device: the same seed-7 hands-off replay gave 11.7 s upright on CPU (job 36490)
and 12.3 s on GPU (job 36487), on the earlier simulator.

So one run is one sample. Compare conditions over several seeds and report the spread, and quote any single-run
number with its job id.

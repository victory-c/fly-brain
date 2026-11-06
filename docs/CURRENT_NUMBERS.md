# Which numbers are current

The simulator was rewritten on 2026-10-04. The new engine (`fly_brain/brain/engine.py`, first committed in
`0588bd1`) follows two Brian2 rules that the earlier port missed: neurons driven by Poisson input have no
refractory period, and input that reaches a refractory neuron is dropped. The synaptic weight scale also moved
from 0.45 to 0.47. The two rules lower the brain's activity (the higher scale wins part of it back), so decoders
fitted on the earlier simulator do not carry over. The learning-from-blank run was repeated on the new simulator;
the two lane-keeping rounds were not, and the original passenger screen (`results/screen.json`, job 36089: 16
riders x 8 s) was not repeated with its settings (`fly_brain/bike/README.md`, "Simulator change"). A new, larger
screen on the current simulator was run for the Scrambled Brains readouts on 2026-11-05 (job 38035,
`results/rungs/screens/r0.json`: 48 riders x 15 s at 4.0 m/s, 25 N·m gusts, seed 1); see "Readout pilot on the
real wiring".

## Rule of thumb for quoting numbers

- A bike result that involves the brain is current only if it comes from the learn-from-blank run (job 36555,
  `results/relearn/`) or its replays (job 36626: `results/ride_road_trace.json`,
  `results/ride_pilot_road_trace.json`).
  The original passenger screen (`results/screen.json`), the "flight-stabilisation reflex" finding, both lane-keeping rounds, the gain sweep and
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
| Balance-gate generation on CPU with the C kernel | On 32 threads, 436 to 504 s for R3 seed 201 (generations 18 to 59, job 38043) and 507 to 1,127 s for R3 seed 202 (generations 10 to 59, job 37952; generation 36 took 1,127 s), and 681 s and 705 s on 48 threads (seed 201, generations 14 and 15), against 3,590 to 4,303 s with the torch ops (riders up 7 to 13 s in the C-kernel generations, 4 to 9 s in the torch ones). The step is bound by memory traffic, so 48 threads are no faster than 32 and the time depends on what else the node runs (seed 202 shared it with one to three other 16- to 48-thread jobs throughout): seed 201 took 2,802 s for generation 16 while a 16-thread screen shared its socket and 1,064 s for generation 17, and seed 202 took 1,502 s for generation 9 | `logs/ride-rung-37946.out`, `-37949.out`, `-37952.out`, `-38043.out`, `-37938.out`, `-37948.out` |
| Passenger screen on CPU with the C kernel, 48 riders x 15 s, 16 threads | about 12 min a rung (R0, R1, R2, R3) | `logs/screen-rungs-38035.out` |

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
Generation 0 is the blank decoder plus the search's first random spread. It is not a hands-off replay; the
hands-off replays at these speeds are in the table below (`results/gate/v4.*_s201/handsoff_trace.json`).

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

The 4.5 m/s floor was replayed again on 2026-11-06 with 48 riders (job 38084): 5.38 s, 41 left the road and 7
fell, none rode all 15 s. Without the off-road rule the same bike lasts 8.65 s and 46 of 48 fall (job 38082), so
the rule shortens the hands-off ride but the bike falls either way. See "Replays with and without the off-road
rule" below. The two replays are different samples of the same condition; the documents keep quoting 5.7 s as
the hands-off level.

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
When this pre-test ran, the balance gate had not run on R1-R3.5; the tables below are R0, R4 and R5 only. R3 has
since been ridden on CPU ("Pilot rides on rewired brains" below); the R1 ride started on 2026-11-06 04:20 (job
38038) and the R2 ride (job 38039) follows the readout pilots.

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

### Pilot rides on rewired brains (CPU; both R3 seeds finished; table as of 2026-11-06 04:50)

The balance gate unchanged (`ride-rung.sbatch`: the hand-picked `lane` readout, CEM from a blank decoder, 48 riders
x 15 s, 4.5 m/s, 5 N·m gusts) on rewiring draw 1. R3 at scale 0.47 with CEM seeds 201 (jobs 37938, 37946, 37949,
38043; 60 generations in 19.0 h of search) and 202 (jobs 37948, 37952, 37953; 60 generations in 20.4 h); R4 at scale 1.2 with seed 201 (job
37945). They run on CPU: R3 took 23 to 83 min per generation at first and 7 to 19 min with the C kernel (except
generation 9 of seed 202, 1,502 s, and generation 16 of seed 201, 2,802 s, right after the switch; see the timing
rows above); R4, whose riders fall early, took 4 to 33 min per generation, all before the C kernel. Each job stops
after 22 h and the next one continues the search (`--resume`), up to 60 generations. `python3 tools/ride_table.py`
prints the table (it also lists the readout pilots under `results/rungs/r0/` and the R1 ride that started on
2026-11-06, left out here); mean riding time
in seconds:

| Generation | R0 seed 201 | R0 seed 202 | r3_s1_cpu seed 201 | r3_s1_cpu seed 202 | r4_s1_w1.2_cpu seed 201 |
|---|---|---|---|---|---|
| 0 | 1.01 | 0.87 | 0.97 | 0.95 | 0.76 |
| 1 | 1.45 | 1.14 | 1.32 | 1.46 | 0.56 |
| 2 | 3.18 | 1.82 | 2.18 | 2.12 | 0.65 |
| 3 | 5.42 | 3.11 | 3.24 | 3.50 | 0.68 |
| 5 | 6.83 | 4.93 | 4.46 | 5.88 | 0.74 |
| 6 | 7.48 | 6.99 | 5.08 | 6.35 | 0.79 |
| 8 | 8.94 | 7.30 | 6.23 | 9.08 | 1.35 |
| 10 | 9.03 | 10.07 | 7.04 | 9.80 | 1.45 |
| 15 | 10.95 | 9.22 | 6.89 | 8.27 | 1.58 |
| 20 | 10.98 | 9.39 | 8.16 | 10.73 | 1.73 |
| 24 | 10.46 | 11.74 | 8.94 | 10.90 | 1.69 |
| 25 | 10.75 | 10.87 | 8.78 | 11.57 |  |
| 29 | 9.50 | 10.77 | 9.49 | 12.15 |  |
| 30 | 11.77 | 12.23 | 8.69 | 12.30 |  |
| 35 | 11.83 | 10.97 | 10.76 | 12.08 |  |
| 40 | 10.99 | 12.53 | 9.97 | 10.41 |  |
| 45 | 13.35 | 11.69 | 10.49 | 11.63 |  |
| 50 | 13.68 | 12.37 | 11.26 | 11.63 |  |
| 55 | 12.55 | 10.89 | 11.22 | 11.66 |  |
| 56 | 13.15 | 11.89 | 12.39 | 12.18 |  |
| 57 | 13.71 |  | 10.29 | 12.28 |  |
| 59 |  |  | 11.48 | 11.14 |  |
| generations done | 58 | 57 | 60 | 60 | 25 |
| finishing 15 s, last generation | 77% | 52% | 42% | 52% | 0% |
| spikes/s per brain, last generation | 35,727 | 38,101 | 36,050 | 43,228 | 90,007 |
| device | cuda | cuda | cpu | cpu | cpu |

Reading on 2026-11-06, one rewiring draw:
- R3 learns to ride. Both blank decoders start at the real wiring's level (0.95 to 0.97 s). Seed 201 reached the
  hands-off bike's level in generation 7 (5.71 s against 5.69 s), when it also had its first full 15 s ride (1 of
  48), and was clearly above it from generation 8 (6.23 s). It trails the real
  wiring through the middle of the search (8.7 s at generation 30, where the real wiring's seeds were at 11.8 and
  12.2 s) and closes most of the gap by the end: 11.48 s in its last generation (59) with 42% of riders finishing,
  against 13.71 s (77%) and 11.89 s (52%) in the last generations of the real wiring's two seeds. That is 10% below
  the real wiring's mean (12.80 s) and 16% below the same CEM seed. Averaged over each search's last five
  generations: R3 11.31 s, the real wiring 13.37 and 11.38 s. The real wiring's two seeds differ by 1.82 s in the
  last generation, more than R3 differs from their mean (1.32 s).
- R3 seed 202 finished on 2026-11-06 04:48 (job 37952; job 37953 found the 60 generations done and stopped):
  11.14 s in its last generation with 52% of riders finishing, against 11.89 s (52%) for the real wiring's seed
  202 in its last generation (56), 6% below it and 13% below the real wiring's mean. The sign of that 6% is not
  robust: at generation 56 R3's seed 202 rode 12.18 s, and over each search's last five generations it is 4%
  above the real wiring's seed 202 (11.79 against 11.38 s). It reached the hands-off
  level in generation 5 (5.88 s) and from generation 30 to 40 rode 10.4 to 12.4 s, where the real wiring's two
  seeds rode 11.0 to 12.7 s. Averaged over its last five generations: 11.79 s.
- The two R3 seeds together: 11.31 s in the last generation (11.48 and 11.14 s), 12% below the real wiring's
  12.80 s (13.71 and 11.89 s); over each search's last five generations, 11.55 s against 12.38 s, 7% below. The
  real wiring's two seeds differ by 1.82 s in the last generation, more than the two means differ (1.49 s).
- Against the draft prediction (R3 loses under 30% of R0's riding time): in the last generation R3 loses 16% and
  6% seed by seed and 12% on the means; over the last five generations seed 201 is 15% below and seed 202 4%
  above. One rewiring draw, two CEM seeds, hand-picked readout; not the confirmatory test.
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

### Readout pilot on the real wiring: the top-8 screened neurons (CPU, 2026-11-06)

`ride-readout.sbatch 4.5 201 r0 topk 8` (job 38036; 30 generations in 3.45 h of search, 213 to 480 s each): the
balance gate's search on the real wiring at 4.5 m/s, CEM seed 201, but the decoder reads the 8 descending neurons
that R0's passenger screen (`results/rungs/screens/r0.parquet`, job 38035) ranks highest by roll-rate correlation:
DNp20 right and left, DNg46 right and left, DNp22 right and left, DNge043 left, DNb06 left. Each is read as its
deviation from the batch-mean warm-up rate, and there is no lane filter. Mean riding time in seconds
(`results/rungs/r0/top8/v4.5_s201/cem.json`), next to the gate's two searches with the hand-picked readout:

| Generation | top-8, seed 201 | riding all 15 s | hand-picked, seed 201 | hand-picked, seed 202 |
|---|---|---|---|---|
| 0 | 1.33 | 0% | 1.01 | 0.87 |
| 3 | 5.16 | 2% | 5.42 | 3.11 |
| 5 | 5.23 | 0% | 6.83 | 4.93 |
| 7 | 5.75 | 2% | 8.60 | 6.92 |
| 9 | 7.12 | 13% | 9.59 | 9.63 |
| 10 | 7.11 | 6% | 9.03 | 10.07 |
| 15 | 7.01 | 10% | 10.95 | 9.22 |
| 20 | 7.62 | 6% | 10.98 | 9.39 |
| 25 | 6.44 | 4% | 10.75 | 10.87 |
| 27 | 7.92 | 4% | 10.30 | 9.81 |
| 29 | 7.21 | 6% | 9.50 | 10.77 |

Reading, one seed:
- The search reached the hands-off level in generation 7 (5.75 s against 5.69 s) and then stayed between 5.79 and
  7.92 s (generations 19 and 27). The last generation rode 7.21 s with 3 of 48 riders finishing; no generation
  had more than 6 of 48 (generation 9). Averaged over generations 25 to 29: 7.15 s, against 9.95 and 10.64 s for
  the hand-picked readout in the same generations, about 30% below their mean (10.29 s).
- What ends the rides is the road. From generation 2 on, the riders' mean distance from the center line at the end
  of the ride is 3.2 to 3.5 m, and the off-road rule ends a ride at 3.5 m (`logs/ride-readout-38036.out`). That
  figure is the mean over all 48 riders, finishers included, so it mostly follows how many finish: the gate's
  seed 201 is at 2.7 to 3.2 m in generations 25 to 29 with 19 to 38% of its riders finishing
  (`logs/ride-gate-37492.out`), against 2 to 6% here. The gate's numbers are consistent with its failed rides
  also ending at the road edge (in generation 26, 9 of 48 finish and the mean is 3.19 m, so the other 39 average
  at least 3.1 m), but the search logs keep no per-rider outcomes, so its split between falls and road exits is
  not known. What the two readouts are shown to differ in is how many riders stay on the road for 15 s: 6%
  against 23% in generation 29.
- Replay of the search's final mean decoder (the CEM mean after generation 29, without the sampled spread, about
  0.03 to 0.045 per weight at the end of the search, that 47 of the 48 riders of a search generation carry; job 38077, 48 riders x 15 s, seed 201, the
  same options): 9.04 s upright, 7 of 48 ride all 15 s, 41 leave the road, none falls
  (`results/rungs/r0/top8/v4.5_s201/replay_mu_summary.json`, `logs/replay-r0-top8-38077.out`). The hands-off replay
  above lost 3 of 16 riders to a fall and 13 to the road; a 48-rider one lost 7 to a fall and 41 to the road (see
  "Replays with and without the off-road rule" below). The gate's decoders were not replayed this way, so the
  9.04 s has no hand-picked counterpart; compare the generation means.
- That decoder's steering weights: DNp20 right +0.218, DNp20 left -0.253, the other six between -0.056 and +0.017.
  The DNp20 pair holds 67% of the summed absolute weight.
- So eight neurons picked for roll rate are enough to keep the bike upright, and the readout does not hold the
  lane. The hand-picked readout differs in at least three ways: (a) 42 cell types pooled per side against 8 single
  neurons, and 9 of the 42 (`LANE_DNS`) were picked by the HS lane probe, not by roll rate; (b) a matched-filter
  lane signal, with the lane channel smoothed over 300 ms (`--tau-lane-ms 300`; here 40 ms throughout); (c) the
  search setup: the gate searches around a riding operating point (`--zbar`) with the roll features uncentred,
  while this run centres every feature on its warm-up rate (`--center-all`), which riding exceeds by 4 to 16 Hz
  per neuron in the replay. The replay's 41 off-road riders leave on both sides (21 and 20), so (c) is not shown
  to matter. The bypass search below uses the same set-up, and its mean decoder keeps 48 of 48 riders on the
  road; that takes (c) out of the list. This run does not separate (a) from (b); top-32 tests only whether more
  roll-rate-ranked neurons are enough.
- Next: the top-32 readout (job 38078, started 2026-11-06 08:35 when the bypass search below ended; the R2 pilot
  ride, job 38039, waits for it), 8 neurons drawn at random from the screen's pool (`randk`, job 38079, queued
  on 2026-11-06 05:12 behind the R1 ride), and the bypass with every synapse off (job 38086, see below).

### Readout pilot on the real wiring: the sensory bypass (CPU, 2026-11-06)

`ride-readout.sbatch 4.5 201 r0 bypass` (job 38037; 30 generations in 3.78 h of search, 176 to 523 s each): the
same search as the top-8 pilot above (same script, options, speed and CEM seed), but the decoder reads the ten
driven sensory populations themselves, one mean rate each: VS, HS, halteres, Johnston's organ and front-leg
proprioceptors, on each side (16 + 5 + 104 + 228 + 45 neurons on the left, 18 + 5 + 101 + 247 + 20 on the right,
789 in all). The brain still runs, at 31,700 to 36,200 spikes/s in generations 25 to 29, but nothing downstream of
the driven neurons is read. The wiring could still reach the decoder through the driven neurons themselves: they
are ordinary model neurons and receive 486,000 synapses from the rest of the brain (VS and HS cells thousands
each). The check is the same search with every synapse switched off (`ride-readout.sbatch 4.5 201 r0 bypass0`,
`runs/ride.py --no-synapses`, job 38086, started 2026-11-06 09:31, still running): after warm-up the ten
populations fire at the same rates to the printed 1 Hz, and in its first 8 generations the mean riding time is
within 0.002 s of this search's in every generation (`results/rungs/r0/bypass_nosyn/v4.5_s201/cem.json`). So far
nothing the brain does reaches the bypass decoder. Mean riding time in seconds
(`results/rungs/r0/bypass/v4.5_s201/cem.json`), next to the top-8 search and the gate's two searches with the
hand-picked readout:

| Generation | bypass, seed 201 | riding all 15 s | top-8, seed 201 | riding all 15 s | hand-picked, seed 201 | hand-picked, seed 202 |
|---|---|---|---|---|---|---|
| 0 | 1.29 | 0% | 1.33 | 0% | 1.01 | 0.87 |
| 3 | 3.96 | 0% | 5.16 | 2% | 5.42 | 3.11 |
| 5 | 5.48 | 0% | 5.23 | 0% | 6.83 | 4.93 |
| 6 | 6.01 | 2% | 5.00 | 2% | 7.48 | 6.99 |
| 7 | 6.91 | 8% | 5.75 | 2% | 8.60 | 6.92 |
| 9 | 7.10 | 13% | 7.12 | 13% | 9.59 | 9.63 |
| 10 | 7.21 | 13% | 7.11 | 6% | 9.03 | 10.07 |
| 15 | 10.65 | 44% | 7.01 | 10% | 10.95 | 9.22 |
| 20 | 11.27 | 56% | 7.62 | 6% | 10.98 | 9.39 |
| 24 | 13.82 | 77% | 6.03 | 2% | 10.46 | 11.74 |
| 25 | 12.25 | 60% | 6.44 | 4% | 10.75 | 10.87 |
| 27 | 13.15 | 75% | 7.92 | 4% | 10.30 | 9.81 |
| 29 | 13.92 | 77% | 7.21 | 6% | 9.50 | 10.77 |

Reading, one seed:
- The bypass search passed the hands-off level (5.69 s) in generation 6 and kept climbing: 10.65 s in generation
  15, 13.82 s in generation 24, 13.92 s in generation 29 with 37 of 48 riders finishing. Averaged over generations
  25 to 29: 13.18 s, against 7.15 s for top-8 and 9.95 and 10.64 s for the hand-picked readout. By the end the
  search's sampling width was within 0.005 of its floor (0.03) on all eleven steering weights.
- Replay of the search's final mean decoder (job 38081, 48 riders x 15 s, seed 201, the same options; the
  counterpart of job 38077 for top-8): all 48 riders ride the full 15 s, none falls and none leaves the road
  (`results/rungs/r0/bypass/v4.5_s201/replay_mu_summary.json`, `logs/replay-r0-bypass-38081.out`). They end
  0.48 m from the center line on average (median 0.40 m, largest 2.75 m; the road edge is at 3.5 m). In the
  search's last generation 37 of 48 finished. That generation differs from the replay in three ways: 47 of its
  48 riders carried the sampled spread (0.030 to 0.034 per weight), its mean was the one before the last update,
  and it had its own gust, start-lean and brain-noise draws. So the 11 that did not finish cannot be pinned on
  one of these; the sampled spread is the likely cause, not a shown one. Top-8 moves the same way: 3 of 48 in
  its last generation, 7 of 48 in its replay. The top-8 mean decoder replayed the same way lost 41 of 48 to the
  road.
- That decoder's steering weights, left then right: VS -0.051 / +0.317, HS -0.110 / +0.102, halteres -0.207 /
  -0.034, Johnston's organ -0.064 / +0.211, leg proprioceptors -0.071 / +0.106, bias +0.053. Four of the five
  senses get opposite signs on the two sides; the largest single weight is on the right VS population.
- Against top-8, the two runs share everything but the neurons read. Up to generation 10 they are never more
  than 1.4 s apart and each leads at times: top-8 by 1.35 s in generation 4 (5.63 against 4.28 s), the bypass by
  1.16 s in generation 7 (6.91 against 5.75 s). In generations 8 to 10 they are level (7.21 against 7.11 s in
  generation 10). After that the bypass rides on and top-8 stays where it is: 13.92 against 7.21 s in
  generation 29. So the search set-up that `ride-readout.sbatch` uses (every feature centred on its warm-up rate,
  no lane filter, 40 ms smoothing throughout) can find a decoder that stays on the road when the features carry
  the lane. In the bypass they do: the HS populations it reads are told the heading and the lane offset directly
  (`--gains hs_heading=150,hs_lane=50`). So the search set-up, difference (c) in the top-8 reading above, is no
  longer on the list of what top-8 could be missing. It leaves (a) and (b): which neurons the eight are, and how
  a lane signal is read from them. The bypass does not settle (b) for single neurons: its features are means
  over 5 to 247 neurons, and top-8 reads eight single neurons at 40 ms with no lane filter.
- Against the hand-picked readout through the brain, there is no clear order in generations 0 to 5. The bypass is
  behind both gate searches from generation 6 to 14 (7.21 s in generation 10 against 9.03 and 10.07 s), goes back
  and forth with them in generations 15 to 21, and is ahead of both from generation 22 on. Its 13.92 s and
  77% in generation 29 match what the better of the two gate searches ended on in generation 57 (13.71 s, 77%;
  that search first rode 13.5 s or more in generation 50), and the other gate search never got there (12.97 s at
  its best, 11.89 s in its last generation). The two set-ups differ (see (b) and (c) above), the gate search
  tunes 86 weights (84 steering weights, the bias and the lane-filter gain) against 11 here with the same 48
  riders per generation, and the gate ran on the GPU, so this is not a like-for-like comparison of learning
  speed. What it does show is that a linear decoder on the ten sensory rates is enough for this task.
  The preregistration draft lists the bypass as the ceiling. After 30 generations it is level with the best the
  hand-picked readout reached in 58: 13.18 s over its last five generations against 13.37 s over the better gate
  search's last five (11.38 s for the other), and 13.92 s in its best generation against 14.11 s. The one gate
  search that got there first rode 13.5 s or more in generation 50, against generation 24 here; given the
  differences above, that does not say which readout is easier to learn.

### Replays with and without the off-road rule (CPU, 2026-11-06)

Five replays at 4.5 m/s, 48 riders x 15 s, seed 201, 5 Nm gusts, each riding one fixed decoder with the options of
`ride-readout.sbatch`. "Hands-off" is the blank decoder the readout searches start from (steering weights and
bias 0, pedal held). The off-road rule (`--offroad 3.5`) ends a ride when the rider is more than 3.5 m from the
center line; without it only a fall ends a ride. Per-rider outcomes: `tools/replay_summary.py` on each trace, with
the `--offroad` the replay ran with (3.5, or 0 for the two replays without the rule).

| Decoder | Off-road rule | Upright, mean | Ride all 15 s | Leave the road | Fall | Job, summary |
|---|---|---|---|---|---|---|
| hands-off | 3.5 m | 5.38 s | 0 of 48 | 41 | 7 | 38084, `results/rungs/r0/handsoff/v4.5_s201/replay_road_summary.json` |
| hands-off | none | 8.65 s | 2 of 48 | | 46 | 38082, `results/rungs/r0/handsoff/v4.5_s201/replay_noroad_summary.json` |
| top-8, search mean | 3.5 m | 9.04 s | 7 of 48 | 41 | 0 | 38077, `results/rungs/r0/top8/v4.5_s201/replay_mu_summary.json` |
| top-8, search mean | none | 15.00 s | 48 of 48 | | 0 | 38083, `results/rungs/r0/top8/v4.5_s201/replay_mu_noroad_summary.json` |
| bypass, search mean | 3.5 m | 15.00 s | 48 of 48 | 0 | 0 | 38081, `results/rungs/r0/bypass/v4.5_s201/replay_mu_summary.json` |

- Hands-off with the rule: 5.38 s here against 5.69 s in the gate's hands-off replay (16 riders, on the login VM,
  `results/gate/v4.5_s201/handsoff_trace.json`, 3 fell and 13 left the road). The two are different samples of the
  same condition; the documents keep quoting 5.7 s as the hands-off level.
- Hands-off without the rule: the bike falls by itself. 46 of 48 riders fall, between 5.0 and 13.3 s (median
  8.0 s); the two still upright at 15 s are 3.9 and 31.9 m from the center line. So the bike with no steering
  falls even without the off-road rule. The rule only ends its rides sooner: 5.38 s upright on average instead
  of 8.65 s.
- Top-8 without the rule: every rider stays upright for the full 15 s. At the end the median distance from the
  center line over all 48 riders is 7.7 m and the largest is 30.3 m. 14 riders are within 3.5 m and 34 beyond it,
  24 on one side and 10 on the other. With the rule the same decoder lost 41 of 48 to the road and none to a
  fall. So this decoder balances every rider and holds no lane.
- The preregistration draft leaves a choice open (section 9a, point 5): give the per-brain readout a lane signal
  of its own, or score riding time without the off-road rule. Without the rule the replayed top-8 mean decoder is
  at the 15 s cap, 6.4 s above the hands-off bike scored the same way (8.65 s). That is one fixed decoder, from a
  search that had the rule on. No search has run without the rule, so the score section 5 uses (the mean of a
  search's last generation, which includes the search's random variation) is not measured without it; with the
  rule that score was below the replay by 1.1 s for the bypass (13.9 against 15.0 s) and 1.8 s for top-8 (7.2
  against 9.0 s). If a search without the rule also ends near the cap, there is no room above top-8 unless the
  rides get longer or the gusts stronger. Scored with the rule, the top-8 mean decoder rides 9.0 s in its replay
  (job 38077) and top-8 rode 7.2 s in its search's last generation, and the bypass shows that 15 s is reachable
  with the rule when the readout carries the lane.

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
| Flight-steering DNs track roll rate, opposite sign left and right ("the fly steers the bike with its flight-stabilisation reflex") | abs(r) up to 0.78 (DNp20_R 0.783) | `results/screen.json`; `fly_brain/bike/README.md:57-61`; `README.md:41-43` | old simulator for the 0.78, not re-run with the same settings. The current-simulator screen of job 38035 (48 riders x 15 s, seed 1, `results/rungs/screens/r0.json`; the original was 16 riders x 8 s, seed 0) again puts DNp20_R first among descending neurons by roll-rate correlation, with opposite signs left and right, at lower values: DNp20_R +0.65, DNp20_L -0.58; DNg46_R +0.62, DNg46_L -0.62; DNp22_R +0.60, DNp22_L -0.58. The top-level `README.md` states it without this caveat |
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

Pages on victory-c.github.io/fly-brain (`site/build.sh`; fly-brain-bike.vercel.app redirects there since 2026-11-05): `/ride/`, `/ride/3d`, `/ride/charts`, `/ride/open-loop` and
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

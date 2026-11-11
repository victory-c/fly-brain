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
- R1 (5% of neurons with flipped sign) lowers the network rate by more than a third (13,700 against 21,500
  spikes/s). With 8 brains its VS channel was noisy (15 outputs
  against a null max of 24 from one balanced split); the 30-brain confirmatory run (2026-11-03, login VM CPU,
  `logs/local/pretest-r1_s1-b30-w0.47.out`, `results/rungs/pretest_r1_s1_b30_w0.47.json`, 1,000 random balanced
  relabellings) gives 35 and 31 lateralised outputs against null maxima of 4 and 13 (95th percentile 1), at
  13,000-14,300 network spikes/s. R1 passes the transmission gate at 0.47.
When this pre-test ran, the balance gate had not run on R1-R3.5; the tables below are R0, R4 and R5 only. R3 and
R1 and R2 have since been ridden on CPU ("Pilot rides on rewired brains" below).

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

### Pilot rides on rewired brains (CPU; R1, R2 and R3 on two draws, plus a third R0 seed; table as of 2026-11-08 14:30)

The balance gate unchanged (`ride-rung.sbatch`: the hand-picked `lane` readout, CEM from a blank decoder, 48 riders
x 15 s, 4.5 m/s, 5 N·m gusts) on rewiring draw 1. R3 at scale 0.47 with CEM seeds 201 (jobs 37938, 37946, 37949,
38043; 60 generations in 19.0 h of search) and 202 (jobs 37948, 37952, 37953; 60 generations in 20.4 h); R1 at
scale 0.47 with seed 201 (job 38038; 60 generations in 7.39 h of search, 91 to 565 s each, all with the C kernel)
and, on rewiring draw 2, with seed 201 (job 38107, started 2026-11-06 14:23 when the random-8 pilot ended, finished
22:27; 60 generations in 7.99 h, 132 to 531 s each) and, on draw 1 again, with seed 202 (job 38108, started
2026-11-06 20:10 when the R2 ride ended, finished 2026-11-07 03:59; 60 generations in 7.71 h, 133 to 540 s each);
R3 on rewiring draw 2 with seed 201 (job 38134 queued 2026-11-07 13:00, ran 18:51 to 2026-11-08 03:07; 60
generations in 8.21 h, 87 to 562 s each; `results/rungs/r3_s2_cpu/`) and seed 202 (job 38154, 2026-11-08 03:10, CEM
from 03:16, to 14:13; 60 generations in 10.95 h, 137 to 1,214 s each); R2 on rewiring draw 2 with seed 201 (job
38135, queued with it, ran 18:51 to 04:25; 60 generations in 9.44 h, 207 to 1,000 s each; `results/rungs/r2_s2_cpu/`);
R2 at scale 0.47 with seed 201 (job 38039, started 2026-11-06 12:12 when the top-32 readout pilot ended, finished
20:10; 60 generations in 7.90 h of search, 112 to 533 s each, C kernel) and seed 202 (job 38125, 2026-11-07 04:27,
CEM from 04:30, to 12:08; 60 generations in 7.64 h, 120 to 501 s each); R4 at scale 1.2 with seed 201 (job 37945). The real wiring
also has a third seed, run the same way on CPU (`ride-gate.sbatch --gres=none`, job 38124, 2026-11-07 04:27, CEM
from 04:32, to 12:41; 60 generations in 8.16 h, 113 to 529 s each; `results/gate/v4.5_s203`): its two earlier seeds ran on GPU. They run on CPU: R3 took 23 to 83 min per generation at first and 7 to 19 min with the C kernel (except
generation 9 of seed 202, 1,502 s, and generation 16 of seed 201, 2,802 s, right after the switch; see the timing
rows above); R4, whose riders fall early, took 4 to 33 min per generation, all before the C kernel. Each job stops
after 22 h and the next one continues the search (`--resume`), up to 60 generations. `python3 tools/ride_table.py`
prints the table (it also lists the readout pilots under `results/rungs/r0/`, left out here); mean riding time
in seconds:

| Generation | R0 seed 201 | R0 seed 202 | R0 seed 203 | r1_s1_cpu seed 201 | r1_s1_cpu seed 202 | r1_s2_cpu seed 201 | r2_s1_cpu seed 201 | r2_s1_cpu seed 202 | r2_s2_cpu seed 201 | r3_s1_cpu seed 201 | r3_s1_cpu seed 202 | r3_s2_cpu seed 201 | r3_s2_cpu seed 202 | r4_s1_w1.2_cpu seed 201 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1.01 | 0.87 | 0.98 | 1.04 | 1.07 | 0.98 | 1.02 | 0.95 | 0.95 | 0.97 | 0.95 | 0.87 | 0.98 | 0.76 |
| 1 | 1.45 | 1.14 | 1.84 | 1.30 | 1.11 | 1.36 | 1.08 | 1.19 | 1.26 | 1.32 | 1.46 | 1.09 | 1.16 | 0.56 |
| 2 | 3.18 | 1.82 | 2.95 | 1.89 | 1.89 | 2.10 | 1.98 | 2.29 | 2.57 | 2.18 | 2.12 | 2.34 | 1.94 | 0.65 |
| 3 | 5.42 | 3.11 | 3.70 | 2.72 | 2.25 | 4.48 | 3.09 | 2.80 | 4.28 | 3.24 | 3.50 | 3.35 | 2.75 | 0.68 |
| 5 | 6.83 | 4.93 | 5.38 | 3.97 | 3.40 | 6.74 | 6.46 | 4.36 | 5.21 | 4.46 | 5.88 | 4.92 | 3.75 | 0.74 |
| 6 | 7.48 | 6.99 | 4.99 | 3.64 | 4.16 | 7.20 | 5.97 | 4.98 | 5.72 | 5.08 | 6.35 | 4.83 | 4.43 | 0.79 |
| 8 | 8.94 | 7.30 | 7.14 | 5.19 | 5.07 | 7.89 | 7.06 | 7.24 | 6.25 | 6.23 | 9.08 | 6.01 | 6.18 | 1.35 |
| 10 | 9.03 | 10.07 | 6.41 | 4.87 | 5.72 | 8.75 | 7.21 | 9.14 | 7.56 | 7.04 | 9.80 | 7.75 | 7.06 | 1.45 |
| 15 | 10.95 | 9.22 | 9.50 | 4.80 | 7.24 | 8.34 | 8.77 | 11.73 | 7.80 | 6.89 | 8.27 | 7.28 | 7.93 | 1.58 |
| 20 | 10.98 | 9.39 | 9.64 | 4.91 | 8.78 | 10.49 | 9.39 | 11.16 | 9.21 | 8.16 | 10.73 | 6.96 | 8.45 | 1.73 |
| 24 | 10.46 | 11.74 | 9.26 | 4.93 | 9.29 | 9.84 | 10.32 | 11.65 | 10.59 | 8.94 | 10.90 | 7.96 | 9.96 | 1.69 |
| 25 | 10.75 | 10.87 | 9.28 | 5.62 | 9.78 | 9.31 | 9.93 | 12.16 | 9.67 | 8.78 | 11.57 | 6.68 | 9.36 |  |
| 29 | 9.50 | 10.77 | 10.28 | 6.04 | 10.29 | 10.39 | 9.87 | 12.53 | 8.87 | 9.49 | 12.15 | 7.09 | 9.72 |  |
| 30 | 11.77 | 12.23 | 9.73 | 6.79 | 9.39 | 10.84 | 10.30 | 11.64 | 10.50 | 8.69 | 12.30 | 7.23 | 9.34 |  |
| 35 | 11.83 | 10.97 | 10.34 | 6.60 | 8.90 | 10.19 | 11.26 | 11.85 | 10.76 | 10.76 | 12.08 | 6.70 | 10.07 |  |
| 40 | 10.99 | 12.53 | 10.14 | 7.32 | 10.41 | 11.08 | 11.41 | 12.76 | 11.05 | 9.97 | 10.41 | 8.76 | 11.24 |  |
| 45 | 13.35 | 11.69 | 11.63 | 7.44 | 11.02 | 11.25 | 13.73 | 13.32 | 11.86 | 10.49 | 11.63 | 8.68 | 11.15 |  |
| 50 | 13.68 | 12.37 | 10.95 | 7.11 | 10.89 | 11.75 | 12.71 | 11.85 | 11.77 | 11.26 | 11.63 | 8.16 | 11.66 |  |
| 55 | 12.55 | 10.89 | 11.45 | 8.14 | 10.85 | 11.54 | 12.97 | 13.59 | 11.36 | 11.22 | 11.66 | 9.76 | 11.75 |  |
| 56 | 13.15 | 11.89 | 10.97 | 7.13 | 12.14 | 11.77 | 12.50 | 13.55 | 11.76 | 12.39 | 12.18 | 8.74 | 11.64 |  |
| 57 | 13.71 |  | 11.80 | 7.70 | 11.34 | 11.05 | 13.53 | 13.38 | 11.71 | 10.29 | 12.28 | 9.41 | 11.28 |  |
| 59 |  |  | 10.91 | 7.01 | 12.27 | 11.75 | 13.42 | 13.46 | 11.96 | 11.48 | 11.14 | 8.53 | 10.89 |  |
| generations done | 58 | 57 | 60 | 60 | 60 | 60 | 60 | 60 | 60 | 60 | 60 | 60 | 60 | 25 |
| finishing 15 s, last generation | 77% | 52% | 40% | 8% | 56% | 40% | 69% | 75% | 44% | 42% | 52% | 10% | 40% | 0% |
| spikes/s per brain, last generation | 35,727 | 38,101 | 38,062 | 24,358 | 22,747 | 26,903 | 39,095 | 40,526 | 48,852 | 36,050 | 43,228 | 36,783 | 51,190 | 90,007 |
| device | cuda | cuda | cpu | cpu | cpu | cpu | cpu | cpu | cpu | cpu | cpu | cpu | cpu | cpu |

Reading on 2026-11-06, one rewiring draw (two for R1):
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
- R2 finished its 60 generations on 2026-11-06 20:10 (job 38039) and rides at the real wiring's level: 13.42 s
  in its last generation with 33 of 48 riders (69%) finishing, against 13.71 s (77%) and 11.89 s (52%) for the
  real wiring's two seeds, 5% above their mean (12.80 s) and 2% below the same CEM seed. Over each search's last
  five generations: 13.02 s against 13.37 and 11.38 s (5% above their mean). Its best generation rode 13.73 s
  (generation 45); from generation 45 on it stayed between 11.87 and 13.73 s, where the real wiring's seeds rode
  10.9 to 13.7 s. It passed the hands-off level in generation 5 (6.46 s, with its first 2 full rides), trailed
  the real wiring through the middle of the search (9.5 to 12.1 s in generations 30 to 40, against 11.0 to 12.5 s)
  and caught up by generation 45. Its network rate over the last five generations is 40,200 spikes/s per brain
  (R0 37,000 and 36,200). The search ended with the lane-filter gain at -0.115 (R0: -0.117 and -0.163), its
  sampling width on the floor for 58 of 90 weights (mean 0.031, largest 0.063), and its set-up steps came out
  like R0's (`logs/ride-rung-38039.out`): the reference decoder rode 8.30 s (8.57 and 8.53 s on R0), the operating
  point comes from 11,605 on-road samples with a lane signal of +0.041 (9,922 and 9,904; +0.064 and +0.074), and
  the lane filter has 10 features. Against draft prediction 1 (R1 and R2 within one seed-SD of R0): R2 is 0.62 s
  above the real wiring's mean in the last generation, 0.5 of the two seeds' SD (1.29 s), and 0.64 s above over
  the last five (0.5 SD). On this draw and seed the R2 half of prediction 1 holds; the R1 half does on draw 2 and
  not on draw 1 (bullets below). Replays of R2's final mean decoder (jobs 38118 and 38119, table under "Replays
  with and without the off-road rule"): with the off-road rule 14.68 s, 46 of 48 finish, 2 leave the road, none
  falls; without it all 48 stay upright and all 48 end within 3.5 m of the center line (median 0.9 m, 22 on one
  side and 26 on the other), like the real wiring's two decoders (46 and 44 finish; 1 and 3 beyond 3.5 m).
- R2 with CEM seed 202 finished on 2026-11-07 12:08 (job 38125): 13.46 s in its last generation with 36 of 48
  (75%) finishing, 13.53 s over its last five generations, best 13.68 s (generation 58); it passed the hands-off
  level in generation 7 (6.17 s) and from generation 45 on stayed between 11.26 and 13.68 s. Same brain, same
  lane filter and operating point as seed 201 (identical `probe.json`), lane-filter gain -0.162. So R2's two
  seeds end 0.04 s apart (13.42 and 13.46 s): 5% above the real wiring's GPU pair (12.80 s) and 10% above its
  three-seed mean (12.17 s, next bullet), 0.9 of the three-seed SD. Replays of this decoder (jobs 38128 and
  38129): with the off-road rule 14.08 s, 43 of 48 finish, 5 leave the road, none falls; without it 47 of 48
  stay upright (1 falls) and 3 end beyond 3.5 m (median 0.7 m, 24 riders on each side).
- A third seed on the real wiring (job 38124, CEM seed 203, the gate's own script on CPU) finished on
  2026-11-07 12:41: 10.91 s in its last generation with 19 of 48 (40%) finishing, 11.11 s over its last five
  generations, best 12.20 s (generation 51); hands-off level in generation 7 (6.71 s), 10.43 to 12.20 s from
  generation 45 on. It rides below both GPU seeds (13.71 and 11.89 s). Two things differ from them besides the
  seed: the device (its set-up replay of the reference decoder rode 9.45 s on CPU against 8.57 and 8.53 s on
  GPU, so its operating point comes from 12,075 on-road samples with a lane signal of +0.336 against 9,922 and
  9,904 with +0.064 and +0.074; the lane filter is the same `results/relearn/probe.json` as theirs) and the
  generation count (60 against 58 and 57). Its lane-filter gain ended at -0.160 and its network rate at 38,750
  spikes/s per brain over the last five generations (the GPU seeds 37,000 and 36,200). With three seeds the real
  wiring's last-generation mean is 12.17 s with an SD of 1.42 s (over each search's last five generations 11.95
  and 1.23 s). Against that three-seed mean: R2's two seeds +10% and +11% (0.9 SD each), R3's -6% and -8% (0.5
  and 0.7 SD), R1's +1% and -3% for the two unstalled searches (0.1 and 0.3 SD) and -42% for the stalled one
  (3.6 SD); by rung mean R2 +10%, R3 -7%, R1 -15%. Every pilot except the stalled R1 search is within one
  three-seed SD of the real wiring, and R2 rides above every real-wiring seed but one. This CPU seed is the
  like-for-like comparison for the CPU rung rides; the percentages elsewhere in this section are against the two
  GPU seeds, as written when they were the only ones. Replays of this seed's final mean decoder (jobs 38130 and
  38131): with the off-road rule 14.26 s, 38 of 48 finish, 10 leave the road, none falls; without it all 48 stay
  upright and 5 end beyond 3.5 m (median 1.2 m, 32 riders on one side and 16 on the other). That sits between
  the GPU seeds' decoders (46 and 44 finish; 1 and 3 beyond) and R3's (22 and 28; 18 and 10).
- R1 finished its 60 generations on 2026-11-06 11:48 (job 38038) and rides far below the real wiring: 7.01 s in
  its last generation with 4 of 48 riders (8%) finishing, against 13.71 s (77%) and 11.89 s (52%) for the real
  wiring's two seeds. That is 45% below their mean (12.80 s) and 49% below the same CEM seed. Over each search's
  last five generations: 7.56 s against 13.37 and 11.38 s, 39% below their mean. Its best generation rode 8.14 s
  (generation 55). The blank decoder starts where the others do (1.04 s). From generation 8 to 27 the search
  stays between 4.36 and 5.62 s, at or below the hands-off bike (5.4 to 5.7 s), and from generation 28 on it
  rides 5.89 to 8.14 s. The first full 15 s ride is in generation 12; no generation has more than 6 of 48
  finishing (generation 58). By the end the search's sampling width was on its floor (0.03) for 52 of the 86 weights it samples
  and within 0.005 of it for 70; the mean over the 86 was 0.032 and the largest 0.052.
- R1 against R3: 38% below R3's two-seed mean in the last generation (7.01 against 11.31 s) and 35% below over
  the last five (7.56 against 11.55 s). On this draw the rung nearest the real wiring (wiring untouched, 5% of
  neurons with the wrong sign) rides worse than the rung that redraws every target within its cell type. With
  the hand-picked readout, one draw and one CEM seed, riding time is not monotonic along the ladder.
- R1's network is quieter during the search (the rate is averaged over all 48 brains for the whole generation,
  ended rides included; R1's rides end sooner): 25,400 spikes/s per brain over its last five generations, against 37,000
  and 36,200 for the real wiring and 36,400 and 44,300 for R3 (generation 0: 53,500 against 68,800 and 63,700,
  and 65,500 and 64,000). That is about 70% of the real wiring's rate; upright, the pre-test had it at 61% on the VS probe (13,000 against 21,300) and 66% on the
  haltere probe (14,300 against 21,600).
- Where this draw's sign flips fall (`tools/r1_flips.py`, `results/rungs/r1_s1_cpu/sign_flips.json`): 9,907 of
  166,700 neurons are relabelled (5.9%) and 8,584 change sign (5.1%), 5,976 from excitatory to inhibitory and
  2,608 the other way. They send 5.1% of all synapses, and the inhibitory share of synapses goes from 38.4% to
  40.2%. Of the 789 driven sensory neurons 42 change sign (5.3%): none of the 44 VS and HS cells, 8 of 205
  haltere afferents, 27 of 475 in Johnston's organ, 7 of 65 leg proprioceptors. Of the 112 neurons in the
  hand-picked readout 8 change sign, which changes what they send back into the brain and not what the decoder
  reads; 4.4% of the synapses onto those 112 come from neurons that changed sign. So the draw hit neither the
  visual input nor the readout's inputs harder than the brain as a whole. At the time why this search rode worse than R3 was not known; the second search on the same draw
  answered it (its bullet below).
- One clue is in the decoder: the R1 search ended with the lane-filter gain at +0.011, where the four searches
  on R0 and R3 ended at -0.117, -0.163, -0.149 and -0.194 (`steer:lane_filter` in each `cem.json` `mu`; every
  search starts it at 0). So R1's final decoder does not use the matched-filter lane signal; its 18 lane-type
  steering weights can still carry some. Without the off-road rule it drifts about as far as top-8, which has
  no lane filter (median 7.2 m with 35 of 48 beyond 3.5 m; top-8 7.7 m with 34). R1's set-up steps also came
  out differently (`logs/ride-rung-38038.out` against `ride-gate-37492`, `ride-gate-37494` and
  `ride-rung-37938`): the reference decoder rode 4.17 s on R1 (8.57 and 8.53 s on R0, 7.07 s on R3), the
  operating point comes from 3,969 on-road samples (9,922, 9,904 and 8,610) with a lane signal of -0.027
  (+0.064, +0.074 and +0.145), and the lane filter has 19 features (14 on R0, 13 on R3). Candidates at the time:
  the R1 brain carries less of the lane to the readout neurons, the lane filter or operating point built for
  R1 is poor, this one search seed, the lower network rate, sign errors on particular pathways. The second
  search on the same draw (seed 202, bullet below) rode 12.27 s with the same brain, the same lane filter and
  the same operating point (its `probe.json` and `zbar_mu.npy` are byte-identical to seed 201's), and draw 2
  runs at the same low rate and rode 11.75 s; so the brain, its lane filter, its operating point and the rate
  are not what held the seed-201 search at 7 s. What is left is the search itself: from the same start the two
  seeds ended on decoders that differ in 46 of 90 weights by more than 0.08 (seed 201 bias -0.245, lane-filter
  gain +0.011; seed 202 +0.043 and -0.135).
- What R1 loses is the lane, not its balance. In the search the rides end near the road edge: the riders' mean
  distance from the center line at the end of the ride is 3.0 to 3.5 m in generations 28 to 59
  (`logs/ride-rung-38038.out`; the road edge is 3.5 m; the search keeps no per-rider outcomes). The outcomes
  come from replays of each search's final mean decoder (48 riders x 15 s,
  seed 201, each search's own options; jobs 38092 to 38101, table under "Replays with and without the off-road
  rule" below). With the off-road rule R1's decoder rides 10.12 s: 10 of 48 finish, 37 leave the road, 1 falls.
  R3's two ride 12.25 and 12.73 s with 22 and 28 finishing (26 and 17 leave the road, 0 and 3 fall). The real
  wiring's two ride 14.79 and 14.52 s with 46 and 44 finishing (2 and 4 leave the road, none falls). Without the
  rule R1's decoder keeps 47 of 48 upright for the full 15 s, and 35 of those end more than 3.5 m from the center
  line (median over all 48: 7.2 m). The real wiring's two keep all 48 upright with 1 and 3 beyond 3.5 m (medians
  0.8 and 0.9 m); R3's keep 48 and 44 upright with 18 and 10 beyond (medians 2.7 and 1.9 m).
  The drift is to one side, the same side for R1 and both R3 decoders. All 35 of R1's riders beyond 3.5 m are
  on it, and 43 of its 48 riders end on it (mean signed offset -9.0 m against a mean distance of 9.2 m). On R3,
  17 of 18 and 10 of 10 of the riders beyond 3.5 m are on it, and 35 and 28 of 48 riders end on it (mean signed
  offset -3.1 and -1.6 m against mean distances of 3.9 and 2.8 m). The real wiring's riders end on both sides:
  28 and 31 of 48 on the other side, mean signed offset +0.1 and +0.2 m, with the same starts and gusts. So
  the lane loss on R3 and R1 is a net drift to one side, not scatter to both; whether the decoder, the wiring's
  left-right balance or the lane signal causes it is not tested (`result.lateral` in each
  `replay_mu_noroad_summary.json`). So on R0, R3 and R1
  nearly every rider stays upright, and what changes from rung to rung is how many stay on the road. As with the
  readout pilots, a replayed mean decoder rides longer than its search's last generation (R1 10.12 against
  7.01 s; R3 12.25 and 12.73 against 11.48 and 11.14 s; R0 14.79 and 14.52 against 13.71 and 11.89 s). The order
  R0, R3, R1 is the same in both, but the gaps are smaller on the replayed decoders: R1 is 31% below the real
  wiring (10.12 against a mean of 14.65 s) and 19% below R3 (mean 12.49 s), against 45% and 38% in the
  searches' last generation. (The R2 replays, run later, sit with the real wiring's: 14.68 s, 46 finish, 2 leave
  the road; without the rule all 48 upright and on the road, median 0.9 m.)
- Against the draft prediction 1 (R1 and R2 ride within one seed-SD of R0): the real wiring's two GPU seeds have
  an SD of 1.29 s in the last generation and 1.41 s over the last five (with the third, CPU, seed: 1.42 and
  1.23 s; the three-seed comparison is in the third-seed bullet above). R1 is 5.79 s below their mean in the last
  generation (4.5 SDs) and 4.82 s below over the last five (3.4 SDs); R2 is 0.5 SD above (bullet above), and R1
  on rewiring draw 2 is 0.8 SD below and R1 on draw 1 with CEM seed 202 is 0.4 SD below (bullets below). The
  first draw-1 pilot goes against the prediction as drafted; the other two R1 pilots are inside it. The
  prediction is written for the per-brain top-k readouts over 3 draws and 5 seeds; these are the hand-picked
  readout on two draws and two CEM seeds, on CPU against the real wiring's GPU runs.
  On 2026-11-08 the prediction was restated on the median over seeds (scrambled-brains `docs/PREREGISTRATION.md`
  section 8 and 9a.7). With the hand-picked readout the pilots' medians are R0 11.89 s (three seeds, SD 1.42),
  R1 11.75 s (three searches on two draws; the stalled search is the lowest of the three, so it only sets the
  median at the next value up, 11.75 instead of 12.01 s, where it dragged the mean down to 10.34 s) and R2
  13.44 s (two seeds). R1's median is 0.1 SD below R0's and R2's 1.1 SD above, so just outside: the median puts
  R0 at its middle seed, 11.89 s, where its mean is 12.17 s.
- Two more R1 pilots tell the rewiring draw from the search seed, same script and settings: draw 2 with CEM
  seed 201 (job 38107; `results/rungs/r1_s2_cpu/`) and draw 1 with CEM seed 202 (job 38108;
  `results/rungs/r1_s1_cpu/v4.5_s202`). Both finished and both ride near the real wiring (next two bullets).
- R1 draw 2 finished its 60 generations on 2026-11-06 22:27 (job 38107) and rides near the real wiring: 11.75 s
  in its last generation with 19 of 48 riders (40%) finishing, against 13.71 s (77%) and 11.89 s (52%) for the
  real wiring's two seeds; 8% below their mean (12.80 s), 0.8 of their seed-SD (1.29 s), and 4% above R3's
  two-seed mean (11.31 s). Over each search's last five generations: 11.51 s against 13.37 and 11.38 s (7% below
  their mean, 0.6 SD). Its best generation rode 12.06 s (generation 51), and from generation 45 on it stayed
  between 10.77 and 12.06 s. It parts from draw 1 in the first generations (4.48 against 2.72 s at generation 3,
  8.75 against 4.87 s at generation 10, 10.49 against 4.91 s at generation 20) and ends 68% above it (11.75
  against 7.01 s). Its set-up steps came out between R0's and draw 1's (`logs/ride-rung-38107.out`): the
  reference decoder rode 6.41 s (draw 1 4.17 s, R0 8.57 and 8.53 s, R3 7.07 s), the operating point comes from
  7,795 on-road samples with a lane signal of +0.216 (draw 1 3,969 and -0.027), the lane filter has 10
  features, and the search ended with the lane-filter gain at -0.135 (draw 1 +0.011; R0 -0.117 and -0.163), so
  this search did use the matched-filter lane signal. Its network rate is as low as draw 1's: 27,000 spikes/s
  per brain over the last five generations (draw 1 25,400; R0 37,000 and 36,200), so the lower rate is a
  property of R1's rewiring and not what set draw 1 apart. So on two draws with one CEM seed each, R1 rides 45% below and 8% below the real
  wiring with seed 201; the second search on draw 1 (next bullet) says the first was a bad search. Replays of
  draw 2's final mean decoder (jobs 38120 and 38121; table under "Replays with and without the off-road rule"):
  with the off-road rule 13.47 s, 29 of 48 finish, 15 leave the road, 4 fall; without it 39 of 48 are upright at
  15 s and 9 fall, 7 of the 39 end beyond 3.5 m (median over all 48: 1.3 m), and the riders beyond 3.5 m are
  mostly on the side opposite to draw 1's drift (8 against 2, counting the fallen riders' final positions). So
  draw 2's decoder holds the lane about as well as R3's (22 and 28 finish) and falls more often than any other
  replayed hand-picked decoder (9 without the rule, against 0 to 4).
- R1 draw 1 with CEM seed 202 finished its 60 generations on 2026-11-07 03:59 (job 38108) and rides near the
  real wiring: 12.27 s in its last generation with 27 of 48 riders (56%) finishing, against 13.71 s (77%) and
  11.89 s (52%) for the real wiring's two seeds; 4% below their mean (12.80 s), 0.4 of their seed-SD, 3% above
  the real wiring's own seed 202 and 8% above R3's two-seed mean. Over each search's last five generations:
  11.78 s against 13.37 and 11.38 s (5% below their mean, 0.4 SD). Its best generation rode 12.82 s (generation
  54); from generation 45 on it stayed between 10.60 and 12.82 s. Among the pilots that reach the real wiring's level it is the slowest to get going (hands-off level in
  generation 9, 6.39 s, where draw 2, R2 and R3 took 5 to 7 generations and the stalled seed-201 search 28;
  5.72 s at generation 10 where seed 201 was at 4.87 s and draw 2 at 8.75 s) and from generation 15 on it is above seed 201 in every generation (7.24 against 4.80 s at 15, 8.78
  against 4.91 s at 20, 10.41 against 7.32 s at 40), ending 75% above it (12.27 against 7.01 s). Same brain
  (`results/variants/r1_s1.npz`), same lane filter and operating point as seed 201 (the set-up steps are
  deterministic: 4.17 s reference ride, 3,969 samples, lane signal -0.027, 19 features; the two searches'
  `probe.json` and `zbar_mu.npy` are identical), and the search ended with the lane-filter gain at -0.135, the
  same value as draw 2's and in the range of R0's and R3's. Its network rate is the lowest of all: 23,400
  spikes/s per brain over the last five generations (seed 201 25,400; draw 2 27,000). So on draw 1 the two CEM
  seeds end 5.26 s apart (7.01 and 12.27 s), nearly three times the real wiring's seed-to-seed gap (1.82 s)
  and fifteen times R3's (0.34 s): the 7 s pilot was one search that stalled, not a property of the draw. Three R1 pilots now: 7.01,
  12.27 (draw 1) and 11.75 s (draw 2); their mean, 10.34 s, is 19% below the real wiring's. Replays of this
  decoder (jobs 38122 and 38123): with the off-road rule 14.73 s, 44 of 48 finish, 4 leave the road, none
  falls; without it all 48 stay upright and 47 end within 3.5 m of the center line (median 0.9 m, 22 on one
  side and 26 on the other). That is the real wiring's result (46 and 44 finish; 1 and 3 beyond 3.5 m, medians
  0.8 and 0.9 m) on the brain whose seed-201 decoder lost 37 of 48 to the road: the lane can be held on R1
  draw 1 with this readout and lane filter, and the seed-201 search did not find how. Draw 2 (`results/variants/r1_s2.npz`,
  `results/rungs/r1_s2_cpu/sign_flips.json`) changes the sign of 8,697 neurons (5.2%), among them 3 of the 34 VS
  cells, none of the 10 HS cells and 1 of the 112 readout neurons; it has not been through the pre-test.
- R3 on rewiring draw 2 (job 38134, CEM seed 201, `results/variants/r3_s2.npz` from job 38132) finished on
  2026-11-08 03:07 and rides well below draw 1: 8.53 s in its last generation with 5 of 48 (10%) finishing,
  9.29 s over its last five generations, best 9.99 s (generation 58). It passed the hands-off level in
  generation 7 (5.88 s), then sat between 6.7 and 9.0 s from generation 10 to 54; its only generations above 9 s are
  55, 57 and 58 (9.8, 9.4 and 10.0 s). That is 25% below draw 1's two-seed mean (11.31 s), 30% below the real wiring's
  three-seed mean (12.17 s; 2.6 SD) and 33% below its GPU pair (12.80 s): at the edge of prediction 2's 30%
  bound on this draw. Its decoder carries the signature of the stalled R1 search: the lane-filter gain ended at
  +0.003, so the decoder does not use the matched-filter lane signal (the nine other finished searches on R0,
  R1, R2 and R3 ended between -0.11 and -0.19; the stalled R1 search at +0.011). Its set-up
  steps look like draw 1's (reference ride 8.29 s against 7.07 s; 10,389 on-road samples with a lane signal of
  +0.347 against 8,610 and +0.145; 10 lane-filter features against 13), and its network rate is normal (38,400
  spikes/s per brain over the last five generations). Replays of this decoder (jobs 38155 and
  38156): with the off-road rule 10.97 s, 15 of 48 finish, 33 leave the road, none falls; without it all 48 stay
  upright and 32 end beyond 3.5 m (median 7.5 m), all 32 on the same side (44 of 48 riders end on it, mean
  signed offset -10.3 m). That is the stalled R1 decoder's replay almost number for number (47 upright, 35
  beyond, median 7.2 m, all on one side): balance kept, lane not held, drift to one side.
- R3 draw 2 with CEM seed 202 (job 38154, `results/rungs/r3_s2_cpu/v4.5_s202`) finished on 2026-11-08 14:13 and
  bears on whether 8.53 s was a stalled search or a worse draw: 10.89 s in its last generation with 19 of 48 (40%) finishing, 11.52 s over its last five
  generations, best 12.30 s (generation 42); hands-off level in generation 7 (6.01 s). That is 28% above the
  seed-201 search on the same draw (8.53 s), 4% below R3 draw 1's two-seed mean (11.31 s) and 11% below the real
  wiring's three-seed mean (0.9 SD). Same brain and byte-identical `probe.json` and `zbar_mu.npy` as seed 201;
  lane-filter gain -0.142. So, on this one further seed, 8.53 s looks like a second stalled search rather than a worse draw. Of the 13 finished searches
  with this readout, two ended with a lane-filter gain near zero (+0.011 and +0.003; the other eleven -0.087 to
  -0.194), and those two are the two lowest (7.01 and 8.53 s; the other eleven 10.89 to 13.71 s). Both are on
  rewired brains, 2 of 10 searches against 0 of 3 on the real wiring, which is too few to say that rewiring
  makes a search stall more often. On each of the two draws where a search stalled, the other seed rode 2.4 to
  5.3 s longer. R3 over its four searches on two draws (11.48, 11.14, 8.53, 10.89 s): median 11.02 s, 7% below
  the real wiring's median (11.89 s, 0.6 SD), inside prediction 2's 30% bound. Replays of this decoder (jobs
  38171 and 38172): with the off-road rule 13.79 s, 37 of 48 finish, 11 leave the road, none falls; without it all
  48 stay upright and 6 end beyond 3.5 m (median 0.9 m, 4 beyond on one side and 2 on the other). On the same
  brain the seed-201 decoder kept 15 of 48 on the road, with 32 beyond 3.5 m on one side.
- R2 on rewiring draw 2 (job 38135, CEM seed 201, `results/variants/r2_s2.npz` from job 38133) finished on
  2026-11-08 04:25 and rides at the real wiring's level: 11.96 s in its last generation with 21 of 48 (44%)
  finishing, 11.85 s over its last five generations, best 12.87 s (generation 44); hands-off level in
  generation 6 (5.72 s), 10.8 to 12.8 s from generation 45 on. That is 2% below the real wiring's three-seed
  mean (0.15 SD), 1% above its median, 7% below its GPU pair and 11% below R2 draw 1's two seeds (13.42 and
  13.46 s). Its decoder uses the lane signal (gain -0.087). Two things about this draw differ: its lane filter
  has only 5 features (draw 1: 10) and the set-up replay of the reference decoder rode 15.26 s while 31.8 m from
  the center line on average (every other brain 4 to 9.5 s), so the operating point came from 9,512 on-road
  samples with a lane signal of +0.021; and its network runs at 49,700 spikes/s per brain over the last five
  generations (draw 1: 40,200 and 39,700; R0 36,200 to 38,800), the highest of the finished pilots. Its
  generations took 207 to 1,000 s (the others 87 to 565 s). Replays of this decoder (jobs 38157 and 38158): with
  the off-road rule 13.35 s, 34 of 48 finish, 14 leave the road, none falls; without it all 48 stay upright and
  9 end beyond 3.5 m (median 1.6 m, 23 riders on one side and 25 on the other): between the real wiring's
  decoders (46, 44 and 38 finish) and R3 draw 1's (22 and 28). R2 on two draws and three searches: 13.42, 13.46 and 11.96 s, median 13.42 s.
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
  at least 3.1 m), but the search logs keep no per-rider outcomes, so its split between falls and road exits
  during the search is not known (replays of its final mean decoders lose 2 and 4 of 48 to the road and none to a
  fall, see "Replays with and without the off-road rule"). What the two readouts are shown to differ in is how many riders stay on the road for 15 s: 6%
  against 23% in generation 29.
- Replay of the search's final mean decoder (the CEM mean after generation 29, without the sampled spread, about
  0.03 to 0.045 per weight at the end of the search, that 47 of the 48 riders of a search generation carry; job 38077, 48 riders x 15 s, seed 201, the
  same options): 9.04 s upright, 7 of 48 ride all 15 s, 41 leave the road, none falls
  (`results/rungs/r0/top8/v4.5_s201/replay_mu_summary.json`, `logs/replay-r0-top8-38077.out`). The hands-off replay
  above lost 3 of 16 riders to a fall and 13 to the road; a 48-rider one lost 7 to a fall and 41 to the road (see
  "Replays with and without the off-road rule" below). The gate's two final mean decoders, replayed the same way
  later (jobs 38093 and 38095), ride 14.79 and 14.52 s with 46 and 44 of 48 finishing.
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
- Since then: the top-32 readout (job 38078) and the bypass with every synapse off (job 38086) have finished,
  see the two sections below. The random-8 control (`randk`, job 38079) finished at 14:23, see its section below.
  The R2 pilot ride (job 38039) finished at 20:10 and the R1 draw-2 pilot ride (job 38107) at 22:27, see "Pilot
  rides on rewired brains", and R1 draw 1 with CEM seed 202 (job 38108) at 03:59 on 2026-11-07, its replays
  (38122, 38123) at 04:14. Started 2026-11-07 04:27: a third CEM seed on the real wiring (job 38124, seed 203,
  `ride-gate.sbatch` on CPU, `results/gate/v4.5_s203`), so that the seed-SD in prediction 1 rests on three
  values instead of two, and a second seed on R2 (job 38125, seed 202, `results/rungs/r2_s1_cpu/v4.5_s202`),
  so that R2 has two seeds like R3. Both finished on 2026-11-07 (12:41 and 12:08; bullets above); the replays of
  the R0 seed-203 decoder (38130, 38131) finished at 13:10. Queued 2026-11-07 13:00 and started 18:51: pilot
  rides on a second rewiring draw of R3 (job 38134, `results/variants/r3_s2.npz` from job 38132,
  `results/rungs/r3_s2_cpu/`) and of R2 (job 38135, `results/variants/r2_s2.npz` from job 38133,
  `results/rungs/r2_s2_cpu/`), CEM seed 201, so that R2 and R3 have two draws like R1. R3 draw 2 finished at
  03:07 on 2026-11-08 (8.53 s) and R2 draw 2 at 04:25 (11.96 s), see their bullets. R3 draw 2 with seed 202
  (38154) started at 03:10; the R3 draw-2 replays (38155, 38156) finished at 04:26 and the R2 draw-2 replays
  (38157, 38158) at 04:42. R3 draw 2 with seed 202 finished at 14:13 and its replays (38171, 38172) at 14:40. Nothing of this project is running or queued.

### Readout pilot on the real wiring: the top-32 screened neurons (CPU, 2026-11-06)

`ride-readout.sbatch 4.5 201 r0 topk 32` (job 38078; 30 generations in 3.61 h of search, 246 to 537 s each): the
top-8 search above with the 32 highest-ranked neurons of the same screen in place of 8, each still read on its
own. The 32 include the top 8; the other 24 are seven DNp17, four DNpe008, two each of DNge097, DNg94, DNpe013
and DNge087, the second DNge043, and one each of DNge088, DNg90, DNpe014 and DNpe054. Mean riding time in seconds
(`results/rungs/r0/top32/v4.5_s201/cem.json`):

| Generation | top-32, seed 201 | riding all 15 s | top-8, seed 201 | riding all 15 s |
|---|---|---|---|---|
| 0 | 1.69 | 0% | 1.33 | 0% |
| 2 | 5.06 | 4% | 3.87 | 0% |
| 3 | 5.36 | 2% | 5.16 | 2% |
| 5 | 5.72 | 0% | 5.23 | 0% |
| 7 | 5.50 | 0% | 5.75 | 2% |
| 8 | 7.22 | 6% | 6.74 | 4% |
| 9 | 5.60 | 2% | 7.12 | 13% |
| 10 | 6.37 | 2% | 7.11 | 6% |
| 12 | 7.66 | 13% | 5.99 | 2% |
| 15 | 6.07 | 0% | 7.01 | 10% |
| 20 | 5.75 | 0% | 7.62 | 6% |
| 25 | 5.69 | 0% | 6.44 | 4% |
| 27 | 5.34 | 0% | 7.92 | 4% |
| 29 | 6.24 | 0% | 7.21 | 6% |

Reading, one seed:
- Four times as many roll-rate-ranked neurons do not ride longer. Top-32 reaches the hands-off level in
  generation 4 (5.88 s against 5.69 s; top-8 did in generation 7) and then stays between 5.34 and
  7.66 s. Its last generation rides 6.24 s with no rider finishing; generations 25 to 29 average 6.19 s, against
  7.15 s for top-8. Over the whole search 29 rides lasted the full 15 s (top-8: 55), none of them in the last
  three generations.
- The rides end at the road, as with top-8: from generation 3 on the riders' mean distance from the center line at
  the end of the ride is 3.27 to 3.51 m, and 3.51 m in each of the last three generations
  (`logs/ride-readout-38078.out`).
- The final mean decoder spreads its weight. The largest single weight is on one left DNp17 (+0.377, 17% of the
  summed absolute steering weight); the DNp20 pair has +0.063 (right) and -0.126 (left), 9% of the sum, where
  top-8 put 67% on that pair.
- Replays of that decoder (48 riders x 15 s, seed 201, the same options; jobs 38104 and 38105,
  `results/rungs/r0/top32/v4.5_s201/replay_mu_summary.json` and `replay_mu_noroad_summary.json`). With the
  off-road rule: 8.88 s upright, 2 of 48 ride all 15 s, 46 leave the road (37 on one side, 9 on the other), none
  falls. Without it: all 48 are upright at 15 s, 44 of them more than 3.5 m from the center line (40 on one side,
  4 on the other). Over all 48 riders the median distance from the center line is 16.5 m and the largest is
  40.9 m. So like top-8 it balances every rider and holds no lane, and it drifts further and more to one side
  than top-8 did (median over all 48 riders 7.7 m; 24 and 10 beyond 3.5 m).
- So in this search more neurons of the kind the screen ranks highest did not give a lane signal. Of the
  differences from the hand-picked readout listed under top-8, this argues against only the count in (a): 32
  single neurons ride no longer than 8 (6.19 against 7.15 s over generations 25 to 29; one seed, 30 generations,
  37 parameters against 13 for top-8). The rest of (a) remains: which neurons are read, and that each is read
  on its own, not pooled by type and side. So does (b), how a lane signal is read from them.
- What R0's screen holds about the lane (`results/rungs/screens/r0.parquet`, the pool `screen_pool` returns,
  read with pandas on the node, job 38110). The 32 neurons ranked highest by roll rate also follow the bike's
  heading (|r_psi| up to 0.53) and hardly its lateral offset (|r_y| at most 0.14, median 0.05). No neuron in
  the pool follows the lateral offset closely: the largest |r_y| is 0.29, against 0.65 for roll rate, and the
  eight highest (DNg62, DNge044, DNge012, DNge039, DNge027, DNge060) have the same sign on the left and the
  right. So ranking the same screen by lateral offset is not an obvious source of a lane signal. The hand-picked
  readout takes its lane neurons from another measurement, the HS probe (`runs/probe.py`), which every
  `ride-rung.sbatch` run already makes on its own brain.

### Readout pilot on the real wiring: 8 neurons drawn at random (CPU, 2026-11-06)

`ride-readout.sbatch 4.5 201 r0 randk 8` (job 38079; 30 generations in 2.57 h of search, 230 to 522 s each): the
top-8 search above, but the decoder reads 8 descending neurons drawn at random from the same screen's pool
(readout seed 0) in place of the 8 highest-ranked. The 8 are DNp19 right, DNg41 left, DNge046 right, DNb02 right,
DNg05_a right, DNge019 left, DNg105 left and DNg49 right. This is one draw; section 5 of the preregistration
draft asks for three. Mean riding time in seconds
(`results/rungs/r0/rand8_r0/v4.5_s201/cem.json`):

| Generation | random-8, seed 201 | riding all 15 s | top-8, seed 201 | riding all 15 s |
|---|---|---|---|---|
| 0 | 1.11 | 0% | 1.33 | 0% |
| 1 | 2.64 | 0% | 2.26 | 2% |
| 3 | 3.57 | 0% | 5.16 | 2% |
| 5 | 3.46 | 0% | 5.23 | 0% |
| 10 | 4.05 | 0% | 7.11 | 6% |
| 15 | 4.17 | 0% | 7.01 | 10% |
| 20 | 4.07 | 0% | 7.62 | 6% |
| 25 | 4.00 | 0% | 6.44 | 4% |
| 27 | 4.59 | 2% | 7.92 | 4% |
| 29 | 4.06 | 0% | 7.21 | 6% |

Reading, one seed and one draw of the 8 neurons:
- The search never reaches the hands-off level (5.4 to 5.7 s). From generation 3 on it stays between 3.46 and
  4.59 s, and the last generation rides 4.06 s. Generations 25 to 29 average 4.18 s; over the same five
  generations top-8 averages 7.15 s and top-32 6.19 s. One ride in the whole search lasted the full 15 s
  (generation 27).
- The final mean decoder is close to blank: its eight steering weights are between -0.039 and +0.038 and the
  bias is +0.023, with the sampling width on or within 0.003 of its floor (0.03) on all nine. A search generation
  rides below the hands-off bike (4.06 s in generation 29), while the replay of the mean in the next bullet
  rides level with it (5.51 s). In a search generation one rider carries the mean and the other 47 carry weights
  sampled around it, with a spread (0.030 to 0.032 per weight) about as large as the weights themselves. That
  spread is the likely cause of the gap, not a shown one: the generation also used the mean from before the last
  update and had its own gust, start-lean and brain-noise draws.
- Replays of the mean decoder (48 riders x 15 s, seed 201, the same options; jobs 38111 and 38112,
  `replay_mu_summary.json` and `replay_mu_noroad_summary.json` next to the search). With the off-road rule: 5.51 s upright, none rides all 15 s, 38 leave the road, 10 fall. The hands-off bike
  replayed the same way rides 5.38 s; 41 leave the road and 7 fall. Without the rule all 48 fall, between 4.2
  and 12.5 s (median 7.5 s; 7.82 s on average). The hands-off bike without the rule rides 8.65 s on average and
  46 of 48 fall. The top-8 and top-32 decoders without the rule keep all 48 upright for the full 15 s.
- The draw is not a silent one. After warm-up, with the bike upright, five of the 8 fire at 0.5 Hz or more (DNg41
  left 20 Hz, DNg105 left 16, DNg49 right 8, DNg05_a right 4, DNb02 right 1; DNp19, DNge046 and DNge019 are
  below 0.5 Hz), against six of 8 for top-8 (38, 29, 22, 7, 1 and 1 Hz; the two DNp22 are below 0.5 Hz;
  `logs/ride-readout-38079.out`, `logs/ride-readout-38036.out`). These are rates before the ride starts, not
  riding rates, and they do not say whether a neuron follows the roll. The pool holds only descending neurons
  that are not driven by the senses and fired at least 0.5 Hz in the screen (`screen_pool` in
  `bike/readout.py`), so every draw comes from neurons that were active in the screen.
- So these 8 random neurons give the search nothing to balance with, and the screen's ranking does: the top-8
  and top-32 decoders balance every replayed rider. The control separates from top-k on balance; neither holds
  the lane. For prediction 3's second clause (R4 rides no better than random-k on R0), the random-k level on R0
  is below the hands-off bike in the search (4.06 s in generation 29 against 5.4 to 5.7 s) and level with it in
  the replay of the mean decoder (5.51 s against 5.38 s).

### Readout pilot on the real wiring: the sensory bypass (CPU, 2026-11-06)

`ride-readout.sbatch 4.5 201 r0 bypass` (job 38037; 30 generations in 3.78 h of search, 176 to 523 s each): the
same search as the top-8 pilot above (same script, options, speed and CEM seed), but the decoder reads the ten
driven sensory populations themselves, one mean rate each: VS, HS, halteres, Johnston's organ and front-leg
proprioceptors, on each side (16 + 5 + 104 + 228 + 45 neurons on the left, 18 + 5 + 101 + 247 + 20 on the right,
789 in all). The brain still runs, at 31,700 to 36,200 spikes/s in generations 25 to 29, but nothing downstream of
the driven neurons is read. The wiring could still reach the decoder through the driven neurons themselves: they
are ordinary model neurons and receive 486,000 synapses from the rest of the brain (VS and HS cells thousands
each). The check is the same search with every synapse switched off (`ride-readout.sbatch 4.5 201 r0 bypass0`,
`runs/ride.py --no-synapses`, job 38086; 30 generations in 2.76 h of search, 16 threads): after warm-up the ten
populations fire at the same rates to the printed 1 Hz, nothing outside the driven neurons fires, and the search
follows this one generation by generation (`results/rungs/r0/bypass_nosyn/v4.5_s201/cem.json`). Through generation
10 the two mean riding times agree to 0.0013 s; over all 30 generations they are never more than 0.085 s apart
(generation 28: 13.28 against 13.20 s). The last generation rides 13.91 s with 39 of 48 finishing, against 13.92 s
with 37 of 48 here; generations 25 to 29 average 13.20 against 13.18 s. Its final mean decoder has the same signs
on all eleven steering weights, and the largest difference between the two is 0.021 (left Johnston's organ,
-0.085 against -0.064), under the search's sampling-width floor of 0.03; the two largest weights are right VS
+0.298 against +0.317 and left halteres -0.215 against -0.207. So the bypass decoder does not need the brain's wiring: with every synapse off it rides the same.
The two searches are close but not identical, so the synapses onto the driven neurons do change some spikes,
but not the riding. Mean riding time in seconds
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

Replays at 4.5 m/s, 48 riders x 15 s, seed 201, 5 Nm gusts, each riding one fixed decoder. The off-road rule
(`--offroad 3.5`) ends a ride when the rider is more than 3.5 m from the center line; without it only a fall ends
a ride. Per-rider outcomes: `tools/replay_summary.py` on each trace, with the `--offroad` the replay ran with
(3.5, or 0 for the replays without the rule). Two groups: the readout pilots on the real wiring, with the options
of `ride-readout.sbatch`, and the final mean decoders of the hand-picked-readout searches on R0, R3, R1 and R2, each
with its own search's options (its brain, lane filter and 300 ms lane smoothing).

Readout pilots on the real wiring. "Hands-off" is the blank decoder the readout searches start from (steering
weights and bias 0, pedal held):

| Decoder | Off-road rule | Upright, mean | Ride all 15 s | Leave the road | Fall | Job, summary |
|---|---|---|---|---|---|---|
| hands-off | 3.5 m | 5.38 s | 0 of 48 | 41 | 7 | 38084, `results/rungs/r0/handsoff/v4.5_s201/replay_road_summary.json` |
| hands-off | none | 8.65 s | 2 of 48 | | 46 | 38082, `results/rungs/r0/handsoff/v4.5_s201/replay_noroad_summary.json` |
| top-8, search mean | 3.5 m | 9.04 s | 7 of 48 | 41 | 0 | 38077, `results/rungs/r0/top8/v4.5_s201/replay_mu_summary.json` |
| top-8, search mean | none | 15.00 s | 48 of 48 | | 0 | 38083, `results/rungs/r0/top8/v4.5_s201/replay_mu_noroad_summary.json` |
| bypass, search mean | 3.5 m | 15.00 s | 48 of 48 | 0 | 0 | 38081, `results/rungs/r0/bypass/v4.5_s201/replay_mu_summary.json` |
| top-32, search mean | 3.5 m | 8.88 s | 2 of 48 | 46 | 0 | 38104, `results/rungs/r0/top32/v4.5_s201/replay_mu_summary.json` |
| top-32, search mean | none | 15.00 s | 48 of 48 | | 0 | 38105, `results/rungs/r0/top32/v4.5_s201/replay_mu_noroad_summary.json` |
| random-8, search mean | 3.5 m | 5.51 s | 0 of 48 | 38 | 10 | 38111, `results/rungs/r0/rand8_r0/v4.5_s201/replay_mu_summary.json` |
| random-8, search mean | none | 7.82 s | 0 of 48 | | 48 | 38112, `results/rungs/r0/rand8_r0/v4.5_s201/replay_mu_noroad_summary.json` |

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
- Top-32 behaves like top-8: with the rule 46 of 48 leave the road and none falls; without it all 48 stay upright
  for 15 s and 44 end beyond 3.5 m (median over all 48 riders: 16.5 m from the center line).
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

The hand-picked readout on R0 (three seeds), R3 (two draws, two seeds on each), R1 (two draws, two seeds on draw 1) and R2 (two draws, two seeds on draw 1): the CEM mean after each search's last generation (jobs 38092 to 38101, 38118 to 38123, 38128 to 38131, 38155 to 38158, 38171, 38172;
summaries `replay_mu_summary.json` and `replay_mu_noroad_summary.json` next to each search's `cem.json`, under
`results/gate/v4.5_s201`, `.../v4.5_s202`, `.../v4.5_s203`, `results/rungs/r3_s1_cpu/v4.5_s201`, `.../v4.5_s202`, `results/rungs/r3_s2_cpu/v4.5_s201`, `.../v4.5_s202`,
`results/rungs/r2_s1_cpu/v4.5_s201`, `.../v4.5_s202`, `results/rungs/r2_s2_cpu/v4.5_s201`,
`results/rungs/r1_s1_cpu/v4.5_s201`, `.../v4.5_s202` and `results/rungs/r1_s2_cpu/v4.5_s201`). "Beyond 3.5 m" counts the riders still upright at 15 s that are more than
3.5 m from the center line; the median is over all 48 riders' final distance from the center line:

| Search | Last generation of the search | With the rule: upright, mean | Ride all 15 s | Leave the road | Fall | Without the rule: upright at 15 s | Fall | Beyond 3.5 m | Median distance |
|---|---|---|---|---|---|---|---|---|---|
| R0, seed 201 | 13.71 s, 77% | 14.79 s | 46 of 48 | 2 | 0 | 48 of 48 | 0 | 1 | 0.83 m |
| R0, seed 202 | 11.89 s, 52% | 14.52 s | 44 of 48 | 4 | 0 | 48 of 48 | 0 | 3 | 0.91 m |
| R3, seed 201 | 11.48 s, 42% | 12.25 s | 22 of 48 | 26 | 0 | 48 of 48 | 0 | 18 | 2.74 m |
| R3, seed 202 | 11.14 s, 52% | 12.73 s | 28 of 48 | 17 | 3 | 44 of 48 | 4 | 10 | 1.91 m |
| R1, seed 201 | 7.01 s, 8% | 10.12 s | 10 of 48 | 37 | 1 | 47 of 48 | 1 | 35 | 7.17 m |
| R2, seed 201 | 13.42 s, 69% | 14.68 s | 46 of 48 | 2 | 0 | 48 of 48 | 0 | 0 | 0.88 m |
| R2, seed 202 | 13.46 s, 75% | 14.08 s | 43 of 48 | 5 | 0 | 47 of 48 | 1 | 3 | 0.70 m |
| R0, seed 203 (CPU) | 10.91 s, 40% | 14.26 s | 38 of 48 | 10 | 0 | 48 of 48 | 0 | 5 | 1.24 m |
| R1 draw 2, seed 201 | 11.75 s, 40% | 13.47 s | 29 of 48 | 15 | 4 | 39 of 48 | 9 | 7 | 1.35 m |
| R1 draw 1, seed 202 | 12.27 s, 56% | 14.73 s | 44 of 48 | 4 | 0 | 48 of 48 | 0 | 1 | 0.89 m |
| R3 draw 2, seed 201 | 8.53 s, 10% | 10.97 s | 15 of 48 | 33 | 0 | 48 of 48 | 0 | 32 | 7.53 m |
| R3 draw 2, seed 202 | 10.89 s, 40% | 13.79 s | 37 of 48 | 11 | 0 | 48 of 48 | 0 | 6 | 0.95 m |
| R2 draw 2, seed 201 | 11.96 s, 44% | 13.35 s | 34 of 48 | 14 | 0 | 48 of 48 | 0 | 9 | 1.56 m |

- With the rule, 180 of the 188 rides that end early across the thirteen replays end at the road edge and 8 end
  in a fall (4 of the 8 on R1 draw 2). Without the rule 609 of 624 riders are upright at 15 s (9 of the 15 falls
  on R1 draw 2). These decoders balance on all four wirings, R1 draw 2's least reliably; what separates the
  decoders is how many riders ride all 15 s on the road: 46, 44 and 38 on the real wiring, 46 and 43 on R2 draw 1 and 34 on R2 draw 2, 22 and 28 on
  R3 draw 1 and 15 and 37 for the two searches on R3 draw 2, 10 and 44 for the two searches on R1 draw 1 and 29 on R1 draw 2. The two R1 draw-1 decoders span the
  whole range on the same brain, so with this readout the lane result is as much the search's as the wiring's.
- Without the rule the four wirings are within 0.5 s of each other and of the cap (15.00, 15.00 and 15.00 s;
  15.00, 14.83 and 15.00 s; 15.00, 14.63, 15.00 and 15.00 s; 14.82, 15.00 and 14.50 s). So for the open choice in the preregistration draft (section 9a, point 5), riding time
  scored without the off-road rule would not separate R0, R2, R3 and R1 with this readout at 15 s and 5 Nm: the
  difference between them is in the lane, and the rule is what scores it. One replay seed per decoder, fixed
  decoders from searches that had the rule on.
- The riders' final distance from the center line without the rule orders the wirings the same way as riding
  time with it: medians of 0.8, 0.9 and 1.2 m (R0), 0.9 and 0.7 m (R2 draw 1) and 1.6 m (R2 draw 2), 2.7 and 1.9 m (R3 draw 1) and 7.5 and 0.9 m (R3 draw 2's two searches), 7.2 and 0.9 m (R1 draw 1's two
  searches) and 1.3 m (R1 draw 2).

### Track C pilot: decoding roll rate from recorded neurons (CPU, 2026-11-08)

One replay per brain of a final CEM mean decoder (hand-picked readout, draw 1, 48 riders x 15 s, seed 201, no off-road
rule, jobs 38178 to 38181; R1 uses seed 202's decoder, because seed 201's search stalled). `runs/ride.py --counts-out` records
the spike counts of all 1,314 descending neurons and the 67 wing motor neurons in 100 ms bins; `tools/track_c.py` (job
38185, `results/track_c/<rung>.json`) fits ridge regressions to the bike's bin-mean roll rate. 7,200 samples per
brain, five folds over riders, so a test rider never trains the model; R^2 is pooled out of fold. N90 is the number of
neurons reaching 90% of a reference R^2, adding them in order of the brain's own screen (|r_phi_dot|) or in 20 random
orders. Random orders are drawn over all of the site's neurons, silent ones included, because a recording cannot pick the
active ones in advance; the medians for active neurons only are given as well.

| Brain | Site, reference | Active neurons | R^2 of the site | Target R^2 | N90, screen order | N90, random: median (25-75%) | Random, active only: median |
|---|---|---|---|---|---|---|---|
| R0 | descending | 393 of 1,314 | 0.962 | 0.866 | 3 | 277 (188-355) | 73 |
| R1 | descending | 350 | 0.927 | 0.834 | 3 | 454 (345-574) | 100.5 |
| R2 | descending | 408 | 0.964 | 0.867 | 3 | 249.5 (144-345) | 57.5 |
| R3 | descending | 371 | 0.958 | 0.863 | 3 | 297 (188-385) | 80 |
| R0 | wing motor, its own R^2 | 33 of 67 | 0.909 | 0.818 | 4 | 29.5 (24-34) | 14 |
| R1 | wing motor, its own R^2 | 31 | 0.903 | 0.812 | 4 | 37 (25-43) | 14 |
| R2 | wing motor, its own R^2 | 35 | 0.905 | 0.814 | 3 | 31 (24-35) | 13.5 |
| R3 | wing motor, its own R^2 | 40 | 0.867 | 0.780 | 6 | 35.5 (30-42) | 17.5 |
| R0 | wing motor, descending R^2 | 33 | 0.909 | 0.866 | 7 | 44 (41-50) | 18.5 |
| R1 | wing motor, descending R^2 | 31 | 0.903 | 0.834 | 4 | 39 (33-45) | 16.5 |
| R2 | wing motor, descending R^2 | 35 | 0.905 | 0.867 | 7 | 46.5 (44-53) | 22.5 |
| R3 | wing motor, descending R^2 | 40 | 0.867 | 0.863 | 29 | 64.5 (61-65) | 36 |

The roll-rate SD differs between the replays: 0.42, 0.27, 0.43 and 0.40 on R0 to R3.

- Screened neurons are far cheaper than random ones at the descending site (3 against medians of 250 to 454), and N90 at that
  site is 3 on all four brains, so with these data N90 does not separate R0 to R3.
- The wing-motor site depends on the reference. Preregistration section 7 can be read as one reference for both sites (the
  descending R^2) or as each site's own. Against its own R^2 the screened N90 is 3 to 6. Against the descending R^2 it is 4, 7, 7
  and 29; R3's wing-motor site gives only 0.867 against a target of 0.863, so its 29 sits at the edge of what that site can reach. One
  replay per brain cannot say whether R3's difference is real.
- Limits: one replay seed and one rewiring draw per brain; each brain rides under its own decoder, so the roll-rate
  statistics differ; the riders are in closed loop, so a neuron can predict roll rate because it follows the haltere input or
  because the decoder reads it and steers. No rung past R3 has a decoder to replay: R3.5 and R5 have not been ridden and the R4 pilot
  did not learn. The ridge penalty is chosen once per site. The simulated jGCaMP8 and probe-distance parts of preregistration
  section 7 are not done.

### Track B pilot: decoder-free predictions on the ladder (CPU, 2026-11-08)

`python -m runs.predictions` (jobs 38186 and 38187, `results/track_b/`): the rows of scrambled-brains
`docs/track_b_predictions_DRAFT.csv` that need no further choice, 150 Hz Poisson drive for 1 s in 30 flies at synaptic scale 0.47, taste groups on the
right side (Shiu's one labellum; the left side is below) and Johnston's-organ groups on both. With no input the network is silent, so "no stimulus" is 0 Hz. The score is the fraction of the
five signed rows whose difference has the expected sign. Differences in Hz:

| Brain | Score | Sugar to MN9 | Water to MN9 | Bitter on sugar, MN9 | Ir94e on sugar, MN9 | JO-F to MDN | Null rows: JO-C/E to MDN (Hz) |
|---|---|---|---|---|---|---|---|
| R0 | 0.6 | +22.48 | 0 | -22.48 | -22.35 | 0 | 0 |
| R1 draw 1 | 0.6 | +0.03 | 0 | -0.03 | -0.03 | 0 | 0 |
| R1 draw 2 | 0.6 | +21.90 | 0 | -21.90 | -21.40 | 0 | 0.04 |
| R2 draw 1 | 0.6 | +24.82 | 0 | -24.82 | -24.55 | 0 | 1.26 |
| R2 draw 2 | 0.6 | +12.02 | 0 | -12.02 | -12.02 | 0 | 2.82 |
| R3 draw 1 | 0.6 | +22.87 | 0 | -22.87 | -22.80 | 0 | 0.74 |
| R3 draw 2 | 0.6 | +22.52 | 0 | -22.52 | -22.35 | 0 | 0.25 |
| R3.5 | 0 | 0 | 0 | +4.50 | +0.02 | 0 | 0 |
| R4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| R5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

- The real wiring itself scores 0.6: water does not drive MN9 and JO-F does not drive MDN at these settings. Those two rows
  cannot separate rungs as they stand.
- A sign score hides magnitude. R1 draw 1 scores 0.6 with sugar driving MN9 at 0.03 Hz, about 700 times below the real wiring (R1 draw 2: 21.9 Hz), and its
  suppression rows pass on that one-in-a-few-spikes response. This row-by-row sign score is the one section 6 of the preregistration defines.
- R4 and R5 score 0 with every readout at 0 Hz. R3.5 also scores 0, but not through silence: sugar gives MN9 0 Hz and adding bitter raises it to 4.5 Hz, so both
  suppression rows have the wrong sign, and JO-C/E drives MN9 at 21.7 Hz. The bitter-alone and sugar-to-giant-fiber null rows are 0 Hz on every brain except R3.5's
  bitter-alone at 0.72 Hz. All of this is at scale 0.47: scoring at each rung's calibrated scale and the 100 draws for R1 and R2 (section 6) are not done, and this pilot has two draws for R1 to R3 and one for the rest.
- The result depends on the side driven. Driving the left labellum instead (job 38189, `results/track_b/left/`), sugar drives MN9 at only 0.13 Hz on the real wiring (22.48 Hz from the
  right), and at 0.08 to 1.58 Hz on the R1 to R3 draws, except R1 draw 1 at 0. The sign score is still 0.6 on R0 and on every R1 to R3 draw but R1 draw 1 (0), resting on responses of a fraction of a
  spike per second. So the 0.6 is not a robust number, and the right-side rates at scale 0.47 cannot be taken to hold for the other side.

- At the scales the pre-test singled out (job 38190, `results/track_b/calibrated/`, right taste groups): R3.5 at 0.5 scores 0.4 (sugar to MN9 +1.17 Hz and Ir94e suppression -0.67 Hz as expected; adding bitter raises MN9 by 12.0 Hz, the wrong sign, and bitter alone drives it at 3.4 Hz). R4 at 1.2, which no pre-test passed, scores 0 with no MN9 or MDN response to any row. R5 at 2.0 scores 0, and the JO-C/E null row fails: JO-C/E drives MDN at 45.1 Hz.

The table above is the first pilot, on a draft list. The final list (scrambled-brains `docs/track_b_predictions.csv`, each source read on 2026-11-09; job 38207, `results/track_b/final/`, `tools/track_b_score.py`, both taste sides at scale 0.47) has six scored rows and two reported controls. A scored row passes if its sign is right and it is at least half R0's size: R0 1.0 (by construction), R1 draw 1 0.33, R1 draw 2 1.0, R2 draw 1 1.0, R2 draw 2 0.83 (dose response fails), R3 draws 1 and 2 1.0, R3.5, R4 and R5 0. The criterion, the list of rows and the two-sided drive were chosen after the first pilot on the draft list, and the two rows that failed on the real wiring were dropped then, so it is not blind.

### Per-brain lane channel: pilot on the real wiring (GPU, 2026-11-09)

`LANE_K=12 ride-readout.sbatch 4.5 201 r0 topk K`, jobs 38201 and 38202, 30 generations: top-k plus the 12 descending (type, side) groups this brain's HS probe picks, through its matched filter with 300 ms smoothing. Replays of the final mean decoder (48 riders x 15 s, seed 201, jobs 38220 to 38223, `results/rungs/r0/top<K>_lane12/v4.5_s201/replay_mu_*summary.json`):

| Readout | Last generation | Mean of last five | Lane gain | Replay with rule: finish / road / fall | Without rule: upright / beyond 3.5 m | Median distance |
|---|---|---|---|---|---|---|
| top-8 + lane | 6.93 s, 2% | 7.45 s | -0.08 | 6 / 41 / 1 | 39 / 28 | 6.4 m |
| top-8 (CPU) | 7.21 s, 6% | 7.15 s | none | 7 / 41 / 0 | 48 / 34 | 7.7 m |
| top-32 + lane | 8.83 s, 15% | 7.99 s | -0.09 | 12 / 36 / 0 | 48 / 27 | 3.8 m |
| top-32 (CPU) | 6.24 s, 0% | 6.19 s | none | 2 / 46 / 0 | 48 / 44 | 16.5 m |

The channel helps at k = 32 and not at k = 8, and neither holds the lane: the hand-picked readout's replays keep 46, 44 and 38 of 48. One seed; the lane runs were on GPU and the runs without on CPU, so the differences are not all the channel's. Decided 2026-11-09 (preregistration 9a, point 5): the hand-picked readout is primary, top-32 plus the lane channel secondary.

### Confirmatory draws: pre-test at scale 0.47 (GPU, 2026-11-09, job 38261)

Rewiring draws 3 to 5, 30 brains, run after the preregistration tag `prereg-v1`. Rate is outside the driven neurons, VS / haltere. Pass: lateralised outputs above the null maximum on both probes, rate within 10,750 to 43,000 (`results/rungs/pretest_<draw>_b30_w0.47.json`).

| Draw | Spikes/s | Lateralised outputs (null max) | Verdict |
|---|---|---|---|
| R1 s3 | 17,440 / 17,571 | 32 (4) / 28 (3) | pass |
| R1 s4 | 19,212 / 19,446 | 27 (7) / 25 (6) | pass |
| R1 s5 | 19,865 / 20,310 | 29 (4) / 28 (3) | pass |
| R2 s3 | 34,348 / 36,025 | 21 (155) / 20 (160) | **fail**: the null maximum is far above the outputs (null mean 0.9 / 1.0) |
| R2 s4 | 25,956 / 25,975 | 43 (13) / 37 (6) | pass |
| R2 s5 | 18,906 / 21,354 | 27 (19) / 35 (8) | pass |
| R3 s3 | 12,028 / 12,264 | 27 (8) / 30 (13) | pass |
| R3 s4 | 12,756 / 13,801 | 31 (6) / 37 (5) | pass |
| R3 s5 | 15,396 / 16,428 | 36 (9) / 42 (8) | pass |

R2 draw 3 fails on the null only; under section 5 of the preregistration it is ridden anyway, reported, and its runs enter the medians.

### Model-side rung: pre-test on the real wiring (CPU, 2026-11-08)

`runs/pretest.py` with 30 brains on R0 (job 38183, `results/rungs/model_side/`), one parameter moved by 10% at a time; the rate
window is 10,750 to 43,000 spikes/s outside the driven neurons, and R0 itself gives 21,300 on the VS probe with 38 and 39 lateralised outputs.

| Variant | Network spikes/s, VS / haltere | Lateralised outputs, VS / haltere (null max) | Gate |
|---|---|---|---|
| synaptic scale x 0.9 (0.423) | 14,522 / 14,724 | 25 / 21 (7 / 7) | pass |
| synaptic scale x 1.1 (0.517) | 28,539 / 28,914 | 49 / 64 (10 / 8) | pass |
| membrane time constant 18 ms | 25,878 / 26,442 | 41 / 53 (6 / 6) | pass |
| membrane time constant 22 ms | 17,149 / 17,309 | 31 / 29 (4 / 4) | pass |
| synaptic time constant 4.5 ms | 16,333 / 17,109 | 29 / 32 (10 / 3) | pass |
| synaptic time constant 5.5 ms | 25,697 / 25,871 | 45 / 54 (6 / 4) | pass |

All six pass. A 10% change in synaptic scale moves the network rate by about a third, and a 10% change in either time constant by about a fifth. Pilot rides of the six variants on the real wiring (hand-picked readout, CEM seed 201, 60 generations; jobs 38191 to 38196, `results/rungs/model_<variant>_cpu/`, `MODEL_ARGS` in `ride-rung.sbatch`) ran on the CPU, two at a time, and finished on 2026-11-09.

| Variant | Riding time, last generation (s) | Riders finishing | Population rate while riding (spikes/s) |
|---|---|---|---|
| synaptic scale x 0.9 | 12.43 | 60% | 25,082 |
| synaptic scale x 1.1 | 9.26 | 27% | 48,264 |
| membrane time constant 18 ms | 11.05 | 31% | 44,756 |
| membrane time constant 22 ms | 13.36 | 75% | 27,789 |
| synaptic time constant 4.5 ms | 10.63 | 31% | 26,986 |
| synaptic time constant 5.5 ms | 12.38 | 58% | 48,912 |

One seed each, so these are pilots. R0's three pilots (seeds 201 to 203) gave 13.71, 11.89 and 10.91 s (SD 1.4): every variant except scale x 1.1 is within one SD of R0's median, and x 1.1 is 1.9 SD below it. The confirmatory rides of these variants (seeds 211 to 213) are in the secondary design.

## Closed-loop scale of R3.5 and R5 (preregistration section 4)

`ride-rung.sbatch` with `GENS=0` on draw 1, CEM seed 211, jobs 38363 to 38368, then `tools/replay_rate.py --window 0.6` against R0's 23,388 spikes/s (`results/rungs/cl_<rung>_w<scale>/`, CPU).

| Brain | Scale | First 0.6 s, spikes/s | Relative to R0 |
|---|---|---|---|
| R3.5 | 0.47 | 20,763 | 0.89 |
| R3.5 | 0.5 | 36,568 | 1.56 |
| R3.5 | 0.53 | 67,866 | 2.90 |
| R3.5 | 0.56 | 92,167 | 3.94 |
| R5 | 1.5 | 13,546 | 0.58 |
| R5 | 2 | 37,752 | 1.61 |

By the rule (smallest |log(rate / 23,400)|, within 2x), R3.5 rides at 0.47 and R5 at 2.0, and no bisection is needed. R4 stays at 1.2 from the pilot. The R3.5 rate is steep: 0.06 of scale is a factor of 4.4. The three single rides (draw 1, seed 211, 4.5 m/s, hand-picked readout) are on the CPU, chained, jobs 38371 to 38373, because the GPUs are taken; the preregistration allows that and they are reported as CPU runs. Tags `conf_r35_s1_w0.47_cpu`, `conf_r4_s1_w1.2_cpu`, `conf_r5_s1_w2_cpu`.

## First confirmatory ride and the held-out replay tool

The first primary ride (R0, 4.5 m/s, CEM seed 211, job 38263) reached 60 generations on the GPU in 294 min, under the 340 min cap: 12.79 s riding time in the last generation, 62% of riders finishing.

`tools/heldout.py` (with `heldout.sbatch`) replays a search's final mean decoder with the settings recorded in its `cem.json`, into `<run>/heldout/<condition>.json`. Section 5 gives gust seeds for the gust test only; the speed conditions reuse replay seed 301. Test on that ride, CPU, job 38413, about 7 min per condition:

| Condition | Speed (m/s) | Riding time (s) | Finished / 48 | Left road | Fell |
|---|---|---|---|---|---|
| gust seed 301 | 4.5 | 14.05 | 38 | 8 | 2 |
| speed +0.5 | 5.0 | 13.10 | 28 | 20 | 0 |
| speed -0.5 | 4.0 | 7.77 | 0 | 13 | 35 |

One decoder, so this checks the tool and does not test anything. The final mean rides longer than the last generation's mean because the generation includes the search's noise around it.

## Confirmatory rides so far (2026-11-10)

Last-generation riding time of each finished 60-generation ride, 4.5 m/s, CEM seed 211. One seed per rung so far, so no prediction is tested yet.

| Rung | Job | Device | Minutes | Riding time (s) | Finished |
|---|---|---|---|---|---|
| R0 | 38263 | GPU | 294 | 12.79 | 62% |
| R1 draw 3 | 38264 | GPU | 312 | 14.65 | 85% |
| R1 draw 4 | 38265 | GPU | 307 | 13.72 | 71% |
| R1 draw 5 | 38266 | GPU | 274 | 10.47 | 42% |
| R2 draw 3 (failed the pre-test null, ridden as preregistered) | 38267 | GPU | 291 | 12.02 | 44% |
| R2 draw 4 | 38268 | GPU | 286 | 13.05 | 71% |
| R2 draw 5 | 38269 | GPU | 291 | 13.26 | 71% |
| R3 draw 3 | 38270 | GPU | 277 | 13.19 | 60% |
| R3 draw 4 | 38271 | GPU | 280 | 13.37 | 69% |
| R3 draw 5 | 38272 | GPU | 274 | 13.54 | 75% |
| R3.5 draw 1, scale 0.47 | 38371 | CPU | 163 | 2.71 | 0% |
| R4 draw 1, scale 1.2 | 38372 | CPU | 269 | 2.96 | 0% |
| R5 draw 1, scale 2.0 | 38373 | CPU | 301 | 4.34 | 0% |

R3.5's single ride is the one prediction 2 uses for its transition clause; it is 21% of R0's first ride, and the test waits for R0's median over five seeds. R4's single ride is the one prediction 5 uses: it is 23% of R0's first ride (last five generations 2.49 s), so unless R0's five seeds come out very differently, R4 does not ride as well as R0 and prediction 5's condition is not met. Section 5 gives the held-out tests to the primary runs only, so R3.5, R4 and R5 get none. R5's single ride (job 38373) ends at 4.34 s (last five generations 4.21 s), with no rider finishing; it rides longer than R3.5 and R4 but stays a third of R0's first seed. The three single rides are done; none finishes a rider in its last generation. R1's three draws (median 13.72 s) are above R0's first seed, which says nothing yet: prediction 1 compares medians over five R0 seeds against R0's seed-SD.

Held-out replays of the final mean decoder (CPU, 48 riders, 15 s; jobs 38413 and 38436 for R0, 38437 and 38438 for R1). Riding time in s, finished / 48 in brackets:

| Ride | gust301 | gust302 | +0.5 m/s | -0.5 m/s |
|---|---|---|---|---|
| R0 seed 211 | 14.05 (38) | 14.80 (46) | 13.10 (28) | 7.77 (0) |
| R1 draw 3 | 14.75 (44) | 15.00 (48) | 14.61 (42) | 12.71 (24) |
| R1 draw 4 | 14.89 (46) | 14.84 (47) | 14.45 (42) | 11.43 (10) |
| R1 draw 5 | 13.56 (36) | 13.87 (41) | 10.10 (17) | 7.85 (0) |
| R2 draw 3 | 11.92 (26) | 11.99 (24) | 12.13 (27) | 8.89 (4) |
| R2 draw 4 | 15.00 (48) | 14.63 (44) | 14.32 (42) | 12.31 (18) |
| R2 draw 5 | 14.21 (41) | 14.46 (42) | 11.08 (19) | 8.76 (4) |
| R3 draw 3 | 14.07 (33) | 14.15 (34) | 10.99 (15) | 10.50 (9) |
| R3 draw 4 | 13.87 (34) | 13.05 (30) | 11.42 (17) | 7.19 (0) |

Unseen gusts cost little on all three. Slowing to 4.0 m/s costs the most: R0's decoder finishes no rider (35 fall), R1's finish 24 and 10 (R1 draw 4 loses most of the rest off the road, 37 riders). Section 5 makes these descriptive, not tests. R1 draw 5 (job 38442), the weakest of the three rides, also loses the most off the road at both test speeds (31 riders at +0.5, 33 at -0.5) and finishes no rider at 4.0 m/s, like R0.
R2 draw 3 (job 38445) keeps its training-speed riding time under new gusts and at +0.5 m/s, but about half its riders leave the road in each; at 4.0 m/s 4 finish and 26 fall.
R2 draw 4 (job 38455) finishes every rider under gust seed 301; at 4.0 m/s 18 finish and 29 fall.
R2 draw 5 (job 38456) holds under new gusts; at +0.5 m/s 29 riders leave the road, at 4.0 m/s 4 finish and 32 fall.
R3 draw 3's replays were job 38462 (cancelled when the queue became one chain); they ran as job 38691, with draws 4 and 5 after it. Under new gusts no rider falls but 14 to 15 leave the road; at +0.5 m/s 33 leave the road and none falls; at 4.0 m/s 9 finish, 29 leave the road and 10 fall.
R3 draw 4 (job 38706): no rider falls under new gusts or at +0.5 m/s, but 14 to 18 and 31 leave the road; at 4.0 m/s none finishes, 36 leave the road and 12 fall, the most falls of any confirmatory replay so far.
R3's three draws (13.19, 13.37 and 13.54 s, finished 2026-11-11) all ride above R0's first seed; like R1's, this tests nothing until R0 has five seeds.

## The queue as one chain (2026-11-11)

The cluster's default QoS (`normal`) sets one running job per user (`MaxJobsPU=1`). Slurm does not enforce it here (`AccountingStorageEnforce = none`), but the queue had been running two GPU rides and a CPU replay at once, holding 2 of the node's 3 GPUs while another user waited for one. So on 2026-11-11 at 01:33 the 128 pending jobs (two ride chains and the held-out replay 38462) were cancelled and everything left was queued again as one afterany chain by `tools/submit_serial.py --after 38272`: the held-out replays of R3 draws 3 to 5, then each remaining primary ride followed by its held-out replays, then the 38 secondary rides, then prediction 3's four replays. Jobs 38463 to 38687, 225 links (128 rides, 97 replays); the chain was checked to have no break. The rides and their order are unchanged, so this is not a deviation from the preregistration; it only roughly doubles the time left, to about four weeks at about 5 h per ride and 30 min per replay. List of links: `logs/local/submit-serial-2026-11-11.txt`.

Later the same night the queue was changed again so that it shows only what is next (Victor's request): the 225 pending links were cancelled (01:50) and the same list now runs as a relay, `python3 tools/submit_serial.py --next --after 38272`. Each pass submits the first link left and a one-CPU relay job (`serial-next.sbatch`, a few seconds) that waits for it and runs `--next` again, so Slurm holds one link and one relay at a time. Each pass works out what is left from the results on disk, so a ride the 340 min cap stops short is queued again and resumes; a link submitted three times is skipped and named in the relay's log (`logs/serial-next-*.out`, counts in `logs/serial-tries.json`). The first link is job 38691 (R3 draw 3's held-out replays), its relay 38692. If the relay breaks (no link and no relay in the queue while links are left), restart it with `python3 tools/submit_serial.py --next`. The relay jobs are left out of JOBS.md.

## Interim three-row figure (milestone of 13 November)

scrambled-brains `tools/interim_figure.py` (run on the login VM, system python3 with matplotlib) reads the results here and writes `site/figures/interim.{svg,png,json}`; the JSON lists every plotted value with its source file and the date of the newest file read. Rows: A, last-generation riding time of every finished 60-generation hand-picked-readout search at 4.5 m/s (confirmatory filled, pilots open, R0's gate pilots at 57 to 60 generations); B, Track B confirmatory scores per draw; C, Track C pilot N90 at the descending site, R0 to R3 only (R3.5 to R5 not yet measured: the pilot came before they were ridden). First version 2026-11-11, after three independent reviews (numbers, claims, translation and presentation). Rerun the script and edit the caption's list of rides together when rides finish.

## Track B confirmatory runs (preregistration section 6)

`trackb-conf.sbatch`, CPU, `results/track_b/confirmatory/`, scored by `python3 tools/track_b_score.py <dir> --by-rung`. The preregistration gives the numbers of draws, not which ones, so these were picked before any run so that no Track B pilot has used them: R1 and R2 draws 101 to 200; R3, R3.5, R4 and R5 draws 3 to 5 (only R3 has those draws in Track A; R3.5, R4 and R5 ride draw 1 there). Scales: 0.47 for every rung, plus each rung's closed-loop scale where it differs (R4 1.2, R5 2.0). R0's reference (job 38414) came out identical to the pilot's `final/r0.json`. Test, one draw each (job 38415): R1 draw 101 and R2 draw 101 both score 1.0, which says nothing about the mean over 100 draws. The rest ran as jobs 38416 to 38429 (2026-11-10 01:33 to 13:52, all completed, 218 brains, no failed draw).

Results (fraction of the six scored rows passed, mean over draws; `scores.json` holds every brain's rows):

| Rung | Scale | Draws | Mean score | Draws by score |
|---|---|---|---|---|
| R0 | 0.47 | 1 | 1.000 | |
| R1 | 0.47 | 100 | 0.682 | 31 at 1.0, 27 at 0.83, 2 at 0.67, 40 at 0.33 |
| R2 | 0.47 | 100 | 0.993 | 96 at 1.0, 4 at 0.83 |
| R3 | 0.47 | 3 | 1.000 | |
| R3.5 | 0.47 | 3 | 0.000 | |
| R4 | 0.47 / 1.2 | 3 / 3 | 0.000 / 0.000 | |
| R5 | 0.47 / 2.0 | 3 / 3 | 0.000 / 0.056 | one draw at 2.0 passes loom to DNp02/DNp11 |

- R1 loses only taste rows. Both loom rows pass on all 100 draws (median 255 and 174 Hz against R0's 264 and 183). The four taste rows mostly keep their sign and fall below half of R0 (median 18, -17, -17 and 2.4 Hz against 30, -30, -30 and 7.4); 13 row failures out of 228 are sign flips. Where one taste row fails, the others usually fail with it: 40 draws pass the two loom rows only.
- R2 loses only the dose-response row, on 4 draws, by size.
- R3.5, R4 and R5: the taste rows give exactly 0 Hz difference (no response reaches MN9 or the suppression readouts), so they fail by sign; the loom rows keep at most a fraction of R0's difference. The closed-loop scale (R4 1.2, R5 2.0) does not bring the rows back.
- So the ladder is R0, R2, R3 at or near full score, R1 in between, and every rung from R3.5 up at or near zero. The preregistration states no numerical Track B prediction; this is reported as the decoder-free result of section 6.

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

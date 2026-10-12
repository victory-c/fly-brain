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
- Every current riding number is one run at 5.5 m/s with 5 Nm gusts. That speed is inside the bike's self-stable
  range (4.70 to 7.74 m/s), where the bike balances itself. Say "stays on the road", not "balances the bike", and
  give the job id, because a rerun will not reproduce it exactly (see the last section).
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
| Engine matches Shiu's Brian2 code spike for spike | 2,101 spikes over 100 ms, 500-neuron network | `fly_brain/README.md:19-20`; `tests/test_brian2.py` | current; no passing log is committed, and the three logged cluster test runs (jobs 36627, 36631, 36637) skipped this test because brian2 is not installed |
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

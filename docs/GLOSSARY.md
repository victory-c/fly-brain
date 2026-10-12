# Glossary

Terms you will meet in this repo and in the Scrambled Brains plan, for members coming from biology and from
computer science alike. Entries are grouped by topic; the index below is alphabetical. Code paths are relative
to `fly_brain/`.

**Index.** attempt (6) · bailed (5) · balance gate (7) · bodyId (2) · brain.npz (2) · brain_meta.parquet (2) ·
BrainLoop (1) · Brian2 (1) · cell type (2) · CEM (6) · class (2) · connectome (2) · CSR (2) · decoder (6) ·
digital sphinx (4) · DN (3) · dt (1) · Engine (1) · experiment() (1) · fell (5) · flies (1) · FlyWire (2) ·
generation (6) · GraphEngine (1) · GRN (3) · gust (5) · halteres (3) · hands-off (5) · instance (2) ·
JO-CE, JO-F (3) · LIF (1) · male CNS (2) · Meijaard et al. 2007 (4) · MN9 (3) · N90 (7) · off-road (5) ·
open loop (5) · passenger screen (6) · PD rider (5) · Poisson input (1) · polarity (5) · population mean (6) ·
probe (6) · random-k DN (7) · readout (6) · refractory period (1) · rootSide (2) · row (2) ·
self-stable speed (5) · sensory bypass (7) · sensory encoder (5) · Shiu et al. 2024 (4) · silencing (1) ·
somaSide (2) · spike (1) · subclass (2) · superclass (2) · synaptic delay (1) · theta (6) · top-k DN (7) ·
transmission gate (7) · transmitter sign (2) · VNC (3) · VS and HS cells (3) · w_syn, W_SYN_SCALE (1) ·
warm-up (6) · weave and capsize (5) · Whipple model (4) · wiring ladder R0-R5 (7)

Sections: 1 The neuron model and the simulator · 2 The wiring diagram and its files · 3 Fly anatomy ·
4 Papers and debates · 5 The bike · 6 Learning to ride · 7 Scrambled Brains

## 1. The neuron model and the simulator

- **Spike.** A brief electrical pulse, the unit of neural signaling. A model neuron spikes when its membrane
  potential passes the threshold, -45 mV, which is 7 mV above its resting value of -52 mV; it then resets to
  -52 mV (`brain/engine.py` `PARAMS`, `Engine.step`).
- **LIF (leaky integrate-and-fire).** The simplest spiking neuron model: the membrane potential adds up incoming
  input, leaks back toward rest with a 20 ms time constant, and fires a spike at threshold. Synaptic input enters
  through a second variable `g` that decays with a 5 ms time constant. All 166,700 neurons are the same LIF unit,
  with Shiu et al.'s equations and constants (`brain/engine.py:1-45`).
- **dt.** The simulation time step, 0.1 ms (Brian2's default), so one simulated second is 10,000 steps.
- **Poisson input.** Random input events at a set average rate, which is how stimulation is modeled. In every step
  each stimulated neuron gets an event with probability rate x dt, and each event raises its potential by
  250 x `w_syn`, enough to make it spike (`Engine.drive(hz)`; Shiu's default rate is 150 Hz, `brain/stimuli.py`
  `SHIU_HZ`).
- **Refractory period.** For 2.2 ms after a spike a neuron is frozen, and synaptic or Poisson input that reaches
  it then is dropped, not saved for later. Neurons driven by Poisson input have no refractory period. These are
  the two Brian2 rules the rewrite added (`brain/engine.py:6-13`, `PARAMS["t_rfc"]`, `PARAMS["t_rfc_input"]`).
- **Synaptic delay.** A spike reaches its targets 1.8 ms (18 steps) after the neuron fires; the engine holds
  spikes in a ring buffer of that length (`Engine.in_flight`).
- **w_syn and W_SYN_SCALE.** `w_syn` is the voltage jump per synapse, the model's one free parameter; Shiu fit
  0.275 mV on FlyWire. The male CNS has almost twice as many synapses per neuron (745 vs 393), so the repo
  multiplies it by `W_SYN_SCALE = 0.47`, giving `W_SYN` = 0.129 mV (`brain/engine.py:47-52`, chosen by
  `runs/calibrate_wsyn.py`). Watch out: `Engine(...)`, `BrainLoop(...)` and `experiment(...)` use the unscaled
  0.275 mV unless you pass `params={"w_syn": W_SYN}`, as every script in the repo does.
- **Silencing.** In Shiu's sense, a silenced neuron still fires but its synapses deliver nothing, so its effect on
  the rest of the brain is removed while its own activity stays visible. Pass rows as `silenced=` to
  `experiment()` or `silence=` to `Engine` (`brain/engine.py:76-77`, tested in `tests/test_engine.py:103-111`);
  one mask applies to every fly in the batch.
- **Flies (batch).** Independent copies of the brain simulated side by side, each with its own random input,
  sharing only the wiring; every state tensor is (flies, neurons). In the bike code each fly is a "rider".
- **Engine, GraphEngine, BrainLoop, experiment().** `Engine` (`brain/engine.py`) holds the state of a batch of
  flies and steps it. `experiment()` runs one fixed stimulation and returns mean rates and binned spikes.
  `GraphEngine` (`brain/graph_engine.py`) is the same model recorded as a CUDA Graph, about 3.5 times faster for
  a single fly, GPU only. `BrainLoop` (`brain/loop.py`) wraps an Engine for closed loop: set sensory rates, run
  10 ms, read spike counts.
- **Brian2.** The Python neural simulator Shiu's original code uses. `tests/test_brian2.py` runs a random
  500-neuron network in Brian2 and in `Engine` and requires identical spikes; it is skipped unless brian2 is
  installed.

## 2. The wiring diagram and its files

- **Connectome.** The full map of neurons and the synapses between them, reconstructed from electron microscopy.
  In the model it fixes who connects to whom, with how many synapses, and with which sign. Nothing in it is
  learned; the only fitted number is the global weight scale `W_SYN_SCALE`.
- **Male CNS v1.0.** The connectome used here: one male fly's brain plus ventral nerve cord, released by Janelia
  FlyEM and Google Research. The model keeps the 166,700 annotated bodies that have a superclass, with
  124 million synapses between them (`brain/connectome.py`, module docstring).
- **FlyWire.** An earlier connectome of a whole female fly brain, without the nerve cord, on which Shiu et al.
  built and tested their model (version 783: 138,639 neurons, 393 synapses per neuron).
  `runs/calibrate_wsyn.py` `flywire_brain()` downloads Shiu's FlyWire network and runs it in the same engine.
- **CSR, brain.npz.** `brain.npz` stores the wiring as a compressed sparse row matrix with one row per
  presynaptic neuron: row i's targets are `post[ptr[i]:ptr[i+1]]` and their signed synapse counts are
  `syn[ptr[i]:ptr[i+1]]`. This layout lets the engine read only the rows of neurons that just fired. 25.6 million
  connected pairs; `body_ids` gives each row's bodyId. Build it with `python -m brain.connectome` or download it
  with `python -m brain.fetch`.
- **brain_meta.parquet.** One line per neuron in simulator order, with columns `row`, `bodyId`, `type`,
  `instance`, `superclass`, `class`, `subclass`, `somaSide`, `rootSide`, `entryNerve`, `transmitter`,
  `inhibitory`, `synapses_out` and `synapses_in` (written by `brain/connectome.py` `build()`).
- **bodyId vs row.** A bodyId is the dataset's ID for one reconstructed neuron, the number papers and neuPrint use.
  A row is the simulator's index, 0 to 166,699: the neuron's position when all neurons are sorted by bodyId.
  `Engine`, `experiment()`, silencing and every recording use rows, so convert at the edges:

  ```python
  from brain.connectome import Brain
  brain = Brain()
  dnp20 = brain.select(type="DNp20")                # names -> rows (brain/select.py)
  brain.meta.loc[dnp20, ["bodyId", "instance"]]     # rows -> their line of brain_meta.parquet
  rows = brain.index_of(my_body_ids)                # a list of bodyIds -> rows, same order; unknown ids DROPPED
  ids = brain.body_ids[rows]                        # rows -> bodyIds
  ```

  `index_of` drops IDs that are not neurons without warning, so check the length of what it returns
  (`runs/calibrate_wsyn.py` asks for Shiu's 21 sugar GRNs and gets 20). Save bodyIds, not rows, in anything you
  keep: a build from another annotation release can shift every row. Older result files (`results/screen*.json`)
  call the row `idx`. FlyWire root IDs (720575940...) are a different ID space. `brain.select(...)` finds rows by
  type, instance, side, superclass, class, transmitter, region or position, so you rarely type a row number.
- **Cell type, instance.** `type` is the name shared by neurons with the same shape and wiring, such as DNp20 or
  LB3c, often one per side. `instance` names a single neuron, usually type plus side, such as MN9_L;
  `stimuli.instance("MN9_L")` returns its row.
- **Superclass, class, subclass.** Coarser annotation labels. `superclass` is the broad group
  (`descending_neuron`, `vnc_motor`, `ol_intrinsic`, ...); `class` and `subclass` refine it, for sensory neurons by
  modality (`gustatory`, `mechanosensory_proprioceptive`; `haltere`, `wind_gravity`). `bike/senses.py`
  `sensory_populations()` picks the bike's sensory neurons this way.
- **somaSide, rootSide.** `somaSide` is the side of the cell body, L or R. Sensory neurons have their cell bodies
  outside the CNS, so for them `rootSide`, the side where the nerve enters, is used instead; `brain.meta` and
  `stimuli.neurons()` combine the two into `side`, which `brain.select(side=...)` filters on.
- **Transmitter sign.** Every synapse of a neuron is excitatory or inhibitory according to that neuron's predicted
  transmitter, stored as the sign of `syn`. GABA, glutamate and histamine count as inhibitory because in the fly
  CNS they act mainly through chloride channels (GABA and glutamate following Shiu; histamine added here).
  Acetylcholine, dopamine, serotonin, octopamine and the 2,070 neurons with no clear call count as excitatory, and
  38.4% of all synapses are inhibitory (`brain/connectome.py`, module docstring and `CHLORIDE_TRANSMITTERS`).

## 3. Fly anatomy

- **DN (descending neuron).** A neuron in the brain whose axon runs down the neck into the VNC, carrying commands
  to the body; about 1,300 neurons fall in the "descending" region of the brain map. Names such as DNp20 follow
  Namiki et al. 2018, with the letter giving the cell-body cluster. The bike decoder reads DNs and a few wing motor
  neurons (`bike/readout.py`); DNp01, the giant fiber, triggers escape (a bail), and MDN, the moonwalker neuron,
  drives the brake.
- **VNC (ventral nerve cord).** The fly's counterpart of a spinal cord, in the thorax, with the circuits for legs,
  wings and halteres. The male CNS includes it (about 15,000 neurons in the "vnc" map region); FlyWire does not.
- **MN9.** The motor neuron that extends the proboscis, the fly's feeding mouthpart. Shiu used its firing as the
  readout for feeding; `stimuli.mn9()` returns the rows of MN9_L and MN9_R.
- **GRN (gustatory receptor neuron).** A taste neuron. Shiu's experiments drive groups of labellar GRNs: sugar
  (male CNS types LB3b-d, LB4b), water (LB3a), bitter (LB1a-d) and Ir94e (LB1e, LB2a-c) (`brain/stimuli.py`,
  `brain/shiu_groups.json`). Shiu drove about 20 neurons on one side; `stimuli.group(name)` takes both sides
  unless you pass `side="L"` or `"R"`.
- **JO-CE, JO-F.** Subgroups of Johnston's organ neurons, the sensors in the antenna that detect its movement by
  sound, wind and gravity. Shiu activated them to test antennal grooming (`stimuli.group("jo_ce")`, `"jo_f"`).
  The bike uses the wind/gravity JO neurons to signal airspeed and lean.
- **VS and HS cells.** Large optic-lobe neurons that respond to wide-field visual motion: vertical-system cells to
  rotations such as roll, horizontal-system cells to yaw and forward flow. The bike sends roll rate to VS cells and
  yaw, heading and the lane cue to HS cells (`bike/senses.py`).
- **Halteres.** The fly's small hind wings, which work as gyroscopes; their afferents carry roll and yaw rate in
  the bike model.

## 4. Papers and debates

- **Shiu et al. 2024.** "A Drosophila computational brain model reveals sensorimotor processing", *Nature* 2024
  (doi:10.1038/s41586-024-07763-9). They ran the FlyWire brain as an LIF network in Brian2 and showed that
  activating taste neurons predicts which neurons respond, including MN9 for feeding. `brain/engine.py`
  re-implements their model (MIT-licensed code, github.com/philshiu/Drosophila_brain_model) in PyTorch.
- **Digital sphinx.** The objection that a connectome model driving a body proves little when a trained decoder
  sits between the two: a worm connectome plus a trained decoder can also drive a fly body (eLife reviewed
  preprint RP 111516; The Transmitter). If any network with a fitted decoder produces the behavior, the behavior
  does not show that the wiring matters. Scrambled Brains is designed to test exactly this.
- **Whipple model, Meijaard et al. 2007.** Linearized equations for a bicycle's lean and steer, with benchmark
  values published in *Proc. R. Soc. A* 2007. `bike/tarmac.py` builds the matrices from 25 physical parameters;
  `tests/test_bike.py` checks them against the paper to 1e-8.

## 5. The bike

- **Self-stable speed (weave and capsize).** Between the weave speed and the capsize speed a riderless bike
  balances itself: below the weave speed it wobbles and falls, above the capsize speed it slowly leans over. The
  benchmark bicycle is self-stable from 4.29 to 6.02 m/s, the road bike model with a 70 kg rider from 4.70 to
  7.74 m/s (`bike/tarmac.py` `eigen_speeds()`; run `python -m bike.tarmac`). Every current riding result is at
  5.5 m/s, inside that range.
- **Gust.** A random side push on the bike: a roll torque that wanders smoothly (an Ornstein-Uhlenbeck process
  with a 1 s time constant); `--gust 5` sets its standard deviation in Nm (`bike/dynamics.py` `Peloton.step`).
- **Fell, off-road, bailed.** A rider has fallen when its lean passes 30 degrees (`bike/dynamics.py`), has left
  the road when it is more than 3.5 m from the center of the 7 m road (`--offroad 3.5`), and bails when the
  giant fiber fires 4 spikes within 50 ms. Each ends that rider's run.
- **PD rider (oracle).** A conventional controller with no brain that steers into the lean
  (`Peloton.pd_oracle`, `python -m runs.ride --oracle`). It shows the bike is rideable (the `/ride/oracle` page).
- **Hands-off (open loop).** The brain runs and senses the bike, but the decoder does not steer: the prior decoder,
  about 70 W of pedaling and no steering (`--open-loop`, the `/ride/open-loop` page). It is the floor a learned
  decoder has to beat.
- **Sensory encoder.** The modeled mapping from bike state to the firing rates of 789 real sensory neurons: VS
  cells (roll), HS cells (yaw, forward flow, lane), haltere afferents (rotation), Johnston's organ (airspeed,
  lean) and front-leg proprioceptors (handlebar) (`bike/senses.py`, gains in `GAINS`). The neurons are real; the
  gains are hand-set assumptions.
- **Polarity.** Which eye's VS and HS cells a rotation drives. `physio` follows fly physiology; `legacy` is the
  first, arbitrary assignment, kept so older decoders replay (`bike/senses.py`, `Senses.__init__`). The current
  /ride/ run uses `legacy`, the default.

## 6. Learning to ride

- **Passenger screen.** A run in which the PD rider steers and the brain only watches; every neuron's rate is
  correlated with the bike's lean, lean rate and position to find which DNs carry balance information
  (`runs/screen.py` -> `results/screen.json`; earlier simulator, see `CURRENT_NUMBERS.md`).
- **Probe.** The bike is held upright and one side's HS (or VS, or haltere) cells get extra drive; each output
  neuron's left-minus-right response reveals the lane channel and becomes the lane filter (`runs/probe.py`,
  `--lane-filter`).
- **Readout.** Which neurons the decoder listens to, and how they are summarized: the mean rate in Hz per cell
  type and side (`bike/readout.py` `Readout`). The "lane" readout used now has 42 types (84 features, 112 neurons):
  roll-rate DNs, lean DNs, wing steering motor neurons, walking DNs and lane DNs.
- **Decoder.** The learned map from readout features to steering torque (6 Nm x tanh of a weighted sum), pedal
  power (up to 250 W) and braking (up to 6 m/s^2) (`bike/readout.py` `Decoder.act`). Steering features are
  smoothed over 40 ms; the lane channel over 300 ms in the current run (`--tau-lane-ms`), centered on its warm-up
  rate.
- **Theta.** The decoder's parameter vector: one steering weight per feature, a steering bias, pedal gain and bias,
  brake gain and bias, and one lane-filter gain. The /ride/ decoder has 90 numbers, named in each result file's
  `decoder_names` (`runs/ride.py` `dec_names()`). Theta is the only thing learned; the connectome never changes.
- **CEM (cross-entropy method).** A search that needs no gradients: draw candidate thetas from a Gaussian, score
  each, refit the Gaussian's mean and spread to the best quarter, repeat (`runs/ride.py`, from the comment
  "cross-entropy method over decoder weights"). Each of the 48 riders in a generation tries one candidate on fresh
  gusts, with rider 0 always riding the current mean. Fitness is time on the bike, plus a small bonus for speed,
  minus penalties for distance from the lane center, steering effort and bailing (`Ride.episode`).
- **Population mean vs best.** CEM saves `mu`, the search's mean theta, and `best_theta`, the single best-scoring
  rider. "The final decoder" in the READMEs and `results/relearn/cem_mu.json` is the mean.
- **Warm-up.** The first 300 ms of every run, with the bike upright, before the decoder acts. With
  `--center-batch` the lane features are centered on the batch-mean rate at its end.
- **Attempt, generation.** An attempt is one rider's run; a generation is one round of 48 riders. On the /ride/
  page attempt k is generation k // 48, rider k % 48 (`runs/ride.py --log-attempts`).

## 7. Scrambled Brains

Terms from the Scrambled Brains project plan (DeepBrain at Berkeley, fall 2026). None of this is in the repo
yet, and the details may change; the rung generators are planned for `brain/variants.py`.

- **Wiring ladder, R0-R5.** Perturbed connectomes graded from most to least detailed: **R0** the real wiring;
  **R1** transmitter-sign errors at measured rates (Eckstein et al. 2024 confusion rates); **R2** synapse-count
  jitter (plus or minus 25%, flybench's definition); **R3** a type-preserving shuffle, so only cell-type-level
  wiring survives; **R4** a degree-preserving shuffle, so each neuron keeps only its number of inputs and outputs;
  **R5** random wiring. Each rung is scored on riding, on decoder-free predictions and on decodability.
- **Transmission gate.** The test a rung must pass before it gets CEM time: left-vs-right drive to the VS, HS and
  haltere inputs must produce a significant lateralized DN response (30 flies) at a baseline rate within 2x of the
  real brain's, at some `W_SYN_SCALE` between 0.35 and 0.60. Rungs that stay silent or run away are reported as
  outcomes.
- **Sensory bypass, hands-off floor.** The two reference lines for riding: a decoder that reads the sensory
  neurons directly, skipping the brain (the expected ceiling), and the bike with no steering (the floor).
- **Top-k and random-k DN.** Each brain gets its own passenger screen, and the decoder reads the k DN-class neurons
  that screen ranks highest (k = 8 and 32); random-k picks k at random as a control.
- **N90.** The number of recorded neurons needed to reach 90% of the roll-rate R^2 that all DNs give together,
  measured at a brain DN site and at a VNC site (Track C).
- **Balance gate.** The first experiment of the semester: learning from a blank decoder at 4.0 and 4.5 m/s, below
  the self-stable range, to check that the fly can balance the bike at all.

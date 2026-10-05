"""Leaky integrate-and-fire dynamics on the whole male CNS, for many flies at once.

The neuron and synapse model is Shiu et al., Nature 2024 (github.com/philshiu/Drosophila_brain_model, MIT
licence), written there for Brian2:

    dv/dt = (v_0 - v + g) / t_mbr          frozen while refractory
    dg/dt = -g / tau                       frozen while refractory
    v > v_th          ->  spike, then v = v_rst, g = 0 and t_rfc of refractoriness
    presynaptic spike ->  t_dly later, g += w_syn * (signed synapse count)
    stimulated neuron ->  Poisson events at rate r, each v += w_syn * f_poi; no refractory period

Brian2 makes variables flagged (unless refractory) conditional-write: synaptic events and Poisson events that
reach a neuron while it is refractory (including the step it fires) are dropped, not held until it recovers.

Brian2 fills every time step with the same slots, in a fixed order: state update, thresholder, synaptic
propagation, reset. Engine.step keeps that order. The linear ODEs are advanced exactly over dt for every neuron
outside its refractory period; neurons above threshold fire and turn refractory at once; the events of spikes sent
t_dly earlier, and this step's Poisson events, then land on the neurons still able to take input; the neurons that
fired are reset last. tests/test_brian2.py checks this against Brian2 itself, spike for spike.
Spikes are delivered event by event: only the connectome rows of neurons that fired are read, so a step costs
in proportion to the activity, not to the 25.6 million connected pairs.

State lives in the Engine between calls, so one class serves one-shot experiments (experiment below) and a brain
in a closed loop with a body (brain/loop.py). Every state tensor is (flies, neurons): B independent trials that
share the connectome and nothing else.
"""
import math
import time

import numpy as np
import torch

PARAMS = {  # Shiu et al. 2024, model.py, with the sources given there
    "dt": 0.1,          # ms, Brian2's default clock
    "v_0": -52.0,       # mV resting potential       Kakaria & de Bivort 2017
    "v_rst": -52.0,     # mV reset potential         Kakaria & de Bivort 2017
    "v_th": -45.0,      # mV spike threshold         Kakaria & de Bivort 2017
    "t_mbr": 20.0,      # ms membrane time constant  Kakaria & de Bivort 2017
    "tau": 5.0,         # ms synaptic time constant  Jürgensen et al. 2021
    "t_rfc": 2.2,       # ms refractory period       Lazar et al. 2021
    "t_rfc_input": 0.0,  # ms refractory period of Poisson-driven neurons (Shiu: set to 0)
    "t_dly": 1.8,       # ms synaptic delay          Paul et al. 2015
    "w_syn": 0.275,     # mV per synapse, the model's one free parameter (fit on FlyWire)
    "f_poi": 250,       # Poisson event = f_poi * w_syn, enough to make the target spike
}

# The male CNS has 745 synapses per neuron to FlyWire's 393, so Shiu's w_syn overdrives it. runs/calibrate_wsyn.py
# reruns Shiu's FlyWire feeding experiment (sugar GRNs -> MN9) and picks the male-CNS scale that comes closest
# to it among those where strong drive does not run away: 0.47 (MN9 35 Hz at 200 Hz one-sided sugar, FlyWire
# 92 Hz; at 0.48 JO-CE drive already grows without bound). results/calibrate_wsyn.json has the sweep.
W_SYN_SCALE = 0.47
W_SYN = PARAMS["w_syn"] * W_SYN_SCALE


class Engine:
    """B flies, one connectome. `inputs` are the neurons that receive Poisson drive (set with drive())."""

    def __init__(self, brain, flies, inputs=(), params=None, device=None, seed=0, silence=()):
        self.p = p = dict(PARAMS, **(params or {}))
        self.B, self.N = flies, brain.n
        self.dev = dev = torch.device(device or "cpu")
        self.ptr, self.post, self.syn = brain.on(dev)
        dt = p["dt"]
        self.delay = max(1, round(p["t_dly"] / dt))
        self.decay_g = math.exp(-dt / p["tau"])
        self.decay_v = math.exp(-dt / p["t_mbr"])
        self.g_to_v = p["tau"] / (p["tau"] - p["t_mbr"]) * (self.decay_g - self.decay_v)
        self.v_th, self.v_rst = p["v_th"] - p["v_0"], p["v_rst"] - p["v_0"]  # relative to rest
        self.w_syn, self.kick = p["w_syn"], p["w_syn"] * p["f_poi"]

        self.inputs = torch.as_tensor(np.array(inputs, dtype=np.int64), device=dev)
        self.is_input = torch.zeros(self.N, dtype=torch.bool, device=dev)
        self.is_input[self.inputs] = True
        self.rfc = torch.full((self.N,), round(p["t_rfc"] / dt), dtype=torch.int32, device=dev)
        self.rfc[self.inputs] = round(p["t_rfc_input"] / dt)
        self.transmits = torch.ones(self.N, dtype=torch.bool, device=dev)  # silenced neurons spike but have no effect
        self.transmits[torch.as_tensor(np.array(silence, dtype=np.int64), device=dev)] = False
        self.p_fire = torch.zeros(self.B, len(self.inputs), device=dev)
        self.seed = seed
        self.reset()

    def reset(self, seed=None):
        B, N, dev = self.B, self.N, self.dev
        self.rng = torch.Generator(device=dev).manual_seed(self.seed if seed is None else seed)
        self.v = torch.zeros(B, N, device=dev)  # membrane potential minus v_0
        self.g = torch.zeros(B, N, device=dev)
        self.free_at = torch.zeros(B, N, dtype=torch.int32, device=dev)  # first step at which a neuron integrates again
        self.count = torch.zeros(B, N, dtype=torch.int32, device=dev)    # spikes since reset
        self.in_flight = [torch.empty(0, dtype=torch.int64, device=dev) for _ in range(self.delay)]
        self.t = 0
        self.seconds = 0.0

    def drive(self, hz):
        """Poisson rates of the input neurons in Hz: (n_inputs,) for every fly, or (flies, n_inputs)."""
        if torch.is_tensor(hz):
            hz = hz.to(self.dev, torch.float32)
        else:
            hz = torch.as_tensor(np.array(hz, dtype=np.float32), device=self.dev)
        self.p_fire = (hz * (self.p["dt"] / 1000.0)).expand(self.B, len(self.inputs)).contiguous()

    def _deliver(self, spikes, live):
        """Add the synaptic input of `spikes` (flat fly * N + neuron indices) to g of the `live` neurons."""
        N = self.N
        fly, pre = torch.div(spikes, N, rounding_mode="floor"), spikes % N
        keep = self.transmits[pre]
        fly, pre = fly[keep], pre[keep]
        start = self.ptr[pre]
        fan_out = self.ptr[pre + 1] - start
        total = int(fan_out.sum())
        if total == 0:
            return
        owner = torch.repeat_interleave(torch.arange(len(pre), device=self.dev), fan_out, output_size=total)
        first = torch.cumsum(fan_out, 0) - fan_out  # where each spike's edges begin in the expanded list
        edge = start[owner] + torch.arange(total, device=self.dev) - first[owner]
        target = fly[owner] * N + self.post[edge]
        self.g.view(-1).index_add_(0, target, self.syn[edge] * self.w_syn * live.view(-1)[target])

    @torch.no_grad()
    def step(self):
        """Advance every fly by dt. Returns this step's spikes as flat fly * N + neuron indices."""
        t, v, g = self.t, self.v, self.g
        live = self.free_at <= t
        torch.where(live, v * self.decay_v + g * self.g_to_v, v, out=v)
        torch.where(live, g * self.decay_g, g, out=g)
        firing = (v > self.v_th) & live
        spikes = torch.nonzero(firing.view(-1)).squeeze(1)
        live &= ~firing

        slot = t % self.delay
        if self.in_flight[slot].numel():
            self._deliver(self.in_flight[slot], live)
        self.in_flight[slot] = spikes
        if len(self.inputs):
            hit = torch.rand(self.p_fire.shape, generator=self.rng, device=self.dev) < self.p_fire
            v[:, self.inputs] += (hit & live[:, self.inputs]) * self.kick

        if spikes.numel():
            v.view(-1)[spikes] = self.v_rst
            g.view(-1)[spikes] = 0.0
            self.free_at.view(-1)[spikes] = t + self.rfc[spikes % self.N]
            self.count.view(-1)[spikes] += 1
        self.t = t + 1
        return spikes

    def spikes(self):
        """Spikes of every neuron since the last reset: (flies, N) int32."""
        return self.count

    def run(self, ms):
        """Advance every fly by `ms`."""
        t0 = time.time()
        for _ in range(round(ms / self.p["dt"])):
            self.step()
        if self.dev.type == "cuda":
            torch.cuda.synchronize(self.dev)
        self.seconds += time.time() - t0


@torch.no_grad()
def record(engine, ms, bin_ms=10.0, neurons=(), verbose=False):
    """Run `engine` (Engine or GraphEngine, already driven) for `ms` and keep what an experiment reports:
    mean_hz (N,) each neuron's rate averaged over the flies; binned (flies, len(neurons), bins) spike counts of the
    chosen neurons per bin; undriven_hz (bins,) spikes/s of all neurons without Poisson input, per fly."""
    neurons = torch.as_tensor(np.array(neurons, dtype=np.int64), device=engine.dev)
    bins = math.ceil(ms / bin_ms)
    binned = torch.zeros(bins, engine.B, len(neurons), dtype=torch.int32, device=engine.dev)
    undriven = torch.zeros(bins, dtype=torch.int64, device=engine.dev)
    previous = engine.spikes().clone()
    for b in range(bins):
        engine.run(min(bin_ms, ms - b * bin_ms))
        now = engine.spikes().clone()
        in_bin, previous = now - previous, now
        binned[b] = in_bin[:, neurons]
        undriven[b] = in_bin[:, ~engine.is_input].sum()
        if verbose and (b + 1) % max(1, bins // 10) == 0:
            print(f"    {(b + 1) * bin_ms:7.0f} of {ms:.0f} ms after {engine.seconds:5.1f}s wall", flush=True)
    return {"mean_hz": (engine.spikes().double().mean(0) * (1000.0 / ms)).cpu().numpy(),
            "binned": binned.permute(1, 2, 0).cpu().numpy(), "bin_ms": bin_ms,
            "undriven_hz": undriven.cpu().numpy() * (1000.0 / bin_ms) / engine.B,
            "flies": engine.B, "ms": ms, "wall_s": engine.seconds, "device": str(engine.dev)}


def experiment(brain, inputs, hz, *, flies=30, ms=1000.0, bin_ms=10.0, record_neurons=(), params=None, seed=0,
               silenced=(), device=None, verbose=False):
    """Drive the `inputs` neurons with Poisson input at `hz` (one rate, or one per input) in `flies` independent
    flies for `ms`; see record() for what comes back."""
    eng = Engine(brain, flies, inputs, params=params, device=device, seed=seed, silence=silenced)
    eng.drive(np.broadcast_to(np.asarray(hz, dtype=np.float32), (len(eng.inputs),)))
    return record(eng, ms, bin_ms, record_neurons, verbose)

"""brain/engine.py's model with static shapes, so a run of steps can be recorded once as a CUDA Graph and replayed.

Engine.step has data-dependent sizes (how many neurons fired, how many synapses those spikes reach), which costs a
GPU->CPU round trip or two per 0.1 ms step: for small batches the Python and launch overhead dominates. Here every
step runs the same kernels on the same buffers:

  * spikes: the neurons that fire are packed into K slots (prefix sum, then searchsorted for the 1st..Kth one);
    empty slots name a scratch neuron past the end of the state, which has no synapses and soaks up stray writes
  * synaptic events: the synapse rows of the spikes arriving this step are laid out over exactly S slots
    (repeat_interleave with a known output size; a last segment pads the rest and points at the scratch neuron)
  * the step counter, the delay line and the overflow flag stay on the GPU
Running out of K or S cannot be noticed inside a graph, so it is flagged on the GPU and raised after the run.

Update order and rules are Engine's (Brian2's): integrate, threshold, events from t_dly ago and Poisson input onto
non-refractory neurons only, reset. Poisson draws come from the default CUDA generator, which graphs can replay.
tests/test_graph.py checks this against Engine spike for spike.
"""
import math
import time

import numpy as np
import torch

from .engine import PARAMS, record


class GraphEngine:
    """B flies on one GPU, steps recorded `steps_per_graph` at a time. Same arguments as Engine, plus buffer sizes:
    k_spikes (spikes per step, all flies) and s_events (synaptic events per step)."""

    def __init__(self, brain, flies, inputs=(), params=None, device="cuda", seed=0, silence=(),
                 k_spikes=None, s_events=None, steps_per_graph=100):
        self.p = p = dict(PARAMS, **(params or {}))
        self.dev = dev = torch.device(device)
        if dev.type != "cuda":
            raise ValueError("GraphEngine needs a CUDA device; use brain.engine.Engine on the CPU")
        self.B, self.N = B, N = flies, brain.n
        self.BN = BN = B * N  # flat index of the scratch neuron
        # defaults: ~20k spikes/s per fly is 2 per step, x ~150 synapses each; both leave >= 10x headroom
        self.K = K = int(k_spikes or 256 + 32 * B)
        self.S = S = int(s_events or 32768 + 6144 * B)
        dt = p["dt"]
        self.delay = max(1, round(p["t_dly"] / dt))
        self.decay_g = math.exp(-dt / p["tau"])
        self.decay_v = math.exp(-dt / p["t_mbr"])
        self.g_to_v = p["tau"] / (p["tau"] - p["t_mbr"]) * (self.decay_g - self.decay_v)
        self.v_th, self.v_rst = p["v_th"] - p["v_0"], p["v_rst"] - p["v_0"]
        self.w_syn, self.kick = p["w_syn"], p["w_syn"] * p["f_poi"]

        ptr, self.post, self.syn = brain.on(dev)
        self.ptr = torch.cat([ptr, ptr[-1:]])  # neuron N = scratch, no synapses
        self.transmits = torch.ones(N + 1, dtype=torch.bool, device=dev)
        self.transmits[torch.as_tensor(np.array(silence, dtype=np.int64), device=dev)] = False
        self.transmits[N] = False

        self.inputs = torch.as_tensor(np.array(inputs, dtype=np.int64), device=dev)
        self.is_input = torch.zeros(N, dtype=torch.bool, device=dev)
        self.is_input[self.inputs] = True
        rfc = torch.full((N,), round(p["t_rfc"] / dt), dtype=torch.int32, device=dev)
        rfc[self.inputs] = round(p["t_rfc_input"] / dt)
        self.rfc = torch.cat([rfc.repeat(B), torch.zeros(1, dtype=torch.int32, device=dev)])
        self.input_flat = (torch.arange(B, device=dev)[:, None] * N + self.inputs[None, :]).reshape(-1)
        self.p_fire = torch.zeros(len(self.input_flat), device=dev)

        self.v = torch.zeros(BN + 1, device=dev)  # membrane potential minus v_0; [BN] is the scratch neuron
        self.g = torch.zeros(BN + 1, device=dev)
        self.free_at = torch.zeros(BN + 1, dtype=torch.int32, device=dev)
        self.count = torch.zeros(BN + 1, dtype=torch.int32, device=dev)
        self.ring = torch.full((self.delay, K), BN, dtype=torch.int64, device=dev)  # spike slots of the last t_dly
        self.t = torch.zeros((), dtype=torch.int64, device=dev)
        self.overflow = torch.zeros((), dtype=torch.bool, device=dev)
        self.k_rank = torch.arange(1, K + 1, dtype=torch.int32, device=dev)
        self.k_owner = torch.arange(K + 1, device=dev)
        self.s_pos = torch.arange(S, device=dev)
        self.ones_k = torch.ones(K, dtype=torch.int32, device=dev)
        self.seed, self.seconds = seed, 0.0
        self.steps_per_graph = steps_per_graph
        self.graph = None

    def reset(self, seed=None):
        """Back to rest, in place (a recorded graph keeps pointing at these buffers)."""
        for x in (self.v, self.g, self.free_at, self.count, self.t, self.overflow):
            x.zero_()
        self.ring.fill_(self.BN)
        torch.cuda.manual_seed(self.seed if seed is None else seed)
        self.seconds = 0.0

    def drive(self, hz):
        """Poisson rates of the inputs in Hz: (n_inputs,) for every fly, or (flies, n_inputs)."""
        hz = torch.as_tensor(np.array(hz, dtype=np.float32), device=self.dev) if not torch.is_tensor(hz) else hz
        hz = hz.to(self.dev, torch.float32).expand(self.B, len(self.inputs)).reshape(-1)
        self.p_fire.copy_(hz * (self.p["dt"] / 1000.0))

    def _step(self):
        N, BN, K, S = self.N, self.BN, self.K, self.S
        v, g, t = self.v, self.g, self.t
        live = self.free_at <= t
        torch.where(live, v * self.decay_v + g * self.g_to_v, v, out=v)
        torch.where(live, g * self.decay_g, g, out=g)
        firing = (v > self.v_th) & live
        live &= ~firing

        # pack this step's spikes into K slots; slot k holds the (k+1)-th firing neuron, or the scratch neuron
        running = torch.cumsum(firing, 0, dtype=torch.int32)
        spikes = torch.searchsorted(running, self.k_rank).clamp_(max=BN)
        self.overflow |= running[-1] > K

        # synaptic events of the spikes that fired t_dly ago, laid out over S slots
        row = torch.remainder(t, self.delay).view(1)
        arriving = self.ring.index_select(0, row).view(-1)
        scratch = arriving == BN
        fly = torch.where(scratch, 0, torch.div(arriving, N, rounding_mode="floor"))
        pre = torch.where(scratch, N, arriving % N)
        start = self.ptr[pre]
        fan = torch.where(self.transmits[pre], self.ptr[pre + 1] - start, 0)
        before = torch.cumsum(fan, 0) - fan
        fan_fit = torch.clamp(torch.minimum(fan, S - before), min=0)
        used = fan_fit.sum()
        self.overflow |= used < fan.sum()
        owner = torch.repeat_interleave(self.k_owner, torch.cat([fan_fit, (S - used).view(1)]), output_size=S)
        real = owner < K
        owner = owner.clamp(max=K - 1)
        edge = torch.where(real, start[owner] + self.s_pos - (torch.cumsum(fan_fit, 0) - fan_fit)[owner], 0)
        target = torch.where(real, fly[owner] * N + self.post[edge], BN)
        g.index_add_(0, target, torch.where(real, self.syn[edge], 0.0) * self.w_syn * live[target])
        self.ring.index_copy_(0, row, spikes.view(1, K))

        # Poisson input, then reset of this step's spikes
        hit = (torch.rand(self.p_fire.shape, device=self.dev) < self.p_fire) & live[self.input_flat]
        v.index_add_(0, self.input_flat, hit * self.kick)
        v.index_fill_(0, spikes, self.v_rst)
        g.index_fill_(0, spikes, 0.0)
        self.free_at.index_copy_(0, spikes, (t + self.rfc[spikes]).to(torch.int32))
        self.count.index_add_(0, spikes, self.ones_k)
        t += 1

    def _record(self):
        side = torch.cuda.Stream(self.dev)
        side.wait_stream(torch.cuda.current_stream(self.dev))
        with torch.cuda.stream(side):
            for _ in range(3):  # warm-up allocations outside the graph
                self._step()
        torch.cuda.current_stream(self.dev).wait_stream(side)
        self.graph = torch.cuda.CUDAGraph()
        with torch.cuda.graph(self.graph):
            for _ in range(self.steps_per_graph):
                self._step()
        self.reset()

    @torch.no_grad()
    def run(self, ms):
        """Advance every fly by `ms`; whole graphs where possible, single steps for the rest."""
        if self.graph is None:
            self._record()
        steps = round(ms / self.p["dt"])
        t0 = time.time()
        for _ in range(steps // self.steps_per_graph):
            self.graph.replay()
        for _ in range(steps % self.steps_per_graph):
            self._step()
        torch.cuda.synchronize(self.dev)
        self.seconds += time.time() - t0

    def spikes(self):
        """Spikes of every neuron since the last reset: (flies, N) int32 (a view, do not modify)."""
        return self.count[:self.BN].view(self.B, self.N)

    def check(self):
        if bool(self.overflow):
            raise RuntimeError(f"more than k_spikes={self.K} spikes or s_events={self.S} synaptic events in a step; "
                               "raise them and rerun")


def graph_experiment(brain, inputs, hz, *, flies=30, ms=1000.0, bin_ms=10.0, record_neurons=(), params=None, seed=0,
                     silenced=(), device="cuda", verbose=False, k_spikes=None, s_events=None, steps_per_graph=None):
    """brain.engine.experiment on a GraphEngine; one graph covers `steps_per_graph` steps (default: the largest
    divisor of a bin's steps up to 100)."""
    steps_per_bin = round(bin_ms / PARAMS["dt"])
    per_graph = steps_per_graph or max(d for d in range(1, min(steps_per_bin, 100) + 1) if steps_per_bin % d == 0)
    eng = GraphEngine(brain, flies, inputs, params=params, device=device, seed=seed, silence=silenced,
                      k_spikes=k_spikes, s_events=s_events, steps_per_graph=per_graph)
    eng.drive(np.broadcast_to(np.asarray(hz, dtype=np.float32), (len(eng.inputs),)))
    eng._record()
    result = record(eng, ms, bin_ms, record_neurons, verbose)
    eng.check()
    return dict(result, steps_per_graph=per_graph)

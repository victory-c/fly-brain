"""The brain with a body in the loop: brain/engine.py's Engine, read out in windows.

Each fly in the batch gets its own sensory rates, the state carries over between calls, and run(ms) returns
what a controller needs from that window: spike counts of the readout neurons and of the whole brain.

    loop = BrainLoop(brain, n_run=32, stim_idx=sensory, readout_idx=descending, device="cuda")
    loop.set_rates(hz)            # (32, n_sensory) Hz
    counts, pop = loop.run(10.0)  # 10 ms of brain time -> (32, n_descending) spikes, (32,) spikes
"""
import numpy as np
import torch

from .engine import Engine


class BrainLoop:
    def __init__(self, brain, n_run, stim_idx, readout_idx, params=None, device=None, seed=0, silence_idx=()):
        self.engine = Engine(brain, n_run, stim_idx, params=params, device=device, seed=seed, silence=silence_idx)
        self.B, self.N, self.dev = n_run, brain.n, self.engine.dev
        self.readout_idx = torch.as_tensor(np.asarray(readout_idx, dtype=np.int64), device=self.dev)
        self.undriven = ~self.engine.is_input
        self._taken = torch.zeros_like(self.engine.count)

    @property
    def t(self):
        return self.engine.t

    @property
    def seconds(self):
        return self.engine.seconds

    def reset(self, seed=None):
        self.engine.reset(seed)
        self._taken.zero_()

    def set_rates(self, rates_hz):
        """rates_hz: (n_run, n_stim) Hz, or (n_stim,) for the same rates in every fly."""
        self.engine.drive(rates_hz)

    def take_counts(self):
        """Spike counts of every neuron since the last call (or reset): (B, N) int32."""
        now = self.engine.count.clone()
        out, self._taken = now - self._taken, now
        return out

    def run(self, ms):
        """Advance by `ms`. Returns (readout spike counts (B, R) int32, spikes of undriven neurons (B,) int64)."""
        before = self.engine.count.clone()
        self.engine.run(ms)
        spikes = self.engine.count - before
        return spikes[:, self.readout_idx], spikes[:, self.undriven].sum(1)

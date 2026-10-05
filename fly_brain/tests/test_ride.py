"""Closed-loop pieces on a toy brain and the bare bike (no connectome needed; CPU is fine).

    python -m pytest tests/test_ride.py
"""
import math

import numpy as np
import torch

from bike.dynamics import Peloton
from brain.loop import BrainLoop
from tests.test_engine import toy


def test_bike_self_stability_and_pd_rider():
    # self-stable at 6 m/s, falls at 3 m/s, and a PD rider holds it at 3 m/s in gusts
    torch.manual_seed(0)
    bikes = Peloton(4, seed=1)
    bikes.reset(6.0, phi0_deg=3.0)
    for _ in range(500):
        bikes.step(torch.zeros(4), torch.zeros(4), torch.zeros(4), n_sub=10)
    lean = bikes.state[:, 4].abs().max().item()
    print(f"6 m/s, hands off, 5 s: max |lean| {math.degrees(lean):.2f} deg, fallen {int(bikes.done.sum())}/4")
    assert not bikes.done.any() and lean < math.radians(1.0)

    bikes.reset(3.0, phi0_deg=3.0)
    for _ in range(500):
        bikes.step(torch.zeros(4), torch.zeros(4), torch.zeros(4), n_sub=10)
    print(f"3 m/s, hands off, 5 s: fallen {int(bikes.done.sum())}/4")
    assert bikes.done.all()

    bikes.reset(3.0, phi0_deg=3.0, gust_nm=15.0)
    for _ in range(1000):
        bikes.step(bikes.pd_oracle(), torch.full((4,), 60.0), torch.zeros(4), n_sub=10)
    s = bikes.state
    print(f"3 m/s, PD rider, gusts 15 Nm, 10 s: fallen {int(bikes.done.sum())}/4, |y| {s[:, 1].abs().max():.2f} m, "
          f"v {s[:, 3].mean():.2f} m/s, x {s[:, 0].mean():.1f} m")
    assert not bikes.done.any() and s[:, 1].abs().max() < 1.0


def test_loop_keeps_riders_apart_and_carries_state_over(tmp_path):
    """A relay chain 0 -> 1 -> 2 with feed-forward inhibition 3 -| 2; each rider gets its own drive."""
    b = toy(tmp_path, 4, [(0, 1, 260.0), (1, 2, 260.0), (3, 2, -500.0)])
    loop = BrainLoop(b, n_run=3, stim_idx=[0, 3], readout_idx=[0, 1, 2], seed=4)
    loop.set_rates(np.array([[120.0, 0.0], [120.0, 200.0], [0.0, 0.0]]))  # relay, relay under inhibition, silent
    per_window = [loop.run(5.0)[0] for _ in range(200)]                   # 200 windows of 5 ms = 1 s
    hz = torch.stack(per_window).sum(0).float().numpy()
    assert loop.t == 10000
    assert abs(hz[0, 0] - 120) < 15 and abs(hz[1, 0] - 120) < 15  # driven neuron follows its Poisson rate
    assert hz[0, 1] > 20 and hz[0, 2] > 5                          # the relay carries it two synapses on
    assert hz[1, 2] < hz[0, 2] / 3                                 # inhibition on the last stage
    assert hz[2].sum() == 0                                        # an undriven rider stays silent

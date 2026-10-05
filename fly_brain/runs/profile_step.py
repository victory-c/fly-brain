"""Profile the static-shape step of brain/graph_engine.py, run eagerly (no graph), to see which kernels dominate."""
import argparse

from torch.profiler import ProfilerActivity, profile

from brain import stimuli
from brain.connectome import Brain
from brain.engine import W_SYN
from brain.graph_engine import GraphEngine

ap = argparse.ArgumentParser()
ap.add_argument("--trials", type=int, default=8)
ap.add_argument("--steps", type=int, default=200)
a = ap.parse_args()
sugar = stimuli.group("sugar")
eng = GraphEngine(Brain(), a.trials, sugar, params={"w_syn": W_SYN})
eng.drive([stimuli.SHIU_HZ] * len(sugar))
for _ in range(50):  # warm-up
    eng._step()
with profile(activities=[ProfilerActivity.CUDA, ProfilerActivity.CPU]) as prof:
    for _ in range(a.steps):
        eng._step()
print(prof.key_averages().table(sort_by="cuda_time_total", row_limit=22, max_name_column_width=60))

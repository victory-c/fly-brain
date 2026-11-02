"""bike/readout.py: per-brain top-k / random-k readouts and the sensory bypass (no connectome needed)."""
import numpy as np
import pandas as pd
import torch

from bike.readout import Readout, bypass_groups, screen_pool, topk_groups


def fake_meta_and_screen(n=60, seed=0):
    rng = np.random.default_rng(seed)
    sup = np.array(["descending_neuron"] * 30 + ["vnc_motor"] * 10 + ["ol_sensory"] * 10 + ["cb_intrinsic"] * 10)
    types = np.array([f"DN{i % 7}" for i in range(n)], dtype=object)
    side = np.array(["L", "R"] * (n // 2))
    meta = pd.DataFrame({"row": np.arange(n), "bodyId": 10000 + np.arange(n), "type": types,
                         "instance": [f"{t}_{s}" for t, s in zip(types, side)], "superclass": sup, "somaSide": side})
    screen = meta.drop(columns=["somaSide"]).copy()
    screen["driven"] = sup == "ol_sensory"
    screen["mean_hz"] = rng.uniform(1, 40, n)
    screen.loc[[0, 1], "mean_hz"] = 0.1                       # two DNs that stay silent
    screen["r_phi_dot"] = rng.uniform(-0.3, 0.3, n)
    screen.loc[[5, 6, 7], "r_phi_dot"] = [0.9, -0.8, 0.7]      # the three best roll-rate DNs
    screen.loc[45, "r_phi_dot"] = 0.95                         # a driven sensory neuron: never a candidate
    screen.loc[0, "r_phi_dot"] = 0.99                          # silent: never a candidate
    return meta, screen


def test_topk_ranks_this_brains_own_dns_and_skips_driven_and_silent():
    meta, screen = fake_meta_and_screen()
    pool = screen_pool(screen, meta)
    assert set(pool["superclass"]) == {"descending_neuron"} and not pool["driven"].any() and (pool["mean_hz"] >= 0.5).all()
    g = topk_groups(screen, meta, 3)
    assert [int(r[0]) for _, _, r in g] == [5, 6, 7]
    assert g[0][0] == "DN5_R#10005" and g[0][1] == ""


def test_randk_is_a_reproducible_draw_from_the_same_pool():
    meta, screen = fake_meta_and_screen()
    a = topk_groups(screen, meta, 8, random=True, seed=1)
    b = topk_groups(screen, meta, 8, random=True, seed=1)
    c = topk_groups(screen, meta, 8, random=True, seed=2)
    rows = lambda g: [int(r[0]) for _, _, r in g]
    assert rows(a) == rows(b) and rows(a) != rows(c) and len(set(rows(a))) == 8
    pool_rows = set(screen_pool(screen, meta)["row"])
    assert set(rows(a)) <= pool_rows and set(rows(c)) <= pool_rows


def test_readout_from_groups_has_one_feature_per_neuron():
    meta, screen = fake_meta_and_screen()
    r = Readout(meta, groups=topk_groups(screen, meta, 4))
    assert r.n_features == 4 and len(r.idx) == 4 and list(r.idx) == [5, 6, 7] + list(r.idx[3:])
    counts = torch.tensor([[10, 0, 5, 1], [0, 0, 0, 0]])
    f = r.features(counts, 100.0)                      # 100 ms window -> Hz
    assert torch.allclose(f, torch.tensor([[100.0, 0.0, 50.0, 10.0], [0.0, 0.0, 0.0, 0.0]]))
    assert r.names[0] == "DN5_R#10005"
    assert len(r.forward) == 0 and len(r.mdn) == 0 and r.gf_spikes(counts).sum() == 0


def test_bypass_reads_the_driven_sensory_neurons_by_population():
    class FakeSenses:
        names = ["VS_L", "VS_R", "HALT"]
        pops = {"VS_L": np.array([40, 41]), "VS_R": np.array([42, 43, 44]), "HALT": np.array([45])}
    meta, _ = fake_meta_and_screen()
    g = bypass_groups(FakeSenses())
    assert [(n, s, len(r)) for n, s, r in g] == [("VS_L", "", 2), ("VS_R", "", 3), ("HALT", "", 1)]
    r = Readout(meta, groups=g)
    assert r.names == ["VS_L", "VS_R", "HALT"] and list(r.idx) == [40, 41, 42, 43, 44, 45]
    f = r.features(torch.tensor([[2, 4, 3, 3, 3, 9]]), 1000.0)
    assert torch.allclose(f, torch.tensor([[3.0, 3.0, 9.0]]))   # mean rate per population


def test_type_readout_unchanged():
    meta, _ = fake_meta_and_screen()
    r = Readout(meta, types=["DN0", "DN1", "nonexistent"])
    assert r.types == ["DN0", "DN1"] and r.names == ["DN0_L", "DN0_R", "DN1_L", "DN1_R"]

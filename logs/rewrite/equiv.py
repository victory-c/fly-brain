"""Old engine (brain/sim.py, upstream-derived) vs new engine (brain/engine.py) on the same stimuli."""
import sys, json, time, numpy as np
sys.path.insert(0, '.')
from brain import sim as old
from brain.connectome import Brain
from brain.engine import simulate, W_SYN_MALE_CNS
from brain import stimuli as S
ob = old.Brain('/home/s/st/stevejobs/flybrain/fly_brain/brain.npz'); nb = Brain()
mn9 = S.mn9(); out = {}
B, T = 64, 1000.0
for name, idx in [("sugar", S.group("sugar")), ("bitter", S.group("bitter")), ("sugar+bitter", np.r_[S.group("sugar"), S.group("bitter")])]:
    runs = {
      "old": lambda s: old.simulate(ob, idx, np.full(len(idx), 150.0), n_run=B, t_run=T, params={"w_syn": W_SYN_MALE_CNS}, progress=False, device="cuda", seed=s),
      "new_equiv": lambda s: simulate(nb, idx, 150.0, n_run=B, t_run=T, params={"w_syn": W_SYN_MALE_CNS, "t_rfc_input": 2.2}, progress=False, device="cuda", seed=s),
      "new_shiu": lambda s: simulate(nb, idx, 150.0, n_run=B, t_run=T, params={"w_syn": W_SYN_MALE_CNS}, progress=False, device="cuda", seed=s),
    }
    res = {}
    for k, f in runs.items():
        a, b = f(1), f(2)   # two seeds each, to see seed-to-seed noise
        res[k] = (a, b)
        print(f"{name:13s} {k:9s} MN9 {a['rate'][mn9].round(1)} / {b['rate'][mn9].round(1)}  spikes/s {a['rate'].sum():,.0f} / {b['rate'].sum():,.0f}  {a['seconds']:.1f}s", flush=True)
    rest = np.ones(nb.n, bool); rest[idx] = False
    def cmp(x, y):
        x, y = x['rate'][rest], y['rate'][rest]; act = (x > 0) | (y > 0)
        return dict(corr=float(np.corrcoef(x[act], y[act])[0, 1]), total_ratio=float(y.sum() / x.sum()), active=int(act.sum()))
    out[name] = {"old_vs_old(seed)": cmp(res["old"][0], res["old"][1]), "old_vs_new_equiv": cmp(res["old"][0], res["new_equiv"][0]),
                 "new_equiv(seed)": cmp(res["new_equiv"][0], res["new_equiv"][1]), "old_vs_new_shiu": cmp(res["old"][0], res["new_shiu"][0]),
                 "mn9": {k: [float(v[0]['rate'][mn9].mean()), float(v[1]['rate'][mn9].mean())] for k, v in res.items()},
                 "seconds": {k: v[0]['seconds'] for k, v in res.items()}}
    print(json.dumps(out[name]), flush=True)
json.dump(out, open('../logs/rewrite/equiv.json', 'w'), indent=1)

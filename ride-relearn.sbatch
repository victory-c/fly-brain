#!/bin/bash
# The bike on the rewritten simulator (brain/engine.py, Shiu's Brian2 rules, w_syn scale 0.47): everything the
# learning-from-blank run (ride-attempts.sbatch) takes from earlier runs is remade first, then the same search.
#   1) runs.probe: which HS/VS/haltere-driven neurons carry the lane cue -> $OUT/probe.json (the lane filter)
#   2) ride_slow_mu replayed 16 x 20 s on seed 7 -> $OUT/ride_slow_mu_trace.json
#   3) zbar (mean input of each decoder weight while riding, as in lane-next.sbatch step 0) -> $OUT/zbar_mu.npy
#   4) cross-entropy search from the blank decoder, 48 riders x 15 s, every attempt logged -> $OUT/attempts/
# Steps 1-3 are skipped when their output exists (they do not depend on 4); 4 always starts afresh.
# Submit from the repo root: sbatch ride-relearn.sbatch [OUT=results/relearn] [minutes for 4)=165]
#SBATCH --job-name=ride-relearn
#SBATCH --partition=ocf-hpc
#SBATCH --nodelist=corruption
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:30:00
#SBATCH --output=logs/ride-relearn-%j.out
set -euo pipefail
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
cd "$SLURM_SUBMIT_DIR/fly_brain"
PY=/home/s/st/stevejobs/flybrain/venv-cuda/bin/python
OUT=${1:-results/relearn}; MIN=${2:-165}
mkdir -p $OUT/attempts
[ -s $OUT/attempts/init_blank.json ] || cp results/relearn/attempts/init_blank.json $OUT/attempts/  # blank decoder
LANE="--readout lane --lane hs --gains hs_heading=150,hs_lane=50 --v0 5.5 --gust 5"

echo "== $(date +%T) 1) probe"
[ -s $OUT/probe.json ] || $PY -m runs.probe --pop HS VS HALT --extra 30 --brains 16 --ms 1000 --out $OUT/probe.json 2>&1 | tail -3

echo "== $(date +%T) 2) ride_slow_mu trace"
[ -s $OUT/ride_slow_mu_trace.json ] || $PY -m runs.ride --replay results/ride_slow_mu.json --tau-lane-ms 300 \
  --lane-filter $OUT/probe.json $LANE --riders 16 --seconds 20 --seed 7 --trace $OUT/ride_slow_mu_trace.json 2>&1 | grep -E "^replay|Error"

echo "== $(date +%T) 3) zbar"
[ -s $OUT/zbar_mu.npy ] || $PY - $OUT <<'PYEOF'
import json, sys
from pathlib import Path
import numpy as np
from bike.readout import LANE_DNS
out = Path(sys.argv[1])
d = json.load(open(out / "ride_slow_mu_trace.json"))
names, tn = d["dn_names"], d["theta_names"]
X = np.array([r["dn_hz"] for r in d["trace"]], np.float32)
S = np.array([r["state"] for r in d["trace"]], np.float32)
A = ~np.array([r["done"] for r in d["trace"]]) & (np.abs(S[:, :, 1]) < 3.5)
f0 = X[0].mean(0)
cen = np.array([n.rsplit("_", 1)[0] in LANE_DNS for n in names])
by = {}
for r in json.load(open(out / "probe.json"))["HS"]:
    if abs(r["z"]) >= 3.0: by.setdefault((r["type"], r["somaSide"]), []).append(r["diff"])
v = np.array([np.mean(by[tuple(n.rsplit("_", 1))]) if tuple(n.rsplit("_", 1)) in by else 0.0 for n in names], np.float32)
w = v / max(float((v ** 2).sum()), 1e-6)
fbar, F = X[A].mean(0), len(names)
zb = np.zeros(len(tn), np.float32)
zb[:F] = np.where(cen, fbar - f0, fbar) / 50.0
zb[tn.index("steer:lane_filter")] = (fbar - f0) @ w
np.save(out / "zbar_mu.npy", zb)
print(f"zbar: {A.sum()} on-road samples, |z| uncentred {np.linalg.norm(zb[:F][~cen]):.2f}, lane signal {zb[-1]:+.3f}")
PYEOF

echo "== $(date +%T) 4) learning from a blank decoder"
rm -f $OUT/attempts/gen*.npz $OUT/attempts/attempts.json $OUT/attempts/cem.json
$PY -m runs.ride --init-theta $OUT/attempts/init_blank.json --sigma-new 0.1 --sigma0 0.3 --sigma-lane-filter 1.0 --sigma-min 0.03 --sigma-pedal 0 \
  --center-batch --zbar $OUT/zbar_mu.npy --readout lane --lane hs --lane-filter $OUT/probe.json --tau-lane-ms 300 \
  --gains hs_heading=150,hs_lane=50 --v0 5.5 --gust 5 --offroad 3.5 --lane-penalty 0.02 \
  --riders 48 --seconds 15 --generations 80 --max-minutes $MIN --seed 101 --out $OUT/attempts/cem.json --log-attempts $OUT/attempts
echo "== done $(date)"

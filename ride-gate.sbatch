#!/bin/bash
# Balance gate (Scrambled Brains W0): can the real male CNS learn to ride from a blank decoder BELOW the bike's
# self-stable speed (the Tarmac + 70 kg is self-stable at 4.7-7.7 m/s; the relearn run at 5.5 m/s got balance free)?
# Same pipeline and CEM settings as ride-relearn.sbatch, except speed, seed and the frozen pedal/brake terms:
# the blank decoder of the relearn run pedals ~80 W, which accelerates a 4.0 m/s start past 4.7 m/s in ~4.7 s
# (4.5 m/s: 1.5 s) and so back into the self-stable range. Here pedalling is frozen at the power that HOLDS V0
# (pedal gain 0, bias = logit(P_hold/250 W); 23.1 W at 4.0, 29.6 W at 4.5) and the brake is off, so only
# steering is learned and the speed stays at V0 for the whole episode (job 37487 was cancelled for this).
#   1) lane filter: reuse results/relearn/probe.json (the probe holds the bike upright, so it does not depend on speed)
#   2) ride_slow_mu replayed 16 x 20 s at V0 -> trace, 3) zbar at that operating point, 4) CEM from blank, 48 riders x 15 s
# Per-generation upright_mean / finish_frac / distance_mean land in $OUT/cem.json "history"; compare with
# results/relearn/attempts/cem.json (5.5 m/s). Submit from the repo root:
#   sbatch ride-gate.sbatch V0 SEED [MINUTES=300]      e.g. sbatch ride-gate.sbatch 4.0 201
#SBATCH --job-name=ride-gate
#SBATCH --partition=ocf-hpc
#SBATCH --nodelist=corruption
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=06:00:00
#SBATCH --output=logs/ride-gate-%j.out
set -euo pipefail
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
cd "$SLURM_SUBMIT_DIR/fly_brain"
PY=${PY:-$SLURM_SUBMIT_DIR/venv-cuda/bin/python}
V0=${1:?speed m/s}; SEED=${2:?seed}; MIN=${3:-300}
OUT=results/gate/v${V0}_s${SEED}
mkdir -p $OUT
cp -n results/relearn/probe.json $OUT/
# blank steering + speed-holding pedal, brake off -> $OUT/init_hold.json
$PY - $V0 $OUT <<PYEOF
import json, math, sys
from bike.dynamics import Peloton
from bike.tarmac import G, LONGITUDINAL as L
v0, out = float(sys.argv[1]), sys.argv[2]
mT = Peloton(1).mT
P = v0 * (0.5 * L["rho"] * L["CdA"] * v0 * v0 + L["Crr"] * mT * G) / L["drivetrain"]
theta = [0.0, 0.0, math.log(P / (250.0 - P)), 0.0, -12.0]
json.dump({"best_theta": theta, "decoder_names": ["steer:bias", "pedal:gain", "pedal:bias", "brake:gain", "brake:bias"],
           "note": f"blank steering, pedal frozen at {P:.1f} W (holds {v0} m/s), brake off"}, open(f"{out}/init_hold.json", "w"))
print(f"init_hold: {P:.1f} W holds {v0} m/s")
PYEOF
LANE="--readout lane --lane hs --gains hs_heading=150,hs_lane=50 --v0 $V0 --gust 5"
echo "== $(date +%T) gate v0=$V0 seed=$SEED, max $MIN min"

echo "== $(date +%T) 2) ride_slow_mu trace at v0=$V0"
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

echo "== $(date +%T) 4) CEM from a blank decoder at v0=$V0"
$PY -m runs.ride --init-theta $OUT/init_hold.json --sigma-new 0.1 --sigma0 0.3 --sigma-lane-filter 1.0 --sigma-min 0.03 --sigma-pedal 0 \
  --center-batch --zbar $OUT/zbar_mu.npy --readout lane --lane hs --lane-filter $OUT/probe.json --tau-lane-ms 300 \
  --gains hs_heading=150,hs_lane=50 --v0 $V0 --gust 5 --offroad 3.5 --lane-penalty 0.02 \
  --riders 48 --seconds 15 --generations 80 --max-minutes $MIN --seed $SEED --out $OUT/cem.json
echo "== done $(date)"

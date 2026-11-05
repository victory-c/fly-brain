#!/bin/bash
# Riding on a per-brain readout (Scrambled Brains, Track A pipeline): CEM from a blank decoder at a held speed,
# like the balance gate (ride-gate.sbatch), but the decoder reads neurons that this brain's own passenger screen
# picked, not the hand-picked type list. No lane filter, no probe, no zbar: every feature is read as its deviation
# from the batch-mean warm-up rate, and the search starts from a silent steering decoder.
#   READOUT topk   the K descending neurons the screen ranks highest by roll-rate correlation
#           randk  K drawn at random from the same pool (READOUT_SEED picks the draw)
#           bypass the 10 sensory populations themselves (ceiling; needs no screen)
# RUNG is r0 (the real wiring) or results/variants/<RUNG>.npz; its screen is results/rungs/screens/<RUNG>[_w<SCALE>].parquet
# (screen-rungs.sbatch). Results: results/rungs/<RUNG>[_w<SCALE>]/<readout>/v<V0>_s<SEED>/cem.json.
# Submit from the repo root:
#   sbatch ride-readout.sbatch V0 SEED RUNG READOUT [K=8] [MINUTES=300] [W_SYN_SCALE] [READOUT_SEED=0]
#   e.g. sbatch ride-readout.sbatch 4.5 201 r0 topk 8        sbatch ride-readout.sbatch 4.5 201 r0 bypass
# Resubmitting the same command continues the search from $OUT/cem.json (runs/ride.py --resume).
#SBATCH --job-name=ride-readout
#SBATCH --partition=ocf-hpc
#SBATCH --nodelist=corruption
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=06:00:00
#SBATCH --output=logs/ride-readout-%j.out
set -euo pipefail
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
cd "$SLURM_SUBMIT_DIR/fly_brain"
PY=${PY:-$SLURM_SUBMIT_DIR/venv-cuda/bin/python}
V0=${1:?speed m/s}; SEED=${2:?seed}; RUNG=${3:?r0 or a rung}; RO=${4:?topk|randk|bypass}; K=${5:-8}; MIN=${6:-300}; WS=${7:-}; RSEED=${8:-0}
WARG=${WS:+--w-syn-scale $WS}; TAG=${RUNG}${WS:+_w$WS}
if [ "$RUNG" = r0 ]; then BARG=""; else BARG="--brain results/variants/$RUNG.npz"; fi
case $RO in
  topk)   NAME=top$K;            RARG="--readout topk --screen results/rungs/screens/$TAG.parquet --k $K" ;;
  randk)  NAME=rand${K}_r$RSEED; RARG="--readout randk --screen results/rungs/screens/$TAG.parquet --k $K --readout-seed $RSEED" ;;
  bypass) NAME=bypass;           RARG="--readout bypass" ;;
  *) echo "READOUT must be topk, randk or bypass" >&2; exit 2 ;;
esac
OUT=results/rungs/$TAG/$NAME/v${V0}_s${SEED}
mkdir -p $OUT
# blank steering + speed-holding pedal, brake off -> $OUT/init_hold.json (as in ride-gate.sbatch)
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
echo "== $(date +%T) CEM from a blank decoder: $TAG, $NAME, v0=$V0, seed $SEED, max $MIN min"
$PY -m runs.ride $BARG $WARG $RARG --init-theta $OUT/init_hold.json --sigma-new 0.1 --sigma0 0.3 --sigma-min 0.03 --sigma-pedal 0 \
  --center-all --center-batch --lane hs --gains hs_heading=150,hs_lane=50 --v0 $V0 --gust 5 --offroad 3.5 --lane-penalty 0.02 \
  --riders 48 --seconds 15 --generations 80 --max-minutes $MIN --seed $SEED --out $OUT/cem.json --resume $OUT/cem.json
echo "== done $(date)"

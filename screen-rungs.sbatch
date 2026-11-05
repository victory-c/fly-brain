#!/bin/bash
# Per-brain passenger screens for the wiring ladder (Scrambled Brains, Track A readouts): a PD rider steers, the
# brain watches, and every neuron's rate is correlated with the bike's roll rate (runs/screen.py). Each rung gets
# its own screen, so `runs/ride.py --readout topk|randk --screen results/rungs/screens/<RUNG>.parquet` never uses a
# neuron list picked on the real wiring. r0 is the real wiring; other rungs are results/variants/<RUNG>.npz.
# Submit from the repo root:
#   sbatch screen-rungs.sbatch "RUNGS" [W_SYN_SCALE]      e.g. sbatch screen-rungs.sbatch "r0 r1_s1 r2_s1 r3_s1"
#   with a scale the files are <RUNG>_w<SCALE>.*          e.g. sbatch screen-rungs.sbatch r4_s1 1.5
#SBATCH --job-name=screen-rungs
#SBATCH --partition=ocf-hpc
#SBATCH --nodelist=corruption
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=40G
#SBATCH --time=02:00:00
#SBATCH --output=logs/screen-rungs-%j.out
set -euo pipefail
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
cd "$SLURM_SUBMIT_DIR/fly_brain"
PY=${PY:-$SLURM_SUBMIT_DIR/venv-cuda/bin/python}
RUNGS=${1:?rungs, e.g. "r0 r3_s1"}; WS=${2:-}; WARG=${WS:+--w-syn-scale $WS}
mkdir -p results/rungs/screens
for r in $RUNGS; do
  if [ "$r" = r0 ]; then BARG=""; else BARG="--brain results/variants/$r.npz"; fi
  out=results/rungs/screens/${r}${WS:+_w$WS}
  [ -s $out.parquet ] && { echo "have $out.parquet"; continue; }
  echo "== $(date +%T) screen $r ${WS:+scale $WS}"
  $PY -m runs.screen $BARG $WARG --riders 48 --seconds 15 --lane hs --seed 1 --out $out.json 2>&1 | grep -E "^screen|t=1[05]\.0s|descending neurons above|driven neurons total|Error|Traceback" || true
  [ -s $out.parquet ] || { echo "screen failed for $r"; exit 1; }
done
echo "== done $(date)"

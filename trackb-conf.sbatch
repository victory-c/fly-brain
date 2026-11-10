#!/bin/bash
# Track B, confirmatory (Scrambled Brains preregistration, tag prereg-v1, section 6): runs/predictions.py on rewiring draws, both taste
# sides, 30 flies, 1 s, seed 0, into results/track_b/confirmatory/<rung>_s<draw>[_w<scale>].json. A brain with a file is skipped, so a cut
# job can be submitted again. A draw not already in results/variants is made on the node's disk and removed after its run.
#   sbatch trackb-conf.sbatch r0                                  the real wiring, the reference for scoring
#   sbatch trackb-conf.sbatch "r1 r2" 101 110                     rungs, first and last draw, at scale 0.47
#   sbatch trackb-conf.sbatch r4 3 5 1.2                          the same at another scale
# Score: python3 tools/track_b_score.py fly_brain/results/track_b/confirmatory --by-rung
#SBATCH --job-name=trackb-conf
#SBATCH --partition=ocf-hpc
#SBATCH --nodelist=corruption
#SBATCH --gres=none
#SBATCH --cpus-per-task=16
#SBATCH --mem=24G
#SBATCH --time=02:30:00
#SBATCH --output=logs/trackb-conf-%j.out
set -euo pipefail
export OMP_NUM_THREADS=16
cd "$SLURM_SUBMIT_DIR/fly_brain"
PY=${PY:-$SLURM_SUBMIT_DIR/venv-cuda/bin/python}
RUNGS=${1:?rungs}; FIRST=${2:-0}; LAST=${3:-0}; WS=${4:-}
O=results/track_b/confirmatory; mkdir -p $O
if [ "$RUNGS" = r0 ]; then
  [ -s $O/r0.json ] || $PY -m runs.predictions --taste-side both --out $O/r0.json
  echo "== done $(date)"; exit 0
fi
TMP=$(mktemp -d)
trap 'rm -r "$TMP"' EXIT
for rung in $RUNGS; do for draw in $(seq $FIRST $LAST); do
  name=${rung}_s$draw; out=$O/$name${WS:+_w$WS}.json
  [ -s $out ] && { echo "have $out"; continue; }
  brain=results/variants/$name.npz
  if [ ! -s $brain ]; then brain=$TMP/$name.npz; $PY -m brain.variants $rung --seed $draw --out $brain | tail -1; fi
  echo "== $(date +%T) $name ${WS:+scale $WS}"
  $PY -m runs.predictions --taste-side both --brain $brain ${WS:+--w-syn-scale $WS} --out $out | tail -1
  case $brain in "$TMP"/*) rm "$brain";; esac
done; done
echo "== done $(date)"

#!/bin/bash
# Transmission pre-test (runs/pretest.py, docs/GLOSSARY.md "Transmission gate") on the GPU for a list of rungs and
# synapse scales: VS and haltere probes, 30 brains per cell (the confirmatory size; the null is 1,000 random balanced
# relabellings). r0 is the real wiring; any other rung is results/variants/<RUNG>.npz (brain/variants.py).
# A cell whose json exists is skipped, so the job can be resubmitted. Submit from the repo root:
#   sbatch pretest-rungs.sbatch "RUNGS" ["SCALES"=0.47] [BRAINS=30]
#   e.g. sbatch pretest-rungs.sbatch "r35_s1 r4_s1 r5_s1" "0.47 0.6 0.8 1 1.5 2"
#SBATCH --job-name=pretest
#SBATCH --partition=ocf-hpc
#SBATCH --nodelist=corruption
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --output=logs/pretest-%j.out
set -euo pipefail
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
cd "$SLURM_SUBMIT_DIR/fly_brain"
PY=${PY:-$SLURM_SUBMIT_DIR/venv-cuda/bin/python}
RUNGS=${1:?rungs, e.g. "r0 r3_s1"}; SCALES=${2:-0.47}; B=${3:-30}
for r in $RUNGS; do
  if [ "$r" = r0 ]; then BARG=""; else BARG="--brain results/variants/$r.npz"; fi
  for s in $SCALES; do
    out=results/rungs/pretest_${r}_b${B}_w${s}.json
    [ -s $out ] && { echo "have $out"; continue; }
    $PY -m runs.pretest $BARG --tag $r --brains $B --pop VS HALT --w-syn-scale $s --out $out
  done
done
echo "== done $(date)"

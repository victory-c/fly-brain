#!/bin/bash
#SBATCH --job-name=flyride
#SBATCH --partition=ocf-hpc
#SBATCH --nodelist=corruption
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=06:00:00
#SBATCH --output=logs/flyride-%j.out
#SBATCH --error=logs/flyride-%j.err
# The fly rides a Tarmac SL9. Examples:
#   sbatch ride.sbatch --oracle
#   sbatch ride.sbatch --open-loop --riders 8 --seconds 5
#   sbatch ride.sbatch --riders 32 --generations 12 --seconds 10
#   sbatch ride.sbatch --replay results/ride.json --riders 4
set -euo pipefail
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
cd "$SLURM_SUBMIT_DIR/fly_brain"  # submit from the repo root
echo "== $(date) on $(hostname): python -m runs.ride $*"
"${PY:-$SLURM_SUBMIT_DIR/venv-cuda/bin/python}" -m runs.ride "$@"
echo "== done $(date)"

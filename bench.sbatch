#!/bin/bash
#SBATCH --job-name=flybench
#SBATCH --partition=ocf-hpc
#SBATCH --nodelist=corruption
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=32
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=logs/flybench-%j.out
#SBATCH --error=logs/flybench-%j.err
set -euo pipefail
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
cd "$SLURM_SUBMIT_DIR/fly_brain"  # submit from the repo root
"${PY:-$SLURM_SUBMIT_DIR/venv-cuda/bin/python}" -m runs.bench_gpu "$@"

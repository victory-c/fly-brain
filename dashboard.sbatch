#!/bin/bash
#SBATCH --job-name=flydash
#SBATCH --partition=ocf-hpc
#SBATCH --nodelist=corruption
#SBATCH --cpus-per-task=32
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --output=logs/flydash-%j.out
#SBATCH --error=logs/flydash-%j.err
set -euo pipefail
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
cd "$SLURM_SUBMIT_DIR/fly_brain"  # submit from the repo root
"${PY:-$SLURM_SUBMIT_DIR/venv/bin/python}" -m export.export_dashboard "$@"

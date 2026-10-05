#!/bin/bash
# Derive W_SYN_SCALE from Shiu et al.'s FlyWire model (fly_brain/runs/calibrate_wsyn.py). Submit from the repo root.
#SBATCH --job-name=calibrate-wsyn
#SBATCH --partition=ocf-hpc
#SBATCH --nodelist=corruption
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=96G
#SBATCH --time=04:00:00
#SBATCH --output=logs/calibrate-wsyn-%j.out
set -euo pipefail
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
cd "$SLURM_SUBMIT_DIR/fly_brain"
/home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.calibrate_wsyn "$@"

#!/bin/bash
#SBATCH --job-name=flylane
#SBATCH --partition=ocf-hpc
#SBATCH --nodelist=corruption
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=03:00:00
#SBATCH --output=logs/flylane-%j.out
#SBATCH --error=logs/flylane-%j.err
# Lane-keeping pipeline: passenger screen with the HS lane cue -> teacher-initialised CEM -> replay of the best.
set -euo pipefail
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
cd "$SLURM_SUBMIT_DIR/fly_brain"  # submit from the repo root
PY=${PY:-$SLURM_SUBMIT_DIR/venv-cuda/bin/python}
echo "== $(date) screen"
$PY -m runs.screen --riders 16 --seconds 8 --lane hs --out results/screen_lane.json
echo "== $(date) train"
$PY -m runs.ride --init results/screen_lane_samples.npz --lane hs --riders 48 --generations 15 --seconds 10 \
    --sigma0 0.1 --lane-penalty 0.05 --seed 2 --out results/ride_lane.json
echo "== $(date) replay"
$PY -m runs.ride --replay results/ride_lane.json --lane hs --riders 16 --seconds 20 --seed 7 --trace results/ride_lane_trace.json
echo "== done $(date)"

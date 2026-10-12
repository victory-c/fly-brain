#!/bin/bash
#SBATCH --job-name=flydagger
#SBATCH --partition=ocf-hpc
#SBATCH --nodelist=corruption
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --output=logs/flydagger-%j.out
#SBATCH --error=logs/flydagger-%j.err
# Lane keeping by DAgger: the fly rides, the PD rider labels every visited state, the decoder is refit.
set -euo pipefail
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
cd "$SLURM_SUBMIT_DIR/fly_brain"  # submit from the repo root
PY=${PY:-$SLURM_SUBMIT_DIR/venv-cuda/bin/python}
echo "== $(date) dagger"
$PY -m runs.ride --init results/screen_lane_samples.npz --lane hs --dagger 8 --riders 48 --seconds 12 --lane-penalty 0.05 --seed 3 --out results/ride_dagger.json
echo "== $(date) replay"
$PY -m runs.ride --replay results/ride_dagger.json --lane hs --riders 16 --seconds 20 --seed 7 --trace results/ride_dagger_trace.json
echo "== done $(date)"

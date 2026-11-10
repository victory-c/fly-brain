#!/bin/bash
# Held-out replays of finished Scrambled Brains searches (tools/heldout.py, which submits this). CPU by default; a GPU with --gres=gpu:1.
#   sbatch [-J name] heldout.sbatch CONDITIONS CEM.json [CEM.json ...]    CONDITIONS: comma-separated, e.g. gust301,gust302,vplus,vminus
#SBATCH --job-name=heldout
#SBATCH --partition=ocf-hpc
#SBATCH --nodelist=corruption
#SBATCH --cpus-per-task=32
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=logs/heldout-%j.out
set -euo pipefail
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-32}
cd "$SLURM_SUBMIT_DIR"
PY=${PY:-$SLURM_SUBMIT_DIR/venv-cuda/bin/python}
CONDITIONS=${1:?conditions}; shift
$PY tools/heldout.py run --conditions "$CONDITIONS" "$@"
echo "== done $(date)"

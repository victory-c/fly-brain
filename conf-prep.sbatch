#!/bin/bash
# Rewiring draws 3 to 5 of R1, R2 and R3 for the confirmatory runs of the Scrambled Brains preregistration (tag prereg-v1,
# section 5). Already-made draws are skipped. CPU only; the login VM is too small for the connectome. Submit from the repo root:
#   sbatch conf-prep.sbatch
#SBATCH --job-name=conf-prep
#SBATCH --partition=ocf-hpc
#SBATCH --nodelist=corruption
#SBATCH --gres=none
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=00:40:00
#SBATCH --output=logs/conf-prep-%j.out
set -euo pipefail
cd "$SLURM_SUBMIT_DIR/fly_brain"
PY=${PY:-$SLURM_SUBMIT_DIR/venv-cuda/bin/python}
for rung in r1 r2 r3; do for draw in 3 4 5; do
  [ -s results/variants/${rung}_s$draw.npz ] && { echo "have ${rung}_s$draw"; continue; }
  $PY -m brain.variants $rung --seed $draw
done; done
echo "== done $(date)"

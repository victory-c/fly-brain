#!/bin/bash
# Track C spike-count replays of finished Scrambled Brains searches (tools/track_c_replay.py). CPU only.
#   sbatch [-J name] trackc.sbatch [--rows ROWS.json] CEM.json [CEM.json ...]
#   sbatch -J tc-verify trackc.sbatch --pilot-r0                 the pilot R0 replay (38178) at 10 ms bins, then
#       tools/track_c_verify.py against the pilot's 100 ms files -> fly_brain/results/track_c/confirmatory/verify.json
#SBATCH --job-name=trackc
#SBATCH --partition=ocf-hpc
#SBATCH --nodelist=corruption
#SBATCH --gres=none
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=01:30:00
#SBATCH --output=logs/trackc-%j.out
set -euo pipefail
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
cd "$SLURM_SUBMIT_DIR"
PY=${PY:-$SLURM_SUBMIT_DIR/venv-cuda/bin/python}
$PY tools/track_c_replay.py "$@"
pilot=0; dry=0
for arg in "$@"; do
  case "$arg" in --pilot-r0) pilot=1 ;; --dry-run) dry=1 ;; esac
done
if [ $pilot = 1 ] && [ $dry = 0 ]; then
  echo "== $(date +%T) verify the 10 ms pilot replay"
  $PY tools/track_c_verify.py   # exit 1 (job FAILED) when verify.json says ok=false
fi
echo "== done $(date)"

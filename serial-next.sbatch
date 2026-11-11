#!/bin/bash
# Relay of the Scrambled Brains queue (tools/submit_serial.py --next): waits for one link, then submits the next link and
# another relay after it, so the queue holds one link at a time. One CPU, a few seconds.
#SBATCH --job-name=serial-next
#SBATCH --partition=ocf-hpc
#SBATCH --nodelist=corruption
#SBATCH --gres=none
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:10:00
#SBATCH --output=logs/serial-next-%j.out
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
echo "== $(date) after job ${SLURM_JOB_DEPENDENCY:-?}"
${PY:-$SLURM_SUBMIT_DIR/venv-cuda/bin/python} tools/submit_serial.py --next

#!/bin/bash
# Track C analyses over the 13 confirmatory brains (tools/track_c_all.py), after all 13 replays and both new screens exist.
# CPU only; one mode per job (the relay's tc-n90, tc-calcium, tc-probe links). A brain whose output exists is skipped,
# so a job cut by the time limit is resumed by submitting it again.
#   sbatch -J tc-n90 --time=03:00:00 trackc-analysis.sbatch n90        ~2 min/brain in the pilot (38185: 4 brains in 7 min)
#   sbatch -J tc-calcium trackc-analysis.sbatch calcium                 plan: 1.5-3 h for 13 brains
#   sbatch -J tc-probe trackc-analysis.sbatch probe                     plan: 2-3 h for 13 brains (needs the n90 outputs)
#SBATCH --job-name=trackc-analysis
#SBATCH --partition=ocf-hpc
#SBATCH --nodelist=corruption
#SBATCH --gres=none
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=10:00:00
#SBATCH --output=logs/trackc-analysis-%j.out
set -euo pipefail
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
cd "$SLURM_SUBMIT_DIR"
PY=${PY:-$SLURM_SUBMIT_DIR/venv-cuda/bin/python}
MODE=${1:?mode: n90, calcium or probe}; shift
echo "== $(date) track C $MODE"
$PY tools/track_c_all.py "$MODE" "$@"
echo "== done $(date)"

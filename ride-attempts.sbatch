#!/bin/bash
#SBATCH --job-name=flyattempt
#SBATCH --partition=ocf-hpc
#SBATCH --nodelist=corruption
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:05:00
#SBATCH --output=/home/s/st/stevejobs/flybrain/logs/flyattempt-%j.out
#SBATCH --error=/home/s/st/stevejobs/flybrain/logs/flyattempt-%j.err
# Learning to ride from a blank decoder, every attempt recorded (the /ride/ attempts page).
# Blank = no steering weights, pedal ~80 W, brake off (results/attempts/init_blank.json); cross-entropy search over the
# 91 decoder numbers at road speed (5.5 m/s, 5 Nm gusts, leaving the 7 m road ends the run), with the round-2 fixes
# (batch centring, bias searched at the riding operating point, pedal/brake frozen). 48 riders x 15 s per generation;
# each rider of each generation is one attempt: bike state every 50 ms, region rates every 100 ms, the whole brain for
# the population mean, the record and the earliest/longest failure of each generation -> results/attempts/gen*.npz.
set -euo pipefail
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
cd /home/s/st/stevejobs/flybrain/fly_brain
PY=/home/s/st/stevejobs/flybrain/venv-cuda/bin/python
OUT=${1:-results/attempts}; MIN=${2:-170}
echo "== $(date) attempts -> $OUT"
$PY -m runs.ride --init-theta $OUT/init_blank.json --sigma-new 0.1 --sigma0 0.3 --sigma-lane-filter 1.0 --sigma-min 0.03 --sigma-pedal 0 \
  --center-batch --zbar results/lane/zbar_mu.npy --readout lane --lane hs --lane-filter results/probe.json --tau-lane-ms 300 \
  --gains hs_heading=150,hs_lane=50 --v0 5.5 --gust 5 --offroad 3.5 --lane-penalty 0.02 \
  --riders 48 --seconds 15 --generations 80 --max-minutes $MIN --seed 101 --out $OUT/cem.json --log-attempts $OUT
echo "== done $(date)"

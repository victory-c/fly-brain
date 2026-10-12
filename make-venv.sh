#!/usr/bin/env bash
# Make the Python environment the code runs in, next to this script:
#   bash make-venv.sh          # venv/       CPU torch: laptop, tests, the notebook without a GPU
#   bash make-venv.sh cuda     # venv-cuda/  torch for CUDA 12.1, on the GPU node (cuda-venv.sbatch runs this there)
# Safe to re-run: an existing environment is brought up to requirements.txt, not rebuilt.
# PYTHON=python3.12 bash make-venv.sh picks the interpreter (3.11 or newer).
set -euo pipefail
cd "$(dirname "$0")"
PYTHON=${PYTHON:-python3}
case "${1:-cpu}" in
  cpu)  VENV=venv
        if [ "$(uname)" = Darwin ]; then TORCH=(torch); else TORCH=(torch --index-url https://download.pytorch.org/whl/cpu); fi ;;
  cuda) VENV=venv-cuda
        TORCH=(torch --index-url https://download.pytorch.org/whl/cu121)
        export PIP_CACHE_DIR=${PIP_CACHE_DIR:-$PWD/.pip-cache} ;;  # the node's home quota is small
  *)    echo "usage: bash make-venv.sh [cpu|cuda]" >&2; exit 2 ;;
esac
"$PYTHON" -c 'import sys; sys.exit(sys.version_info < (3, 11))' || { echo "need Python 3.11+, got $("$PYTHON" -V)" >&2; exit 1; }
[ -x "$VENV/bin/python" ] || "$PYTHON" -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/python" -c 'import torch' 2>/dev/null || "$VENV/bin/pip" install -q "${TORCH[@]}"
"$VENV/bin/pip" install -q -r requirements.txt
"$VENV/bin/python" -c 'import numpy, pandas, pyarrow, torch; print("ok:", "torch", torch.__version__, "numpy", numpy.__version__, "pandas", pandas.__version__)'
echo "activate with: source $VENV/bin/activate"

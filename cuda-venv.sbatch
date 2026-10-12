#!/bin/bash
# Build venv-cuda/ (make-venv.sh cuda: torch for CUDA 12.1) on the GPU node and check the GPU works.
# Submit from the repo root: sbatch cuda-venv.sbatch
#SBATCH --job-name=cudavenv
#SBATCH --partition=ocf-hpc
#SBATCH --nodelist=corruption
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=logs/cudavenv-%j.out
#SBATCH --error=logs/cudavenv-%j.err
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
bash make-venv.sh cuda
venv-cuda/bin/python - <<'PY'
import torch
print("torch", torch.__version__, "cuda build", torch.version.cuda, "available", torch.cuda.is_available())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0))
    x = torch.randn(4096, 4096, device="cuda"); torch.cuda.synchronize()
    import time; t=time.time(); (x@x).sum().item(); torch.cuda.synchronize(); print("matmul ok", round(time.time()-t,3), "s")
PY

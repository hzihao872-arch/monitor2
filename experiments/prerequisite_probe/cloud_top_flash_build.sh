#!/usr/bin/env bash
set -euo pipefail
BASE=/root/autodl-tmp/monitor2
export PATH="/root/miniconda3/bin:/usr/local/cuda-12.8/bin:$PATH"
export CUDA_HOME=/usr/local/cuda-12.8
export PIP_CACHE_DIR=/root/autodl-tmp/pip_cache
export TMPDIR=/root/autodl-tmp/tmp
export MAX_JOBS=8
export NVCC_THREADS=4
export FLASH_ATTN_CUDA_ARCHS=120
export TORCH_CUDA_ARCH_LIST=12.0
export FLASH_ATTENTION_FORCE_BUILD=TRUE
"$BASE/.venv-topreward/bin/python" -m pip install -v --no-build-isolation flash-attn==2.8.3
"$BASE/.venv-topreward/bin/python" - <<'PY'
import flash_attn, torch, transformers
print('TOP_ENV', torch.__version__, torch.version.cuda, transformers.__version__, flash_attn.__version__, torch.cuda.get_device_name(0))
PY

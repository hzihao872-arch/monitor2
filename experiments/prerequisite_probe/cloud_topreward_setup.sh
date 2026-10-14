#!/usr/bin/env bash
set -euo pipefail

BASE=/root/autodl-tmp/monitor2
VENV="$BASE/.venv-topreward"
export PATH="/root/miniconda3/bin:/usr/local/cuda-12.8/bin:$PATH"
export CUDA_HOME=/usr/local/cuda-12.8
export HF_HOME=/root/autodl-tmp/hf
export PIP_CACHE_DIR=/root/autodl-tmp/pip_cache
export TMPDIR=/root/autodl-tmp/tmp
export MAX_JOBS=8
export FLASH_ATTN_CUDA_ARCHS=120

python -m venv --system-site-packages "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip wheel setuptools ninja packaging
"$VENV/bin/python" -m pip install \
    transformers==4.57.1 accelerate==1.12.0 \
    'qwen-vl-utils[decord]==0.0.14' opencv-python-headless loguru \
    huggingface-hub safetensors
"$VENV/bin/python" -m pip install --no-deps -e "$BASE/research/sources/TOPReward"
"$VENV/bin/python" -m pip install --no-build-isolation flash-attn==2.8.3
"$VENV/bin/python" - <<'PY'
import flash_attn, torch, transformers
print('TOP_ENV', torch.__version__, torch.version.cuda, transformers.__version__, flash_attn.__version__, torch.cuda.get_device_name(0))
PY

"$VENV/bin/python" - <<'PY'
from huggingface_hub import snapshot_download
path = snapshot_download(
    'Qwen/Qwen3-VL-8B-Instruct',
    revision='0c351dd01ed87e9c1b53cbc748cba10e6187ff3b',
    cache_dir='/root/autodl-tmp/hf/hub',
)
print('TOP_SNAPSHOT', path)
PY

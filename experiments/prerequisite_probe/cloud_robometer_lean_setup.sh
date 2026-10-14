#!/usr/bin/env bash
set -euo pipefail
BASE=/root/autodl-tmp/monitor2
export PATH="/root/miniconda3/bin:/usr/local/cuda-12.8/bin:$PATH"
export UV_CACHE_DIR=/root/autodl-tmp/uv_cache
export UV_HTTP_TIMEOUT=120
export UV_NO_PROGRESS=1
export UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple
export TMPDIR=/root/autodl-tmp/tmp
PY="$BASE/.venv-robometer/bin/python"
cd /root/autodl-tmp
uv pip install --python "$PY" \
  'torch==2.8.0' 'torchvision==0.23.0' 'xformers==0.0.32.post2' \
  'torchao==0.17.0' 'unsloth==2026.9.14' 'transformers==4.57.6' \
  'trl==0.24.0' 'accelerate==1.15.0' 'qwen-vl-utils[decord]==0.0.14' \
  'numpy==1.26.4' 'matplotlib>=3.5' 'datasets==4.3.0' \
  'peft' 'hydra-core' 'omegaconf' 'pyrallis' 'sentence-transformers' \
  'wandb' 'codetiming' 'tensorboard' 'loguru' 'bitsandbytes' \
  'opencv-python-headless' 'opencv-contrib-python-headless' 'rich' \
  'seaborn' 'h5py' 'evaluate' 'safetensors' 'tyro' 'soundfile' \
  'uvicorn' 'fastapi' 'imageio' 'moviepy' 'gymnasium' 'decord'
uv pip install --python "$PY" --no-deps -e "$BASE/research/sources/robometer"
"$PY" -c 'import torch, transformers, unsloth; print("ROB_ENV", torch.__version__, torch.version.cuda, torch.cuda.is_available(), transformers.__version__, unsloth.__version__)'
PYTHONPATH="$BASE/research/sources/robometer" "$PY" "$BASE/research/sources/robometer/scripts/example_inference_local.py" --help

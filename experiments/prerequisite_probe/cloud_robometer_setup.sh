#!/usr/bin/env bash
set -euo pipefail

BASE=/root/autodl-tmp/monitor2
export PATH="/root/miniconda3/bin:/usr/local/cuda-12.8/bin:$PATH"
export CUDA_HOME=/usr/local/cuda-12.8
export HF_HOME=/root/autodl-tmp/hf
export UV_CACHE_DIR=/root/autodl-tmp/uv_cache
export TMPDIR=/root/autodl-tmp/tmp
export UV_PROJECT_ENVIRONMENT="$BASE/.venv-robometer"
export UV_HTTP_TIMEOUT=120
mkdir -p "$UV_CACHE_DIR" "$TMPDIR"

python -m pip install --upgrade uv
cd "$BASE/research/sources/robometer"
uv python install 3.10
uv sync --extra robometer --python 3.10

"$UV_PROJECT_ENVIRONMENT/bin/python" - <<'PY'
import platform, torch, transformers
print('ROB_ENV', platform.python_version(), torch.__version__, torch.version.cuda, transformers.__version__, torch.cuda.get_device_name(0))
PY

"$UV_PROJECT_ENVIRONMENT/bin/python" - <<'PY'
from huggingface_hub import snapshot_download
for repo, revision in [
    ('robometer/Robometer-4B', 'beef63bc914c5c189329d49c6d712d96d632aa34'),
    ('Qwen/Qwen3-VL-4B-Instruct', 'ebb281ec70b05090aa6165b016eac8ec08e71b17'),
]:
    path = snapshot_download(repo, revision=revision, cache_dir='/root/autodl-tmp/hf/hub')
    print('ROB_SNAPSHOT', repo, path)
PY

#!/usr/bin/env bash
set -euo pipefail
BASE=/root/autodl-tmp/monitor2
export PATH="/root/miniconda3/bin:/usr/local/cuda-12.8/bin:$PATH"
export UV_CACHE_DIR=/root/autodl-tmp/uv_cache
export UV_PROJECT_ENVIRONMENT="$BASE/.venv-robometer"
export UV_HTTP_TIMEOUT=120
export UV_NO_PROGRESS=1
export UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple
export TMPDIR=/root/autodl-tmp/tmp
cd "$BASE/research/sources/robometer"
uv sync --extra robometer --python 3.10 -v

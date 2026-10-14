#!/usr/bin/env bash
set -euo pipefail
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/root/autodl-tmp/hf_xet_test
export HF_XET_CACHE=/root/autodl-tmp/hf_xet_test/xet
export HF_XET_HIGH_PERFORMANCE=1
export HF_HUB_DOWNLOAD_TIMEOUT=120
/root/miniconda3/bin/python -u - <<'PY'
from huggingface_hub import hf_hub_download
path = hf_hub_download(
    repo_id='robometer/Robometer-4B',
    filename='model-00002-of-00002.safetensors',
    revision='beef63bc914c5c189329d49c6d712d96d632aa34',
)
print('ROB_XET_SNAPSHOT', path, flush=True)
PY

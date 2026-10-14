#!/usr/bin/env bash
set -euo pipefail
BASE=/root/autodl-tmp/monitor2
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_OFFLINE=1
export PYTHONPATH="$BASE:$BASE/research/sources/TOPReward"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
PY="$BASE/.venv-topreward/bin/python"
MODEL=/root/autodl-tmp/hf/hub/models--Qwen--Qwen3-VL-8B-Instruct/snapshots/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b
OUT="$BASE/experiments/prerequisite_probe/artifacts/model_results/topreward"
mkdir -p "$OUT"
cd "$BASE"
date --iso-8601=seconds
nvidia-smi
"$PY" -c 'import sys, torch, transformers, flash_attn, accelerate, cv2, importlib.metadata as md; print("VERSIONS", sys.version, torch.__version__, torch.version.cuda, transformers.__version__, flash_attn.__version__, accelerate.__version__, md.version("qwen-vl-utils"), cv2.__version__)'
"$PY" "$BASE/experiments/prerequisite_probe/verify_official_weights.py" \
  --manifest /root/autodl-tmp/official_weight_hashes.json \
  --cache /root/autodl-tmp/hf --repo Qwen/Qwen3-VL-8B-Instruct
"$PY" -u -m experiments.prerequisite_probe.run_topreward_batch_official \
  --model-path "$MODEL" \
  --input-dir "$BASE/experiments/prerequisite_probe/artifacts/model_input" \
  --out-dir "$OUT"
date --iso-8601=seconds
nvidia-smi

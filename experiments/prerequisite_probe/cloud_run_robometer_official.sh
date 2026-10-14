#!/usr/bin/env bash
set -euo pipefail
BASE=/root/autodl-tmp/monitor2
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_OFFLINE=1
export WANDB_MODE=disabled
export MPLBACKEND=Agg
export PYTHONPATH="$BASE/research/sources/robometer"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
PY="$BASE/.venv-robometer/bin/python"
MODEL=/root/autodl-tmp/hf/hub/models--robometer--Robometer-4B/snapshots/beef63bc914c5c189329d49c6d712d96d632aa34
OUT="$BASE/experiments/prerequisite_probe/artifacts/model_results/robometer"
mkdir -p "$OUT"
cd "$BASE"
date --iso-8601=seconds
nvidia-smi
"$PY" -c 'import sys, torch, transformers, unsloth, xformers, decord; print("VERSIONS", sys.version, torch.__version__, torch.version.cuda, transformers.__version__, unsloth.__version__, xformers.__version__, decord.__version__)'
"$PY" "$BASE/experiments/prerequisite_probe/verify_official_weights.py" \
  --manifest /root/autodl-tmp/official_weight_hashes.json \
  --cache /root/autodl-tmp/hf --repo Qwen/Qwen3-VL-4B-Instruct
"$PY" "$BASE/experiments/prerequisite_probe/verify_official_weights.py" \
  --manifest /root/autodl-tmp/official_weight_hashes.json \
  --cache /root/autodl-tmp/hf --repo robometer/Robometer-4B
for number in 0001 0002 0003 0004 0005 0006; do
  VIDEO="$BASE/experiments/prerequisite_probe/artifacts/model_input/$number.mp4"
  OUTPUT="$OUT/$number.npy"
  printf '%q ' "$PY" "$BASE/research/sources/robometer/scripts/example_inference_local.py" \
    --model-path "$MODEL" --video "$VIDEO" \
    --task 'Put the blue cube in the green tray.' --fps 1 --out "$OUTPUT" \
    > "$OUT/$number.command.txt"
  printf '\n' >> "$OUT/$number.command.txt"
  echo "START $number $(date --iso-8601=seconds)"
  "$PY" "$BASE/research/sources/robometer/scripts/example_inference_local.py" \
    --model-path "$MODEL" --video "$VIDEO" \
    --task 'Put the blue cube in the green tray.' --fps 1 --out "$OUTPUT" \
    > "$OUT/$number.log" 2>&1
  echo "COMPLETE $number $(date --iso-8601=seconds)"
done
date --iso-8601=seconds
nvidia-smi

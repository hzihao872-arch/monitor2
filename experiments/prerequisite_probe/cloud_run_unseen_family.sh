#!/usr/bin/env bash
set -euo pipefail
FAMILY=${1:?pass unseen_offset_cell or unseen_pickup_gate_v2}
case "$FAMILY" in unseen_offset_cell|unseen_pickup_gate_v2|unseen_mirror_cell|unseen_left_cell|unseen_pickup_gate_shifted|unseen_rear_cell) ;; *) echo "Unknown family" >&2; exit 2;; esac
BASE=/root/autodl-tmp/monitor2
ROOT="$BASE/experiments/prerequisite_probe/artifacts/$FAMILY"
INPUT="$ROOT/model_input"
OUT="$ROOT/model_results"
TOP_MODEL=/root/autodl-tmp/hf/hub/models--Qwen--Qwen3-VL-8B-Instruct/snapshots/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b
ROB_MODEL=/root/autodl-tmp/hf/hub/models--robometer--Robometer-4B/snapshots/beef63bc914c5c189329d49c6d712d96d632aa34
ROB_REPO="$BASE/research/sources/robometer_pr33_compat"
TOP_PY="$BASE/.venv-topreward/bin/python"
ROB_PY="$BASE/.venv-robometer/bin/python"
mkdir -p "$OUT/topreward" "$OUT/robometer_pr33_compat"
cd "$BASE"
date --iso-8601=seconds
nvidia-smi
sha256sum "$INPUT"/*.mp4 > "$OUT/input_video_sha256.txt"
export HF_HOME=/root/autodl-tmp/hf HF_HUB_OFFLINE=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export PYTHONPATH="$BASE:$BASE/research/sources/TOPReward"
"$TOP_PY" -c 'import sys,torch,transformers,flash_attn; print("TOP_VERSIONS",sys.version,torch.__version__,transformers.__version__,flash_attn.__version__)'
"$TOP_PY" -m experiments.prerequisite_probe.audit_model_decode --backend opencv --input-dir "$INPUT" --out "$OUT/topreward/decoded_frames.json"
printf '%q ' "$TOP_PY" -m experiments.prerequisite_probe.run_topreward_batch_official --model-path "$TOP_MODEL" --input-dir "$INPUT" --out-dir "$OUT/topreward" > "$OUT/topreward/command.txt"
printf '\n' >> "$OUT/topreward/command.txt"
"$TOP_PY" -u -m experiments.prerequisite_probe.run_topreward_batch_official \
  --model-path "$TOP_MODEL" --input-dir "$INPUT" --out-dir "$OUT/topreward" > "$OUT/topreward/run.log" 2>&1
echo "TOP_COMPLETE $FAMILY $(date --iso-8601=seconds)"
export WANDB_MODE=disabled MPLBACKEND=Agg
export PYTHONPATH="$ROB_REPO:$BASE"
"$ROB_PY" -c 'import sys,torch,transformers,unsloth,decord; print("ROB_VERSIONS",sys.version,torch.__version__,transformers.__version__,unsloth.__version__,decord.__version__)'
git -C "$ROB_REPO" rev-parse HEAD
git -C "$ROB_REPO" diff -- robometer/utils/save.py
"$ROB_PY" -m experiments.prerequisite_probe.audit_model_decode --backend robometer --input-dir "$INPUT" --out "$OUT/robometer_pr33_compat/decoded_frames.json"
for number in 0001 0002 0003 0004 0005 0006; do
  video="$INPUT/$number.mp4"
  result="$OUT/robometer_pr33_compat/$number.npy"
  printf '%q ' "$ROB_PY" "$ROB_REPO/scripts/example_inference_local.py" --model-path "$ROB_MODEL" --video "$video" --task 'Put the blue cube in the green tray.' --fps 1 --out "$result" > "$OUT/robometer_pr33_compat/$number.command.txt"
  printf '\n' >> "$OUT/robometer_pr33_compat/$number.command.txt"
  echo "ROB_START $FAMILY $number $(date --iso-8601=seconds)"
  "$ROB_PY" "$ROB_REPO/scripts/example_inference_local.py" --model-path "$ROB_MODEL" --video "$video" --task 'Put the blue cube in the green tray.' --fps 1 --out "$result" > "$OUT/robometer_pr33_compat/$number.log" 2>&1
  echo "ROB_COMPLETE $FAMILY $number $(date --iso-8601=seconds)"
done
date --iso-8601=seconds
nvidia-smi

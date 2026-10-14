#!/usr/bin/env bash
# Read-only checks for the pre-existing rental. Never downloads weights.
set -euo pipefail

BASE=${MONITOR_BASE:-/root/autodl-tmp/monitor2}
HF_HOME=${HF_HOME:-/root/autodl-tmp/hf}
PY="$BASE/.venv-topreward/bin/python"
VERIFY="$BASE/experiments/prerequisite_probe/verify_official_weights.py"
HASHES=/root/autodl-tmp/official_weight_hashes.json
MODEL8="$HF_HOME/hub/models--Qwen--Qwen3-VL-8B-Instruct/snapshots/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b"
MODEL4="$HF_HOME/hub/models--robometer--Robometer-4B/snapshots/beef63bc914c5c189329d49c6d712d96d632aa34"

export HF_HOME HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export PYTHONPATH="$BASE:$BASE/research/sources/TOPReward"
printf 'UTC '; date -u --iso-8601=seconds
printf 'GPU\n'; nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
printf 'Disk\n'; df -h "$BASE" "$HF_HOME"
for path in "$PY" "$VERIFY" "$HASHES" "$MODEL8/config.json" \
  "$BASE/experiments/prerequisite_probe/monitor_contract.py" \
  "$BASE/experiments/prerequisite_probe/run_monitor_qwen.py" \
  "$BASE/experiments/prerequisite_probe/artifacts/model_input/manifest.jsonl" \
  "$BASE/experiments/prerequisite_probe/artifacts/model_input/0001.mp4" \
  "$BASE/new_tests/s01/model_input/manifest.jsonl" \
  "$BASE/new_tests/s02/model_input/manifest.jsonl"; do
  test -e "$path" || { echo "MISSING $path" >&2; exit 2; }
done
"$PY" -c 'import torch, transformers, flash_attn, cv2; print("VERSIONS", torch.__version__, transformers.__version__, flash_attn.__version__, cv2.__version__)'
"$PY" "$VERIFY" --manifest "$HASHES" --cache "$HF_HOME" --repo Qwen/Qwen3-VL-8B-Instruct
if test -f "$MODEL4/config.yaml" && test -x "$BASE/.venv-robometer/bin/python" && \
   test -f "$BASE/research/sources/robometer_pr33_compat/scripts/example_inference_local.py"; then
  if "$PY" "$VERIFY" --manifest "$HASHES" --cache "$HF_HOME" --repo Qwen/Qwen3-VL-4B-Instruct && \
     "$PY" "$VERIFY" --manifest "$HASHES" --cache "$HF_HOME" --repo robometer/Robometer-4B; then
    echo "ROBOMETER_EXISTING_STACK_OK"
  else
    echo "ROBOMETER_EXISTING_WEIGHTS_MISSING; mark baseline unrun, do not download"
  fi
else
  echo "ROBOMETER_EXISTING_STACK_MISSING; mark baseline unrun, do not download"
fi
if test -f "$BASE/research/sources/TOPReward/topreward/clients/qwen.py" && \
   test -f "$BASE/experiments/prerequisite_probe/run_topreward_batch_official.py"; then
  echo "TOPREWARD_EXISTING_SOURCE_OK"
else
  echo "TOPREWARD_EXISTING_SOURCE_MISSING; mark baseline unrun"
fi

"$PY" - "$BASE" <<'PY'
import hashlib, json, sys
from pathlib import Path
base = Path(sys.argv[1])
manifest = json.loads((base / 'new_tests/bundle_manifest.json').read_text())
for entry in manifest['files']:
    path = base / entry['path']
    observed = hashlib.sha256(path.read_bytes()).hexdigest()
    if observed != entry['sha256']:
        raise SystemExit(f"BUNDLE HASH MISMATCH: {entry['path']}")
print('Bundle members verified:', len(manifest['files']))
PY

cd "$BASE"
RUN_ID=$(date -u +%Y%m%dT%H%M%SZ)
OUT="$BASE/new_tests/preflight_$RUN_ID"
mkdir -p "$OUT"
for scene in s01 s02; do
  "$PY" -m experiments.prerequisite_probe.run_monitor_qwen \
    --input-dir "$BASE/new_tests/$scene/model_input" --model-path "$MODEL8" \
    --output "$OUT/$scene.jsonl" --dry-run
done
printf 'PREFLIGHT_OK %s\n' "$OUT"

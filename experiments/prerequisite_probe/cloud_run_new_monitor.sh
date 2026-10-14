#!/usr/bin/env bash
# Explicit stages: smoke on old development input, then frozen new inputs.
set -euo pipefail

STAGE=${1:?Use smoke, development, monitor, topreward, or robometer}
BASE=${MONITOR_BASE:-/root/autodl-tmp/monitor2}
HF_HOME=${HF_HOME:-/root/autodl-tmp/hf}
PY8="$BASE/.venv-topreward/bin/python"
PY4="$BASE/.venv-robometer/bin/python"
MODEL8="$HF_HOME/hub/models--Qwen--Qwen3-VL-8B-Instruct/snapshots/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b"
MODEL4="$HF_HOME/hub/models--robometer--Robometer-4B/snapshots/beef63bc914c5c189329d49c6d712d96d632aa34"
RESULTS="$BASE/new_tests/server_results"
export HF_HOME HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
mkdir -p "$RESULTS"
cd "$BASE"

case "$STAGE" in
  smoke)
    export PYTHONPATH="$BASE:$BASE/research/sources/TOPReward"
    RUN_ID=$(date -u +%Y%m%dT%H%M%SZ)
    OUTPUT="$RESULTS/old_dev_smoke_$RUN_ID.jsonl"
    "$PY8" -m experiments.prerequisite_probe.run_monitor_qwen \
      --input-dir "$BASE/experiments/prerequisite_probe/artifacts/model_input" \
      --model-path "$MODEL8" --output "$OUTPUT" --attention flash_attention_2 --limit 1
    "$PY8" - "$OUTPUT" <<'PY'
import json, sys
rows = [json.loads(line) for line in open(sys.argv[1], encoding='utf-8')]
calls = {row['method']: row for row in rows if row.get('kind') == 'model_call'}
required = {'D', 'P', 'F'}
if not required <= calls.keys() or any(calls[key]['validity'] != 'valid' for key in required):
    raise SystemExit('OLD DEVELOPMENT SMOKE FAILED: inspect all raw outputs before changing a common interface')
print('OLD DEVELOPMENT SMOKE PASSED:', sys.argv[1])
PY
    sha256sum "$BASE/experiments/prerequisite_probe/monitor_contract.py" \
      "$BASE/experiments/prerequisite_probe/run_monitor_qwen.py" > "$RESULTS/smoke_code.sha256"
    ;;
  development)
    export PYTHONPATH="$BASE:$BASE/research/sources/TOPReward"
    (cd / && sha256sum -c "$RESULTS/smoke_code.sha256")
    "$PY8" -m experiments.prerequisite_probe.run_monitor_qwen \
      --input-dir "$BASE/experiments/prerequisite_probe/artifacts/model_input" \
      --model-path "$MODEL8" --output "$RESULTS/old_dev_8b_full.jsonl" \
      --attention flash_attention_2 > "$RESULTS/old_dev_8b_full.log" 2>&1
    sha256sum "$RESULTS/old_dev_8b_full.jsonl" > "$RESULTS/old_dev_8b_full.sha256"
    "$PY8" - "$RESULTS/old_dev_8b_full.jsonl" <<'PY'
import collections, json, sys
rows = [json.loads(line) for line in open(sys.argv[1], encoding='utf-8')]
calls = [row for row in rows if row.get('kind') == 'model_call']
if len(calls) != 24:
    raise SystemExit(f'OLD DEVELOPMENT INCOMPLETE: {len(calls)}/24 model calls')
for method in ('D', 'P', 'F', 'D2_review'):
    records = [row for row in calls if row['method'] == method]
    counts = collections.Counter(row['validity'] for row in records)
    print('OLD DEVELOPMENT', method, dict(counts))
PY
    ;;
  monitor)
    export PYTHONPATH="$BASE:$BASE/research/sources/TOPReward"
    (cd / && sha256sum -c "$RESULTS/smoke_code.sha256")
    for scene in s01 s02; do
      "$PY8" -m experiments.prerequisite_probe.run_monitor_qwen \
        --input-dir "$BASE/new_tests/$scene/model_input" --model-path "$MODEL8" \
        --output "$RESULTS/$scene.monitor.jsonl" --attention flash_attention_2 \
        > "$RESULTS/$scene.monitor.log" 2>&1
      sha256sum "$RESULTS/$scene.monitor.jsonl" > "$RESULTS/$scene.monitor.sha256"
      echo "MONITOR_COMPLETE $scene $(date -u --iso-8601=seconds)"
    done
    ;;
  topreward)
    export PYTHONPATH="$BASE:$BASE/research/sources/TOPReward"
    for scene in s01 s02; do
      OUT="$RESULTS/$scene.topreward"
      test ! -e "$OUT" || { echo "Output exists: $OUT" >&2; exit 2; }
      "$PY8" -u -m experiments.prerequisite_probe.run_topreward_batch_official \
        --model-path "$MODEL8" --input-dir "$BASE/new_tests/$scene/model_input" \
        --out-dir "$OUT" > "$RESULTS/$scene.topreward.log" 2>&1
      echo "TOPREWARD_COMPLETE $scene $(date -u --iso-8601=seconds)"
    done
    ;;
  robometer)
    export WANDB_MODE=disabled MPLBACKEND=Agg
    export PYTHONPATH="$BASE/research/sources/robometer_pr33_compat"
    REPO="$BASE/research/sources/robometer_pr33_compat"
    for scene in s01 s02; do
      OUT="$RESULTS/$scene.robometer_pr33_compat"
      test ! -e "$OUT" || { echo "Output exists: $OUT" >&2; exit 2; }
      mkdir -p "$OUT"
      for number in 0001 0002 0003 0004 0005 0006; do
        echo "ROBOMETER_START $scene $number $(date -u --iso-8601=seconds)"
        "$PY4" "$REPO/scripts/example_inference_local.py" \
          --model-path "$MODEL4" \
          --video "$BASE/new_tests/$scene/model_input/$number.mp4" \
          --task 'Put the blue cube in the green tray.' --fps 1 \
          --out "$OUT/$number.npy" > "$OUT/$number.log" 2>&1
        echo "ROBOMETER_COMPLETE $scene $number $(date -u --iso-8601=seconds)"
      done
    done
    ;;
  *) echo "Unknown stage: $STAGE" >&2; exit 2 ;;
esac

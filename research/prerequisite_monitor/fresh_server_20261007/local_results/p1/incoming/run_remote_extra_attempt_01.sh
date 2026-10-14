#!/usr/bin/env bash
# Run one exploratory task only after P0 raw has been downloaded and verified locally.
set -euo pipefail

BASE=/root/autodl-tmp/monitor2
RUN="${1:?existing P0 run root required}"
LEASE_END_UTC="${2:?provider rental end time in UTC required}"
TASK="${3:?choose p1, p2, or p3}"
case "$RUN" in "$BASE"/fresh_prerequisite_runs/*) ;; *) exit 2 ;; esac
test -f "$RUN/raw_seal.json"
test -f "$RUN/p0_local_verified.sha256"
test "$(cat "$RUN/p0_local_verified.sha256")" = "$(sha256sum "$RUN/raw_seal.json" | cut -d' ' -f1)"

PY8="$BASE/.venv-topreward/bin/python"
PY4="$BASE/.venv-robometer/bin/python"
MODEL8=/root/autodl-tmp/hf/hub/models--Qwen--Qwen3-VL-8B-Instruct/snapshots/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b
MODEL4=/root/autodl-tmp/hf/hub/models--robometer--Robometer-4B/snapshots/beef63bc914c5c189329d49c6d712d96d632aa34
TOP="$BASE/research/sources/TOPReward"
ROBO="$BASE/research/sources/robometer_pr33_compat"
ACCESS="$RUN/inputs/access_gate/model_input"
SUPPORT="$RUN/inputs/support_surface/model_input"
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 WANDB_MODE=disabled WANDB_DISABLED=true TOKENIZERS_PARALLELISM=false
export PYTHONPATH="$RUN/code"
lease_end_epoch="$(date -u -d "$LEASE_END_UTC" +%s)"
remaining() { echo $((lease_end_epoch - $(date -u +%s))); }
require_time() {
  local estimate="$1" label="$2" log="$3" left
  left="$(remaining)"
  printf '%s remaining_seconds=%s estimate_seconds=%s buffer_seconds=600 utc=%s\n' \
    "$label" "$left" "$estimate" "$(date -u +%FT%TZ)" | tee -a "$log"
  if (( left < estimate + 600 )); then
    echo "Insufficient rental time for $label plus download buffer" >&2
    return 1
  fi
}

run_native_cell() {
  local raw="$1" input="$2" arm="$3" method="$4" py="$5" repo="$6" model="$7" estimate="$8" lower rc
  lower="$(printf '%s' "$method" | tr '[:upper:]' '[:lower:]')"
  if ! require_time "$estimate" "${arm}_${lower}" "$raw/time_checks.log"; then return 3; fi
  mkdir -p "$raw/$arm"
  set +e
  "$py" -m pilot_pkg.run_native_single_scene_pilot --method "$method" \
    --input-dir "$input" --repo "$repo" --model-path "$model" --output-dir "$raw/$arm/$lower" \
    > "$raw/$arm/$lower.stdout.txt" 2> "$raw/$arm/$lower.stderr.txt"
  rc=$?
  set -e
  printf '%s\n' "$rc" > "$raw/$arm/$lower.exitcode.txt"
  printf '%s\n' "$(date -u +%FT%TZ)" > "$raw/$arm/$lower.completed_utc.txt"
  return 0
}

run_p1_stage() {
  local tag="$1" stage="$2" count="$3" pilot="$4" estimate="$5" root="$RUN/extra/p1/$tag" rc
  mkdir -p "$root/raw"
  require_time "$estimate" "p1_$tag" "$root/raw/time_checks.log"
  set +e
  if test "$pilot" = yes; then
    "$PY8" -m optional.p1_qwen --access-input "$ACCESS" --support-input "$SUPPORT" \
      --model-path "$MODEL8" --stage "$stage" --limit-per-arm 1 --pilot --output "$root/raw/calls.jsonl" \
      > "$root/raw/stdout.txt" 2> "$root/raw/stderr.txt"
  else
    "$PY8" -m optional.p1_qwen --access-input "$ACCESS" --support-input "$SUPPORT" \
      --model-path "$MODEL8" --stage "$stage" --output "$root/raw/calls.jsonl" \
      > "$root/raw/stdout.txt" 2> "$root/raw/stderr.txt"
  fi
  rc=$?
  set -e
  printf '%s\n' "$rc" > "$root/raw/exitcode.txt"
  "$PY8" -m optional.seal_p1 --raw-root "$root/raw" --seal "$root/raw_seal.json" \
    --access-input "$ACCESS" --support-input "$SUPPORT" --expected-count "$count" \
    > "$root/seal_summary.json"
  "$PY8" -m optional.seal_p1 --raw-root "$root/raw" --seal "$root/raw_seal.json" \
    --access-input "$ACCESS" --support-input "$SUPPORT" --expected-count "$count" --verify
  if (( rc != 0 )); then return "$rc"; fi
}

if test "$TASK" = p1; then
  OPTIONAL_SHA=ebb567b6beebbc1ce1b69ea6d33eb3f0285ad44d140714f6178ad4a8f5116de9
  test "$(sha256sum "$RUN/incoming/optional_p1_code.zip" | cut -d' ' -f1)" = "$OPTIONAL_SHA"
  test ! -e "$RUN/extra/p1_code"
  mkdir -p "$RUN/extra/p1_code" "$RUN/extra/p1/dry"
  unzip -q "$RUN/incoming/optional_p1_code.zip" -d "$RUN/extra/p1_code"
  export PYTHONPATH="$RUN/code:$RUN/extra/p1_code"
  for stage in visual necessity; do
    "$PY8" -m optional.p1_qwen --access-input "$ACCESS" --support-input "$SUPPORT" \
      --model-path "$MODEL8" --stage "$stage" --output "$RUN/extra/p1/dry/$stage.jsonl" --dry-run
  done
  run_p1_stage pilot_visual visual 2 yes 240
  run_p1_stage full_visual visual 18 no 900
  run_p1_stage full_necessity necessity 18 no 900
elif test "$TASK" = p2; then
  ROOT="$RUN/extra/p2"
  test ! -e "$ROOT"
  mkdir -p "$ROOT/raw"
  require_time 1500 p2_all_four_cells "$ROOT/raw/time_checks.log"
  for arm in access_gate support_surface; do
    input="$RUN/inputs/$arm/model_input"
    if ! run_native_cell "$ROOT/raw" "$input" "$arm" TOPReward "$PY8" "$TOP" "$MODEL8" 180; then break; fi
    if ! run_native_cell "$ROOT/raw" "$input" "$arm" Robometer "$PY4" "$ROBO" "$MODEL4" 600; then break; fi
  done
  "$PY8" -m pilot_pkg.seal_fresh_batch --raw-root "$ROOT/raw" --seal "$ROOT/raw_seal.json" \
    --access-input "$ACCESS" --support-input "$SUPPORT" > "$ROOT/seal_summary.json"
  "$PY8" -m pilot_pkg.seal_fresh_batch --raw-root "$ROOT/raw" --seal "$ROOT/raw_seal.json" \
    --access-input "$ACCESS" --support-input "$SUPPORT" --verify
elif test "$TASK" = p3; then
  ROOT="$RUN/extra/p3"
  test ! -e "$ROOT"
  for item in p1/full_visual p1/full_necessity p2; do
    marker="$(printf '%s' "$item" | tr '/' '_')_local_verified.sha256"
    test -f "$RUN/extra/$item/raw_seal.json"
    test -f "$RUN/$marker"
    test "$(cat "$RUN/$marker")" = "$(sha256sum "$RUN/extra/$item/raw_seal.json" | cut -d' ' -f1)"
  done
  test "$(sha256sum "$RUN/incoming/p3_access_gate.zip" | cut -d' ' -f1)" = 8aea344bb497e5ce6a81d9d3e6b9815218bb5369fa6f0de692870edb5797ebf2
  test "$(sha256sum "$RUN/incoming/p3_support_surface.zip" | cut -d' ' -f1)" = 41320aa3abafbbe42aa459f3a8013eddbfa9b4131c5cc411affcc9cba0411e0a
  mkdir -p "$ROOT/raw" "$ROOT/inputs/access_gate/model_input" "$ROOT/inputs/support_surface/model_input"
  require_time 1200 p3_all_four_cells "$ROOT/raw/time_checks.log"
  unzip -q "$RUN/incoming/p3_access_gate.zip" -d "$ROOT/inputs/access_gate/model_input"
  unzip -q "$RUN/incoming/p3_support_surface.zip" -d "$ROOT/inputs/support_surface/model_input"
  for arm in access_gate support_surface; do
    input="$ROOT/inputs/$arm/model_input"
    for method in TOPReward Robometer; do
      lower="$(printf '%s' "$method" | tr '[:upper:]' '[:lower:]')"
      py="$PY8"; repo="$TOP"; model="$MODEL8"
      if test "$method" = Robometer; then py="$PY4"; repo="$ROBO"; model="$MODEL4"; fi
      mkdir -p "$ROOT/dry/$arm"
      "$py" -m pilot_pkg.run_native_single_scene_pilot --method "$method" --input-dir "$input" \
        --repo "$repo" --model-path "$model" --output-dir "$ROOT/dry/$arm/$lower" --dry-run
    done
  done
  for arm in access_gate support_surface; do
    input="$ROOT/inputs/$arm/model_input"
    if ! run_native_cell "$ROOT/raw" "$input" "$arm" TOPReward "$PY8" "$TOP" "$MODEL8" 150; then break; fi
    if ! run_native_cell "$ROOT/raw" "$input" "$arm" Robometer "$PY4" "$ROBO" "$MODEL4" 360; then break; fi
  done
  "$PY8" -m pilot_pkg.seal_fresh_batch --raw-root "$ROOT/raw" --seal "$ROOT/raw_seal.json" \
    --access-input "$ROOT/inputs/access_gate/model_input" \
    --support-input "$ROOT/inputs/support_surface/model_input" --expected-count 4 > "$ROOT/seal_summary.json"
  "$PY8" -m pilot_pkg.seal_fresh_batch --raw-root "$ROOT/raw" --seal "$ROOT/raw_seal.json" \
    --access-input "$ROOT/inputs/access_gate/model_input" \
    --support-input "$ROOT/inputs/support_surface/model_input" --expected-count 4 --verify
else
  echo 'Choose p1, p2, or p3' >&2
  exit 2
fi

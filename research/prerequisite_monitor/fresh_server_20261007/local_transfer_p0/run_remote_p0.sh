#!/usr/bin/env bash
# Existing rented server only. Run after a separate read-only SSH/resource inventory.
set -euo pipefail

BASE=/root/autodl-tmp/monitor2
RUN="${1:?new run root required}"
LEASE_END_UTC="${2:?provider rental end time in UTC required}"
OLD_INPUT="${3:?existing old model_input path required for one-video smoke}"
case "$RUN" in
  "$BASE"/fresh_prerequisite_runs/*) ;;
  *) echo 'run root outside fresh_prerequisite_runs' >&2; exit 2 ;;
esac
test -d "$RUN/incoming"
test ! -e "$RUN/raw"
test ! -e "$RUN/code"
test -d "$OLD_INPUT"
test "$(basename "$OLD_INPUT")" = model_input

PY8="$BASE/.venv-topreward/bin/python"
PY4="$BASE/.venv-robometer/bin/python"
MODEL8=/root/autodl-tmp/hf/hub/models--Qwen--Qwen3-VL-8B-Instruct/snapshots/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b
MODEL4=/root/autodl-tmp/hf/hub/models--robometer--Robometer-4B/snapshots/beef63bc914c5c189329d49c6d712d96d632aa34
TOP="$BASE/research/sources/TOPReward"
ROBO="$BASE/research/sources/robometer_pr33_compat"
CODE_SHA=42c1892ada623216519f9da252cfdfb2626d6bd3e126c25fda57aab04614467a
ACCESS_SHA=3e57af3072091bafbc10b81eea17d8ebd597337458cae5edd6b8433ab5842e78
SUPPORT_SHA=3124b5117820707f3458696d4a553f0fee27d41aa969d45eca78bfd84b6cfc9d
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 WANDB_MODE=disabled WANDB_DISABLED=true TOKENIZERS_PARALLELISM=false

lease_end_epoch="$(date -u -d "$LEASE_END_UTC" +%s)"
remaining() { echo $((lease_end_epoch - $(date -u +%s))); }
require_time() {
  local estimate="$1" label="$2" left
  left="$(remaining)"
  printf '%s remaining_seconds=%s estimated_seconds=%s download_buffer_seconds=600 utc=%s\n' \
    "$label" "$left" "$estimate" "$(date -u +%FT%TZ)" | tee -a "$RUN/raw/time_checks.log"
  if (( left < estimate + 600 )); then
    echo "Insufficient rental time for $label and ten-minute download buffer" >&2
    return 1
  fi
}

test "$(sha256sum "$RUN/incoming/access_gate.zip" | cut -d' ' -f1)" = "$ACCESS_SHA"
test "$(sha256sum "$RUN/incoming/support_surface.zip" | cut -d' ' -f1)" = "$SUPPORT_SHA"
test "$(sha256sum "$RUN/incoming/model_side_code.zip" | cut -d' ' -f1)" = "$CODE_SHA"
mkdir -p "$RUN/code" "$RUN/raw" "$RUN/inputs/access_gate/model_input" "$RUN/inputs/support_surface/model_input"
unzip -q "$RUN/incoming/model_side_code.zip" -d "$RUN/code"
export PYTHONPATH="$RUN/code"

"$PY8" -m pilot_pkg.preflight_fresh_server \
  --base "$BASE" --access-zip "$RUN/incoming/access_gate.zip" \
  --support-zip "$RUN/incoming/support_surface.zip" --code-zip "$RUN/incoming/model_side_code.zip" \
  --code-sha "$CODE_SHA" --model8 "$MODEL8" --model4 "$MODEL4" \
  --python8 "$PY8" --python4 "$PY4" \
  --weight-manifest "$RUN/code/pilot_pkg/official_weight_hashes.json" \
  > "$RUN/raw/server_preflight.json" 2> "$RUN/raw/server_preflight.stderr.txt"

unzip -q "$RUN/incoming/access_gate.zip" -d "$RUN/inputs/access_gate/model_input"
unzip -q "$RUN/incoming/support_surface.zip" -d "$RUN/inputs/support_surface/model_input"
"$PY8" -m pilot_pkg.precheck_native_decoder \
  --access-input "$RUN/inputs/access_gate/model_input" \
  --support-input "$RUN/inputs/support_surface/model_input" \
  --repo "$ROBO" --python "$PY4" \
  > "$RUN/raw/native_decoder_precheck.json" 2> "$RUN/raw/native_decoder_precheck.stderr.txt"
require_time 1800 p0_full_before_smoke

# Exactly one old anonymous video through each native method. No old scores are read.
for method in TOPReward Robometer; do
  lower="$(printf '%s' "$method" | tr '[:upper:]' '[:lower:]')"
  py="$PY8"; repo="$TOP"; model="$MODEL8"; estimate=180
  if test "$method" = Robometer; then py="$PY4"; repo="$ROBO"; model="$MODEL4"; estimate=420; fi
  require_time "$estimate" "old_input_smoke_$lower"
  "$py" -m pilot_pkg.smoke_old_input --method "$method" --input-dir "$OLD_INPUT" \
    --repo "$repo" --model-path "$model" --output-dir "$RUN/raw/smoke/$lower" \
    > "$RUN/raw/smoke_$lower.stdout.txt" 2> "$RUN/raw/smoke_$lower.stderr.txt"
  test "$(grep -c '"kind": "native_result"' "$RUN/raw/smoke/$lower/native_calls.jsonl")" = 1
done

for arm in access_gate support_surface; do
  for method in TOPReward Robometer; do
    lower="$(printf '%s' "$method" | tr '[:upper:]' '[:lower:]')"
    py="$PY8"; repo="$TOP"; model="$MODEL8"
    if test "$method" = Robometer; then py="$PY4"; repo="$ROBO"; model="$MODEL4"; fi
    mkdir -p "$RUN/raw/dry/$arm"
    "$py" -m pilot_pkg.run_native_single_scene_pilot --method "$method" \
      --input-dir "$RUN/inputs/$arm/model_input" --repo "$repo" --model-path "$model" \
      --output-dir "$RUN/raw/dry/$arm/$lower" --dry-run \
      > "$RUN/raw/dry/$arm/$lower.stdout.txt" 2> "$RUN/raw/dry/$arm/$lower.stderr.txt"
    test "$(grep -c '"kind": "video_input"' "$RUN/raw/dry/$arm/$lower/native_calls.jsonl")" = 9
  done
done

printf '{"scope":"fresh_dev_v2_P0","started_utc":"%s","code_zip_sha256":"%s","lease_end_utc":"%s"}\n' \
  "$(date -u +%FT%TZ)" "$CODE_SHA" "$LEASE_END_UTC" > "$RUN/raw/run_identity.json"

run_cell() {
  local arm="$1" method="$2" py="$3" repo="$4" model="$5" estimate="$6" lower rc
  lower="$(printf '%s' "$method" | tr '[:upper:]' '[:lower:]')"
  if ! require_time "$estimate" "p0_${arm}_${lower}"; then return 3; fi
  set +e
  "$py" -m pilot_pkg.run_native_single_scene_pilot --method "$method" \
    --input-dir "$RUN/inputs/$arm/model_input" --repo "$repo" --model-path "$model" \
    --output-dir "$RUN/raw/$arm/$lower" \
    > "$RUN/raw/$arm/$lower.stdout.txt" 2> "$RUN/raw/$arm/$lower.stderr.txt"
  rc=$?
  set -e
  printf '%s\n' "$rc" > "$RUN/raw/$arm/$lower.exitcode.txt"
  printf '%s\n' "$(date -u +%FT%TZ)" > "$RUN/raw/$arm/$lower.completed_utc.txt"
  return 0
}

for arm in access_gate support_surface; do
  mkdir -p "$RUN/raw/$arm"
  if ! run_cell "$arm" TOPReward "$PY8" "$TOP" "$MODEL8" 180; then break; fi
  if ! run_cell "$arm" Robometer "$PY4" "$ROBO" "$MODEL4" 600; then break; fi
done

printf '%s\n' "$(date -u +%FT%TZ)" > "$RUN/raw/completed_utc.txt"
"$PY8" -m pilot_pkg.seal_fresh_batch --raw-root "$RUN/raw" --seal "$RUN/raw_seal.json" \
  --access-input "$RUN/inputs/access_gate/model_input" \
  --support-input "$RUN/inputs/support_surface/model_input" > "$RUN/seal_summary.json"
"$PY8" -m pilot_pkg.seal_fresh_batch --raw-root "$RUN/raw" --seal "$RUN/raw_seal.json" \
  --access-input "$RUN/inputs/access_gate/model_input" \
  --support-input "$RUN/inputs/support_surface/model_input" --verify
cat "$RUN/seal_summary.json"

#!/usr/bin/env bash
# Existing server only; one pre-frozen development task per invocation.
# Reviewed order: P5 visual -> P5 necessity, then P4 neutral -> P4 causal_fact.
# P4 credit_rule remains available only as an optional, lower-value diagnostic.
set -euo pipefail

BASE=/root/autodl-tmp/monitor2
RUN="$BASE/fresh_prerequisite_runs/20261007_dev_v2_01"
TASK="${1:?p4-neutral|p4-causal_fact|p4-credit_rule|p5-visual|p5-necessity}"
LEASE_END_UTC="${2:?provider expiration time in UTC, e.g. 2026-10-07T13:00:00Z}"
INCOMING="$RUN/incoming"
UPLOAD="$INCOMING/p4_p5_upload.zip"
PREPARED="$INCOMING/p4_p5_prepared"
CODE_DIR="$RUN/extra/p4_p5_code"
PY8="$BASE/.venv-topreward/bin/python"
MODEL8=/root/autodl-tmp/hf/hub/models--Qwen--Qwen3-VL-8B-Instruct/snapshots/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b
TOP="$BASE/research/sources/TOPReward"
EXPECTED_UPLOAD_SHA=d9fe7ba669d5f9362facae95fbeb2882ec42d565261dcf7c00491119377e070c
EXPECTED_CODE_SHA=8520a1b946dc8006b51e71ab2d062bdc6308282592e0072b13630d9263cd6198
EXPECTED_P0_SEAL=63eb941801fc64098a79185cd21b0e1c6d1357169fc8dd9f68ca06c96477f363
EXPECTED_TOP_COMMIT=4877a0ee5098cbec18485125466631b1dcc4a573
EXPECTED_MODEL_CONFIG=5cd452860dc1e9c29dd71cc3cef7f39b338b7a40793f7a260655c2d3568f3661
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 WANDB_MODE=disabled WANDB_DISABLED=true TOKENIZERS_PARALLELISM=false

test -d "$RUN/code/pilot_pkg" && test -d "$RUN/inputs/access_gate/model_input"
test "$(sha256sum "$RUN/raw_seal.json" | cut -d' ' -f1)" = "$EXPECTED_P0_SEAL"
test "$(sha256sum "$UPLOAD" | cut -d' ' -f1)" = "$EXPECTED_UPLOAD_SHA"
test "$(git -C "$TOP" rev-parse HEAD)" = "$EXPECTED_TOP_COMMIT"
test "$(sha256sum "$MODEL8/config.json" | cut -d' ' -f1)" = "$EXPECTED_MODEL_CONFIG"
test "$(sha256sum "$MODEL8/model-00001-of-00004.safetensors" | cut -d' ' -f1)" = d5d0aef0eb170fc7453a296c43c0849a56f510555d3588e4fd662bb35490aefa
test "$(sha256sum "$MODEL8/model-00002-of-00004.safetensors" | cut -d' ' -f1)" = 8be88fb5501e4d5719a6d4cc212e6a13480330e74f3e8c77daa1a68f199106b5
test "$(sha256sum "$MODEL8/model-00003-of-00004.safetensors" | cut -d' ' -f1)" = 83de00eafe6e0d57ccd009dbcf71c9974d74df2f016c27afb7e95aafd16b2192
test "$(sha256sum "$MODEL8/model-00004-of-00004.safetensors" | cut -d' ' -f1)" = 0a88b98e9f96270973f567e6a2c103ede6ccdf915ca3075e21c755604d0377a5
test "$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1 | tr -d ' ')" -ge 21000
test "$(df -B1 --output=avail /root/autodl-tmp | tail -1 | tr -d ' ')" -ge 5368709120
if test ! -d "$PREPARED"; then
  mkdir -p "$PREPARED"
  unzip -q "$UPLOAD" -d "$PREPARED"
fi
test "$(sha256sum "$PREPARED/p4_p5_model_code.zip" | cut -d' ' -f1)" = "$EXPECTED_CODE_SHA"
if test ! -d "$CODE_DIR"; then
  mkdir -p "$CODE_DIR"
  unzip -q "$PREPARED/p4_p5_model_code.zip" -d "$CODE_DIR"
fi
export PYTHONPATH="$RUN/code:$CODE_DIR"
lease_epoch="$(date -u -d "$LEASE_END_UTC" +%s)"
remaining() { echo $((lease_epoch - $(date -u +%s))); }
require_time() {
  local estimate="$1" label="$2" left
  left="$(remaining)"
  printf '%s utc=%s remaining_seconds=%s estimate_seconds=%s download_buffer=600\n' \
    "$label" "$(date -u +%FT%TZ)" "$left" "$estimate"
  if (( left < estimate + 600 )); then
    echo "Insufficient rental time for $label and download buffer" >&2
    return 3
  fi
}

run_native() {
  local input="$1" output="$2" logprefix="$3" rc
  set +e
  "$PY8" -m pilot_pkg.run_native_single_scene_pilot --method TOPReward \
    --input-dir "$input" --repo "$TOP" --model-path "$MODEL8" --output-dir "$output" \
    > "${logprefix}.stdout.txt" 2> "${logprefix}.stderr.txt"
  rc=$?
  set -e
  printf '%s\n' "$rc" > "${logprefix}.exitcode.txt"
  printf '%s\n' "$(date -u +%FT%TZ)" > "${logprefix}.completed_utc.txt"
}

package_evidence() {
  local root="$1"
  local entries=(raw dry pilot)
  if test -f "$root/raw_seal.json"; then entries+=(raw_seal.json); fi
  if test -f "$root/seal_summary.json"; then entries+=(seal_summary.json); fi
  if test -d "$root/inputs"; then entries+=(inputs); fi
  tar -czf "$root/evidence.tar.gz" -C "$root" "${entries[@]}"
  sha256sum "$root/evidence.tar.gz" > "$root/evidence.tar.gz.sha256"
  printf 'evidence_sha256=%s\n' "$(cut -d' ' -f1 < "$root/evidence.tar.gz.sha256")"
}

locally_verified() {
  local root="$1" marker="$2"
  test -f "$root/raw_seal.json" && test -f "$marker" && \
    test "$(cat "$marker")" = "$(sha256sum "$root/raw_seal.json" | cut -d' ' -f1)"
}

case "$TASK" in
  p4-neutral)
    variant=neutral
    access_sha=e030c6002d8dbf4c4b9bdc0e0dca553279690f96e83d88bdf08d906347694c23
    support_sha=5ab98f2b43a6840c5686e9c85eef2b45b75128a13f42f695a39a64239d146852 ;;
  p4-causal_fact)
    variant=causal_fact
    access_sha=a838e700c968e9d8f50c1d160891e8fc1a8169d7659cd996f36ad23bc45d9bdc
    support_sha=958ba9e05bfb5852b759470ac62b52aeca0cfa6a1884549457bdf0867a746ca5 ;;
  p4-credit_rule)
    variant=credit_rule
    access_sha=5dab84be15b8a92697e7d930af0c79e460762df12c24562d9d0998adf4d28b6c
    support_sha=cbf66bbf94801c37b25be7d45b749e6ae88e43de6374943eb81048980c0193f0 ;;
  p5-visual|p5-necessity) stage="${TASK#p5-}" ;;
  *) echo "Unknown task: $TASK" >&2; exit 2 ;;
esac

if [[ "$TASK" == p4-* ]]; then
  if test "$variant" = causal_fact; then
    locally_verified "$RUN/extra/p4/neutral" "$RUN/p4_neutral_local_verified.sha256"
  fi
  if test "$variant" = credit_rule; then
    locally_verified "$RUN/extra/p4/causal_fact" "$RUN/p4_causal_fact_local_verified.sha256"
  fi
  root="$RUN/extra/p4/$variant"
  test ! -e "$root"
  access_zip="$PREPARED/p4_inputs/$variant/access_gate/model_input.zip"
  support_zip="$PREPARED/p4_inputs/$variant/support_surface/model_input.zip"
  test "$(sha256sum "$access_zip" | cut -d' ' -f1)" = "$access_sha"
  test "$(sha256sum "$support_zip" | cut -d' ' -f1)" = "$support_sha"
  require_time 480 "p4_$variant"
  mkdir -p "$root/inputs/access_gate/model_input" "$root/inputs/support_surface/model_input" \
    "$root/dry" "$root/pilot" "$root/raw"
  unzip -q "$access_zip" -d "$root/inputs/access_gate/model_input"
  unzip -q "$support_zip" -d "$root/inputs/support_surface/model_input"
  for arm in access_gate support_surface; do
    input="$root/inputs/$arm/model_input"
    "$PY8" -m pilot_pkg.run_native_single_scene_pilot --method TOPReward --input-dir "$input" \
      --repo "$TOP" --model-path "$MODEL8" --output-dir "$root/dry/$arm/topreward" --dry-run
    test "$(grep -c '"kind": "video_input"' "$root/dry/$arm/topreward/native_calls.jsonl")" = 9
    "$PY8" -m optional.p4_pilot_input --source "$input" --output "$root/pilot/$arm/model_input"
    run_native "$root/pilot/$arm/model_input" "$root/pilot/$arm/topreward" "$root/pilot/$arm/topreward"
    test "$(grep -c '"kind": "native_result"' "$root/pilot/$arm/topreward/native_calls.jsonl")" = 1
  done
  require_time 300 "p4_${variant}_full"
  for arm in access_gate support_surface; do
    mkdir -p "$root/raw/$arm"
    run_native "$root/inputs/$arm/model_input" "$root/raw/$arm/topreward" "$root/raw/$arm/topreward"
  done
  set +e
  "$PY8" -m optional.p4_seal --raw-root "$root/raw" --seal "$root/raw_seal.json" \
    --access-input "$root/inputs/access_gate/model_input" \
    --support-input "$root/inputs/support_surface/model_input" > "$root/seal_summary.json"
  seal_rc=$?
  set -e
  if test -f "$root/raw_seal.json"; then
    "$PY8" -m optional.p4_seal --raw-root "$root/raw" --seal "$root/raw_seal.json" \
      --access-input "$root/inputs/access_gate/model_input" \
      --support-input "$root/inputs/support_surface/model_input" --verify || true
  fi
  package_evidence "$root"
  if (( seal_rc != 0 )); then exit "$seal_rc"; fi
else
  if test "$stage" = necessity; then
    locally_verified "$RUN/extra/p5/visual" "$RUN/p5_visual_local_verified.sha256"
  fi
  root="$RUN/extra/p5/$stage"
  test ! -e "$root"
  require_time 600 "p5_$stage"
  mkdir -p "$root/dry" "$root/pilot/raw" "$root/raw"
  access_input="$RUN/inputs/access_gate/model_input"
  support_input="$RUN/inputs/support_surface/model_input"
  "$PY8" -m optional.p5_qwen --access-input "$access_input" --support-input "$support_input" \
    --model-path "$MODEL8" --stage "$stage" --output "$root/dry/calls.jsonl" --dry-run
  "$PY8" -m optional.p5_qwen --access-input "$access_input" --support-input "$support_input" \
    --model-path "$MODEL8" --stage "$stage" --limit-per-arm 1 --pilot \
    --output "$root/pilot/raw/calls.jsonl" > "$root/pilot/raw/stdout.txt" 2> "$root/pilot/raw/stderr.txt"
  "$PY8" -m optional.seal_p5 --raw-root "$root/pilot/raw" --seal "$root/pilot/raw_seal.json" \
    --access-input "$access_input" --support-input "$support_input" --expected-count 2 \
    > "$root/pilot/seal_summary.json"
  require_time 450 "p5_${stage}_full"
  set +e
  "$PY8" -m optional.p5_qwen --access-input "$access_input" --support-input "$support_input" \
    --model-path "$MODEL8" --stage "$stage" --output "$root/raw/calls.jsonl" \
    > "$root/raw/stdout.txt" 2> "$root/raw/stderr.txt"
  rc=$?
  set -e
  printf '%s\n' "$rc" > "$root/raw/exitcode.txt"
  set +e
  "$PY8" -m optional.seal_p5 --raw-root "$root/raw" --seal "$root/raw_seal.json" \
    --access-input "$access_input" --support-input "$support_input" --expected-count 18 \
    > "$root/seal_summary.json"
  seal_rc=$?
  set -e
  if test -f "$root/raw_seal.json"; then
    "$PY8" -m optional.seal_p5 --raw-root "$root/raw" --seal "$root/raw_seal.json" \
      --access-input "$access_input" --support-input "$support_input" --expected-count 18 --verify || true
  fi
  package_evidence "$root"
  if (( seal_rc != 0 )); then exit "$seal_rc"; fi
fi

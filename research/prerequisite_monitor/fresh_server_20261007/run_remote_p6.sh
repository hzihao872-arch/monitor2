#!/usr/bin/env bash
# P6 direct Qwen baseline on the existing server only. No truth is present here.
set -euo pipefail

BASE=/root/autodl-tmp/monitor2
RUN="$BASE/fresh_prerequisite_runs/20261007_dev_v2_01"
LEASE_END_UTC="${1:?provider expiration time in UTC, e.g. 2026-10-07T13:00:00Z}"
ROOT="$RUN/extra/p6/direct"
INCOMING="$RUN/incoming"
CODE_ZIP="$INCOMING/p6_model_code.zip"
PY8="$BASE/.venv-topreward/bin/python"
MODEL8=/root/autodl-tmp/hf/hub/models--Qwen--Qwen3-VL-8B-Instruct/snapshots/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b
ACCESS="$RUN/inputs/access_gate/model_input"
SUPPORT="$RUN/inputs/support_surface/model_input"

export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 WANDB_MODE=disabled WANDB_DISABLED=true TOKENIZERS_PARALLELISM=false

lease_epoch="$(date -u -d "$LEASE_END_UTC" +%s)"
if (( lease_epoch - $(date -u +%s) < 600 )); then
  echo "Less than 10 minutes remain before preflight" >&2
  exit 3
fi

test ! -e "$ROOT"
test -d "$ACCESS" && test -d "$SUPPORT"
test "$(sha256sum "$RUN/raw_seal.json" | cut -d' ' -f1)" = 63eb941801fc64098a79185cd21b0e1c6d1357169fc8dd9f68ca06c96477f363
test "$(sha256sum "$CODE_ZIP" | cut -d' ' -f1)" = 27aacffe5588b043e3d582eba30458eca420a6ccb068c1b282e5b81cf3e3d736
test "$(sha256sum "$ACCESS/manifest.jsonl" | cut -d' ' -f1)" = 1b5cf62e6289e17b4f9e7b36576a07594ddb4ccad7459804cb23f505501c9d42
test "$(sha256sum "$ACCESS/media_hashes.json" | cut -d' ' -f1)" = 4d6e8a3f25cbe2099fa97ef8acceeaff06c4ea078db98d0a276823e16dd07c4e
test "$(sha256sum "$ACCESS/instruction.txt" | cut -d' ' -f1)" = c9a54672a8be801ce31325c4a840c4d7d3238233445b52f3737890fccc8b7e7f
test "$(sha256sum "$SUPPORT/manifest.jsonl" | cut -d' ' -f1)" = e2d88bd72043973caa8e34021c70d266d97c24ebd26c12cd4f5f2d244cf6fc08
test "$(sha256sum "$SUPPORT/media_hashes.json" | cut -d' ' -f1)" = eefcd2a1cbdce85a4a45593c65fb6570d1d660123dee0e90890ab00b9496fb48
test "$(sha256sum "$SUPPORT/instruction.txt" | cut -d' ' -f1)" = d33b6e478ac42f51f17c4832e222f31542228c93092936c75cfa523737214cc7
test "$(sha256sum "$MODEL8/config.json" | cut -d' ' -f1)" = 5cd452860dc1e9c29dd71cc3cef7f39b338b7a40793f7a260655c2d3568f3661
test "$(sha256sum "$MODEL8/model-00001-of-00004.safetensors" | cut -d' ' -f1)" = d5d0aef0eb170fc7453a296c43c0849a56f510555d3588e4fd662bb35490aefa
test "$(sha256sum "$MODEL8/model-00002-of-00004.safetensors" | cut -d' ' -f1)" = 8be88fb5501e4d5719a6d4cc212e6a13480330e74f3e8c77daa1a68f199106b5
test "$(sha256sum "$MODEL8/model-00003-of-00004.safetensors" | cut -d' ' -f1)" = 83de00eafe6e0d57ccd009dbcf71c9974d74df2f016c27afb7e95aafd16b2192
test "$(sha256sum "$MODEL8/model-00004-of-00004.safetensors" | cut -d' ' -f1)" = 0a88b98e9f96270973f567e6a2c103ede6ccdf915ca3075e21c755604d0377a5
test "$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1 | tr -d ' ')" -ge 21000
test "$(df -B1 --output=avail /root/autodl-tmp | tail -1 | tr -d ' ')" -ge 5368709120

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

package_evidence() {
  local entries=(code preflight.txt dry pilot raw)
  if test -f "$ROOT/raw_seal.json"; then entries+=(raw_seal.json); fi
  if test -f "$ROOT/seal_summary.json"; then entries+=(seal_summary.json); fi
  tar -czf "$ROOT/evidence.tar.gz" -C "$ROOT" "${entries[@]}"
  sha256sum "$ROOT/evidence.tar.gz" > "$ROOT/evidence.tar.gz.sha256"
  printf 'evidence_sha256=%s\n' "$(cut -d' ' -f1 < "$ROOT/evidence.tar.gz.sha256")"
}

require_time 600 p6_direct_pilot_and_full
mkdir -p "$ROOT/code" "$ROOT/dry" "$ROOT/pilot/raw" "$ROOT/raw"
unzip -q "$CODE_ZIP" -d "$ROOT/code"
export PYTHONPATH="$ROOT/code"
{
  printf 'utc=%s\nlease_end_utc=%s\n' "$(date -u +%FT%TZ)" "$LEASE_END_UTC"
  sha256sum "$RUN/raw_seal.json" "$CODE_ZIP" \
    "$ACCESS/manifest.jsonl" "$ACCESS/media_hashes.json" "$ACCESS/instruction.txt" \
    "$SUPPORT/manifest.jsonl" "$SUPPORT/media_hashes.json" "$SUPPORT/instruction.txt" \
    "$MODEL8/config.json" "$MODEL8"/model-0000*-of-00004.safetensors
  nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
  df -h /root/autodl-tmp
} > "$ROOT/preflight.txt"

"$PY8" -m p6pkg.run --access-input "$ACCESS" --support-input "$SUPPORT" \
  --model-path "$MODEL8" --output "$ROOT/dry/calls.jsonl" --dry-run
test "$(grep -c '"kind": "video_input"' "$ROOT/dry/calls.jsonl")" = 18

set +e
"$PY8" -m p6pkg.run --access-input "$ACCESS" --support-input "$SUPPORT" \
  --model-path "$MODEL8" --output "$ROOT/pilot/raw/calls.jsonl" --limit-per-arm 1 --pilot \
  > "$ROOT/pilot/raw/stdout.txt" 2> "$ROOT/pilot/raw/stderr.txt"
pilot_rc=$?
set -e
printf '%s\n' "$pilot_rc" > "$ROOT/pilot/raw/exitcode.txt"
set +e
"$PY8" -m p6pkg.seal --raw-root "$ROOT/pilot/raw" --seal "$ROOT/pilot/raw_seal.json" \
  --access-input "$ACCESS" --support-input "$SUPPORT" --expected-count 2 \
  > "$ROOT/pilot/seal_summary.json"
pilot_seal_rc=$?
set -e
if (( pilot_rc != 0 || pilot_seal_rc != 0 )); then
  package_evidence
  echo "P6 pilot failed; partial evidence preserved" >&2
  exit 2
fi

if ! require_time 450 p6_direct_full; then
  package_evidence
  exit 3
fi
set +e
"$PY8" -m p6pkg.run --access-input "$ACCESS" --support-input "$SUPPORT" \
  --model-path "$MODEL8" --output "$ROOT/raw/calls.jsonl" \
  > "$ROOT/raw/stdout.txt" 2> "$ROOT/raw/stderr.txt"
run_rc=$?
set -e
printf '%s\n' "$run_rc" > "$ROOT/raw/exitcode.txt"
set +e
"$PY8" -m p6pkg.seal --raw-root "$ROOT/raw" --seal "$ROOT/raw_seal.json" \
  --access-input "$ACCESS" --support-input "$SUPPORT" --expected-count 18 \
  > "$ROOT/seal_summary.json"
seal_rc=$?
set -e
if test -f "$ROOT/raw_seal.json"; then
  "$PY8" -m p6pkg.seal --raw-root "$ROOT/raw" --seal "$ROOT/raw_seal.json" \
    --access-input "$ACCESS" --support-input "$SUPPORT" --expected-count 18 --verify || true
fi
package_evidence
if (( run_rc != 0 || seal_rc != 0 )); then exit 2; fi

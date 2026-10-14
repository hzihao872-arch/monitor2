#!/usr/bin/env bash
# Run only on the user's already active instance, after its endpoint and lease are supplied.
set -euo pipefail

PACKAGE="${1:?package ZIP path}"
RUN_ROOT="${2:?new persistent run directory}"
MODEL="${3:?existing Qwen3-VL checkpoint directory}"
LEASE_END_UTC="${4:?lease end UTC, e.g. 2026-10-08T12:00:00Z}"
TOP_REPO="${5:?existing official TOPReward checkout}"
PY="${6:?existing Python interpreter with torch/transformers/cv2/PIL}"
EXPECTED_PACKAGE_SHA="${7:?local package SHA-256}"

test ! -e "$RUN_ROOT"
test "$(sha256sum "$PACKAGE" | cut -d' ' -f1)" = "$EXPECTED_PACKAGE_SHA"
test -f "$MODEL/config.json"
test -f "$TOP_REPO/topreward/clients/qwen.py"
test "$(git -C "$TOP_REPO" rev-parse HEAD)" = 4877a0ee5098cbec18485125466631b1dcc4a573
git -C "$TOP_REPO" diff --quiet HEAD -- topreward/clients/qwen.py
test "$(sha256sum "$MODEL/config.json" | cut -d' ' -f1)" = 5cd452860dc1e9c29dd71cc3cef7f39b338b7a40793f7a260655c2d3568f3661
expected_shards=(
  d5d0aef0eb170fc7453a296c43c0849a56f510555d3588e4fd662bb35490aefa
  8be88fb5501e4d5719a6d4cc212e6a13480330e74f3e8c77daa1a68f199106b5
  83de00eafe6e0d57ccd009dbcf71c9974d74df2f016c27afb7e95aafd16b2192
  0a88b98e9f96270973f567e6a2c103ede6ccdf915ca3075e21c755604d0377a5
)
for i in 1 2 3 4; do
  file="$(printf '%s/model-%05d-of-00004.safetensors' "$MODEL" "$i")"
  test "$(sha256sum "$file" | cut -d' ' -f1)" = "${expected_shards[$((i-1))]}"
done
test "$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1 | tr -d ' ')" -ge 21000
test "$(df -B1 --output=avail "$(dirname "$RUN_ROOT")" | tail -1 | tr -d ' ')" -ge 5368709120

lease_epoch="$(date -u -d "$LEASE_END_UTC" +%s)"
remaining() { echo $((lease_epoch - $(date -u +%s))); }
require_time() {
  local estimate="$1" label="$2" left
  left="$(remaining)"
  printf '%s utc=%s remaining_s=%s required_s=%s seal_download_buffer_s=600\n' \
    "$label" "$(date -u +%FT%TZ)" "$left" "$estimate"
  (( left >= estimate + 600 ))
}
package_evidence() {
  local files=() name
  for name in identity.txt dry_run.jsonl pilot.jsonl raw.jsonl qwen_seal.json qwen_exitcode.txt text_inputs text_dry text_pilot text_raw text_seal.json; do
    if test -e "$RUN_ROOT/$name"; then files+=("$name"); fi
  done
  tar -czf "$RUN_ROOT/evidence.tar.gz" -C "$RUN_ROOT" "${files[@]}"
  sha256sum "$RUN_ROOT/evidence.tar.gz" > "$RUN_ROOT/evidence.tar.gz.sha256"
  printf 'evidence_sha256=%s\n' "$(cut -d' ' -f1 < "$RUN_ROOT/evidence.tar.gz.sha256")"
}

export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 WANDB_MODE=disabled WANDB_DISABLED=true
export TOKENIZERS_PARALLELISM=false
mkdir -p "$RUN_ROOT"
{
  printf 'utc=%s\n' "$(date -u +%FT%TZ)"
  printf 'package_sha256=%s\n' "$EXPECTED_PACKAGE_SHA"
  printf 'model_config_sha256=%s\n' "$(sha256sum "$MODEL/config.json" | cut -d' ' -f1)"
  for i in 1 2 3 4; do
    file="$(printf '%s/model-%05d-of-00004.safetensors' "$MODEL" "$i")"
    printf 'model_shard_%s_sha256=%s\n' "$i" "$(sha256sum "$file" | cut -d' ' -f1)"
  done
  printf 'topreward_commit=%s\n' "$(git -C "$TOP_REPO" rev-parse HEAD 2>/dev/null || true)"
  printf 'topreward_qwen_blob=%s\n' "$(git -C "$TOP_REPO" rev-parse HEAD:topreward/clients/qwen.py)"
  nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
  "$PY" -c 'import sys,torch,transformers,cv2;print("python="+sys.version.split()[0]);print("torch="+torch.__version__);print("transformers="+transformers.__version__);print("opencv="+cv2.__version__)'
} > "$RUN_ROOT/identity.txt"
unzip -q "$PACKAGE" -d "$RUN_ROOT/package"
"$PY" - "$RUN_ROOT/package" <<'PY'
import hashlib,json,sys
from pathlib import Path
p=Path(sys.argv[1]); m=json.loads((p/'bundle_manifest.json').read_text())
for name,digest in m['members'].items():
    if hashlib.sha256((p/name).read_bytes()).hexdigest()!=digest:
        raise SystemExit('bundle member mismatch: '+name)
print('bundle_members_verified',len(m['members']))
PY
mkdir -p "$RUN_ROOT/inputs/group_01/model_input" "$RUN_ROOT/inputs/group_02/model_input"
unzip -q "$RUN_ROOT/package/group_01.zip" -d "$RUN_ROOT/inputs/group_01/model_input"
unzip -q "$RUN_ROOT/package/group_02.zip" -d "$RUN_ROOT/inputs/group_02/model_input"
export PYTHONPATH="$RUN_ROOT/package"
"$PY" - "$TOP_REPO" <<'PY'
import sys,types
from pathlib import Path
repo=Path(sys.argv[1])
sys.path.insert(0,str(repo))
package=types.ModuleType('topreward.clients')
package.__path__=[str(repo/'topreward/clients')]
sys.modules['topreward.clients']=package
from topreward.clients.qwen import QwenClient
print('official_topreward_client_import_verified',QwenClient.__name__)
PY
COMMON=(--group-01 "$RUN_ROOT/inputs/group_01/model_input" --group-02 "$RUN_ROOT/inputs/group_02/model_input")

"$PY" "$RUN_ROOT/package/one_session_suite_v0_2.py" "${COMMON[@]}" \
  --output "$RUN_ROOT/dry_run.jsonl" --dry-run
require_time 1800 qwen_pilot_and_full || { echo 'Lease too short for full suite before pilot' >&2; exit 3; }
set +e
"$PY" "$RUN_ROOT/package/one_session_suite_v0_2.py" "${COMMON[@]}" \
  --model-path "$MODEL" --limit-per-group 1 --output "$RUN_ROOT/pilot.jsonl"
pilot_rc=$?
set -e
if test "$pilot_rc" -ne 0; then package_evidence; exit "$pilot_rc"; fi
if ! "$PY" - "$RUN_ROOT/pilot.jsonl" <<'PY'
import json,sys
rows=[json.loads(x) for x in open(sys.argv[1],encoding='utf-8')]
calls=[x for x in rows if x.get('kind') in ('model_output','model_failure')]
assert len(calls)==18, ('pilot_calls',len(calls))
assert all(x['kind']=='model_output' for x in calls), 'pilot runtime failure'
print('pilot_status', {s:sum(x.get('validation',{}).get('status','runtime_failure')==s for x in calls) for s in
                      set(x.get('validation',{}).get('status','runtime_failure') for x in calls)})
PY
then
  package_evidence
  exit 4
fi
pilot_seconds="$("$PY" - "$RUN_ROOT/pilot.jsonl" <<'PY'
import json,sys
rows=[json.loads(x) for x in open(sys.argv[1],encoding='utf-8')]
print((sum(x.get('elapsed_ms',0) for x in rows if x.get('kind')=='model_output')+999)//1000)
PY
)"
full_estimate=$((pilot_seconds*27/2+300))
if (( full_estimate < 1200 )); then full_estimate=1200; fi
require_time "$full_estimate" qwen_full || { echo 'Lease too short after pilot; pilot preserved' >&2; package_evidence; exit 3; }
set +e
timeout --signal=INT --kill-after=5 "$(($(remaining)-600))" \
  "$PY" "$RUN_ROOT/package/one_session_suite_v0_2.py" "${COMMON[@]}" \
  --model-path "$MODEL" --output "$RUN_ROOT/raw.jsonl"
qwen_rc=$?
set -e
printf '%s\n' "$qwen_rc" > "$RUN_ROOT/qwen_exitcode.txt"
if test -f "$RUN_ROOT/raw.jsonl"; then
  if ! "$PY" "$RUN_ROOT/package/seal_one_session_v0_2.py" --raw "$RUN_ROOT/raw.jsonl" \
    --package "$PACKAGE" --output "$RUN_ROOT/qwen_seal.json" --allow-partial; then
    package_evidence
    exit 5
  fi
else
  echo 'No full Qwen raw file; pilot remains the only model evidence' >&2
  package_evidence
  exit "$qwen_rc"
fi
if test "$qwen_rc" -ne 0; then
  echo 'Qwen suite incomplete; preserve raw evidence and stop before text probes' >&2
  package_evidence
  exit "$qwen_rc"
fi

if ! "$PY" "$RUN_ROOT/package/build_text_probe_inputs_v0_2.py" "${COMMON[@]}" \
  --suite-raw "$RUN_ROOT/raw.jsonl" --out-root "$RUN_ROOT/text_inputs"; then
  package_evidence
  exit 5
fi
for variant in matched_neutral general_preparation auto_relation auto_counterclaim; do
  for group in group_01 group_02; do
    if ! "$PY" "$RUN_ROOT/package/native_topreward_probe_v0_2.py" --dry-run \
      --input-dir "$RUN_ROOT/text_inputs/$variant/$group/model_input" \
      --repo "$TOP_REPO" --model-path "$MODEL" \
      --output-dir "$RUN_ROOT/text_dry/$variant/$group"; then
      package_evidence
      exit 5
    fi
  done
done
require_time 1200 topreward_pilot_and_first_variant || { package_evidence; exit 3; }
set +e
"$PY" "$RUN_ROOT/package/native_topreward_probe_v0_2.py" \
  --input-dir "$RUN_ROOT/text_inputs/matched_neutral/group_01/model_input" \
  --repo "$TOP_REPO" --model-path "$MODEL" --limit 1 --output-dir "$RUN_ROOT/text_pilot"
native_pilot_rc=$?
set -e
if test "$native_pilot_rc" -ne 0; then package_evidence; exit "$native_pilot_rc"; fi
if ! "$PY" - "$RUN_ROOT/text_pilot/native_calls.jsonl" <<'PY'
import json,sys
rows=[json.loads(x) for x in open(sys.argv[1],encoding='utf-8')]
assert sum(x.get('kind')=='native_result' for x in rows)==1, 'TOPReward pilot failed'
PY
then
  package_evidence
  exit 5
fi
mkdir -p "$RUN_ROOT/text_raw"
native_failed=0
for variant in matched_neutral general_preparation auto_relation auto_counterclaim; do
  require_time 600 "topreward_${variant}" || break
  for group in group_01 group_02; do
    input="$RUN_ROOT/text_inputs/$variant/$group/model_input"
    output="$RUN_ROOT/text_raw/$variant/$group"
    mkdir -p "$(dirname "$output")"
    set +e
    timeout --signal=INT --kill-after=5 "$(($(remaining)-600))" \
      "$PY" "$RUN_ROOT/package/native_topreward_probe_v0_2.py" \
      --input-dir "$input" --repo "$TOP_REPO" --model-path "$MODEL" --output-dir "$output"
    native_rc=$?
    set -e
    if test "$native_rc" -ne 0; then
      native_failed=1
      break
    fi
  done
  if test "$native_failed" -ne 0; then break; fi
done
if ! "$PY" "$RUN_ROOT/package/seal_text_probe_v0_2.py" --input-root "$RUN_ROOT/text_inputs" \
  --raw-root "$RUN_ROOT/text_raw" --output "$RUN_ROOT/text_seal.json" --allow-partial; then
  package_evidence
  exit 5
fi
package_evidence
if test "$native_failed" -ne 0; then exit 5; fi

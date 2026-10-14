#!/usr/bin/env bash
# Run only on the user's previously rented server after a fresh read-only inventory.
set -euo pipefail

BASE=/root/autodl-tmp/monitor2
RUN="${1:?pass a new run root under /root/autodl-tmp/monitor2/causal_rescue}"
case "$RUN" in
  "$BASE"/causal_rescue/*) ;;
  *) echo 'run root outside allowed causal_rescue directory' >&2; exit 2 ;;
esac
test -d "$RUN/incoming"
test ! -e "$RUN/code"
test ! -e "$RUN/raw"

PY8="$BASE/.venv-topreward/bin/python"
PY4="$BASE/.venv-robometer/bin/python"
MODEL8=/root/autodl-tmp/hf/hub/models--Qwen--Qwen3-VL-8B-Instruct/snapshots/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b
MODEL4=/root/autodl-tmp/hf/hub/models--robometer--Robometer-4B/snapshots/beef63bc914c5c189329d49c6d712d96d632aa34
TOP="$BASE/research/sources/TOPReward"
ROBO="$BASE/research/sources/robometer_pr33_compat"
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export WANDB_MODE=disabled
export WANDB_DISABLED=true
export TOKENIZERS_PARALLELISM=false

test "$(sha256sum "$RUN/incoming/L1.zip" | cut -d' ' -f1)" = d19299e3a1a609aaaa42e02474223e748672954b97e575b53d4c09214b0ec1a5
test "$(sha256sum "$RUN/incoming/L2.zip" | cut -d' ' -f1)" = 9df5a32ab7f22a13cbda6a536031f8938f0f88d797a274f221eb4d8a7379d3f2
test "$(sha256sum "$RUN/incoming/code_v5.zip" | cut -d' ' -f1)" = 800a51e57aa3943626adc1d8f97f1701d004dc877b51b72dafff96e105ac4017

mkdir -p "$RUN/code" "$RUN/raw/L1" "$RUN/raw/L2" "$RUN/raw/dry/L1" "$RUN/raw/dry/L2"
unzip -q "$RUN/incoming/code_v5.zip" -d "$RUN/code"
export PYTHONPATH="$RUN/code"

"$PY8" -m pilot_pkg.preflight_causal_rescue_server \
  --base "$BASE" --l1-zip "$RUN/incoming/L1.zip" --l2-zip "$RUN/incoming/L2.zip" \
  --code-zip "$RUN/incoming/code_v5.zip" \
  --l1-sha d19299e3a1a609aaaa42e02474223e748672954b97e575b53d4c09214b0ec1a5 \
  --l2-sha 9df5a32ab7f22a13cbda6a536031f8938f0f88d797a274f221eb4d8a7379d3f2 \
  --code-sha 800a51e57aa3943626adc1d8f97f1701d004dc877b51b72dafff96e105ac4017 \
  --model8 "$MODEL8" --model4 "$MODEL4" --python4 "$PY4" \
  --hf-home "$HF_HOME" --weight-manifest "$RUN/code/pilot_pkg/official_weight_hashes.json" \
  > "$RUN/raw/server_preflight.json" 2> "$RUN/raw/server_preflight.stderr.txt"

for arm in L1 L2; do
  mkdir -p "$RUN/$arm/model_input"
  unzip -q "$RUN/incoming/$arm.zip" -d "$RUN/$arm/model_input"
  for method in TOPReward Robometer; do
    lower="$(printf '%s' "$method" | tr '[:upper:]' '[:lower:]')"
    py="$PY8"; repo="$TOP"; model="$MODEL8"
    if test "$method" = Robometer; then py="$PY4"; repo="$ROBO"; model="$MODEL4"; fi
    "$py" -m pilot_pkg.run_native_single_scene_pilot --method "$method" \
      --input-dir "$RUN/$arm/model_input" --repo "$repo" --model-path "$model" \
      --output-dir "$RUN/raw/dry/$arm/$lower" --dry-run \
      > "$RUN/raw/dry/$arm/$lower.stdout.txt" 2> "$RUN/raw/dry/$arm/$lower.stderr.txt"
  done
done

printf '{"design_sha256":"0f9ddeb56eb91ef16936114825d4ba28206b8c34451c449f5d87bb970c5f70e7","code_zip_sha256":"800a51e57aa3943626adc1d8f97f1701d004dc877b51b72dafff96e105ac4017","scope":"seen_development_six_clips","started_utc":"%s"}\n' "$(date -u +%FT%TZ)" > "$RUN/raw/run_identity.json"

run_cell() {
  local arm="$1" method="$2" py="$3" repo="$4" model="$5" lower
  lower="$(printf '%s' "$method" | tr '[:upper:]' '[:lower:]')"
  "$py" -m pilot_pkg.run_native_single_scene_pilot --method "$method" \
    --input-dir "$RUN/$arm/model_input" --repo "$repo" --model-path "$model" \
    --output-dir "$RUN/raw/$arm/$lower" \
    > "$RUN/raw/$arm/$lower.stdout.txt" 2> "$RUN/raw/$arm/$lower.stderr.txt"
  printf '%s\n' "$?" > "$RUN/raw/$arm/$lower.exitcode.txt"
}

set +e
run_cell L1 TOPReward "$PY8" "$TOP" "$MODEL8"
run_cell L1 Robometer "$PY4" "$ROBO" "$MODEL4"
run_cell L2 TOPReward "$PY8" "$TOP" "$MODEL8"
run_cell L2 Robometer "$PY4" "$ROBO" "$MODEL4"
set -e

printf '%s\n' "$(date -u +%FT%TZ)" > "$RUN/raw/completed_utc.txt"
"$PY8" -m pilot_pkg.seal_causal_rescue_batch --raw-root "$RUN/raw" --seal "$RUN/raw_seal.json" \
  > "$RUN/seal_summary.json"
"$PY8" -m pilot_pkg.seal_causal_rescue_batch --raw-root "$RUN/raw" --seal "$RUN/raw_seal.json" --verify
cat "$RUN/seal_summary.json"

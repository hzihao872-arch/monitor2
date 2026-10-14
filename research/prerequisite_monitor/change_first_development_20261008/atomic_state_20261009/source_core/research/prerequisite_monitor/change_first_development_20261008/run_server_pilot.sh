#!/usr/bin/env bash
set -euo pipefail

RUN_PY=""; RUN_MODEL=""; RUN_INPUT=""; RUN_OUTPUT=""; RUN_START=""; RUN_PREFLIGHT=""
RUN_MAX_REQUESTS=96; RUN_MAX_QUERIES=8; RUN_MAX_WALL_MINUTES=120; RUN_SEAL_BUFFER_MINUTES=15
while [[ $# -gt 0 ]]; do
  case "$1" in
    --python) RUN_PY="$2"; shift 2;;
    --model) RUN_MODEL="$2"; shift 2;;
    --input) RUN_INPUT="$2"; shift 2;;
    --output) RUN_OUTPUT="$2"; shift 2;;
    --window-start-epoch) RUN_START="$2"; shift 2;;
    --preflight-report) RUN_PREFLIGHT="$2"; shift 2;;
    --max-requests) RUN_MAX_REQUESTS="$2"; shift 2;;
    --max-queries) RUN_MAX_QUERIES="$2"; shift 2;;
    --max-wall-minutes) RUN_MAX_WALL_MINUTES="$2"; shift 2;;
    --seal-buffer-minutes) RUN_SEAL_BUFFER_MINUTES="$2"; shift 2;;
    -h|--help) echo 'Required: --python --model --input --output --preflight-report --window-start-epoch. Limits: --max-requests 96 --max-queries 1..8 --max-wall-minutes 120 --seal-buffer-minutes 15'; exit 0;;
    *) echo "Unknown option $1" >&2; exit 2;;
  esac
done
[[ -n "$RUN_PY" && -n "$RUN_MODEL" && -n "$RUN_INPUT" && -n "$RUN_OUTPUT" && -n "$RUN_START" && -n "$RUN_PREFLIGHT" ]] || { echo 'Missing required option' >&2; exit 2; }
[[ "$RUN_MAX_REQUESTS" -le 96 && "$RUN_MAX_QUERIES" -ge 1 && "$RUN_MAX_QUERIES" -le 8 && "$RUN_MAX_WALL_MINUTES" -le 120 && "$RUN_SEAL_BUFFER_MINUTES" -ge 15 ]] || { echo 'Hard limit rejected' >&2; exit 2; }
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
mkdir -p "$RUN_OUTPUT"
exec 9>"$RUN_OUTPUT/.run.lock"
flock -n 9 || { echo 'This run is already active' >&2; exit 3; }
"$RUN_PY" -c 'import json,sys; x=json.load(open(sys.argv[1])); assert float(x["window_start_epoch"])==float(sys.argv[2])' "$RUN_PREFLIGHT" "$RUN_START"
if [[ -e "$RUN_OUTPUT/preflight.json" ]]; then
  cmp -s "$RUN_PREFLIGHT" "$RUN_OUTPUT/preflight.json" || { echo 'Preflight identity changed' >&2; exit 3; }
else
  cp "$RUN_PREFLIGHT" "$RUN_OUTPUT/preflight.json"
fi
WINDOW_FILE="$RUN_OUTPUT/window.json"
if [[ -e "$WINDOW_FILE" ]]; then
  "$RUN_PY" -c 'import json,sys; x=json.load(open(sys.argv[1])); assert float(x["window_start_epoch"])==float(sys.argv[2])' "$WINDOW_FILE" "$RUN_START"
else
  "$RUN_PY" -c 'import json,sys; open(sys.argv[1],"w").write(json.dumps({"window_start_epoch":float(sys.argv[2])}))' "$WINDOW_FILE" "$RUN_START"
fi
RUN_DEADLINE="$($RUN_PY -c 'import sys; print(float(sys.argv[1])+60*float(sys.argv[2]))' "$RUN_START" "$RUN_MAX_WALL_MINUTES")"
RUN_SECONDS="$($RUN_PY -c 'import sys,time; print(max(0,int(float(sys.argv[1])-time.time()-60*float(sys.argv[2]))))' "$RUN_DEADLINE" "$RUN_SEAL_BUFFER_MINUTES")"
[[ "$RUN_SECONDS" -gt 0 ]] || { echo 'No time left before sealing buffer' >&2; exit 4; }
RUN_ARCHIVE="${RUN_OUTPUT%/}_results_$(date -u +%Y%m%dT%H%M%SZ).tar.gz"
seal_run() {
  "$RUN_PY" research/prerequisite_monitor/change_first_development_20261008/collect_and_seal.py --run "$RUN_OUTPUT" --output "$RUN_ARCHIVE"
}
trap seal_run EXIT
PYTHONPATH="$ROOT" timeout --signal=TERM "${RUN_SECONDS}s" "$RUN_PY" -m experiments.prerequisite_probe.change_first_monitor.runner \
  --backend qwen --model "$RUN_MODEL" --input "$RUN_INPUT" --output "$RUN_OUTPUT" \
  --arms D4 K4 C4 --max-requests "$RUN_MAX_REQUESTS" --max-queries "$RUN_MAX_QUERIES" --deadline-epoch "$RUN_DEADLINE" \
  --seal-buffer-minutes "$RUN_SEAL_BUFFER_MINUTES"

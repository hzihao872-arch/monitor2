#!/usr/bin/env bash
set -euo pipefail
kill -TERM 3263 3290 2>/dev/null || true
for i in $(seq 1 30); do
  if ! kill -0 3263 2>/dev/null && ! kill -0 3290 2>/dev/null; then break; fi
  sleep 1
done
if kill -0 3263 2>/dev/null || kill -0 3290 2>/dev/null; then
  echo 'Prior Qwen download processes still running; refusing a second writer' >&2
  exit 1
fi
nohup /root/miniconda3/bin/python -u /root/autodl-tmp/download_official_weights.py \
  --repo Qwen/Qwen3-VL-8B-Instruct \
  --revision 0c351dd01ed87e9c1b53cbc748cba10e6187ff3b \
  --cache /root/autodl-tmp/hf --endpoint https://hf-mirror.com --workers 4 \
  --alternate-weights-url-base https://www.modelscope.cn/models/Qwen/Qwen3-VL-8B-Instruct/resolve/master \
  --manifest /root/autodl-tmp/official_weight_hashes.json \
  > /root/autodl-tmp/top_weights_modelscope.log 2>&1 </dev/null &
echo "TOP_QWEN_PID=$!"
nohup /root/miniconda3/bin/python -u /root/autodl-tmp/download_official_weights.py \
  --repo Qwen/Qwen3-VL-4B-Instruct \
  --revision ebb281ec70b05090aa6165b016eac8ec08e71b17 \
  --cache /root/autodl-tmp/hf --endpoint https://hf-mirror.com --workers 2 \
  --alternate-weights-url-base https://www.modelscope.cn/models/Qwen/Qwen3-VL-4B-Instruct/resolve/master \
  --manifest /root/autodl-tmp/official_weight_hashes.json \
  > /root/autodl-tmp/rob_base_weights_modelscope.log 2>&1 </dev/null &
echo "ROB_BASE_QWEN_PID=$!"

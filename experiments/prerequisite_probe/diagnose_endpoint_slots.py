"""Development-only endpoint predicate diagnostic on the old six videos."""

import json
from pathlib import Path

import torch
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

from experiments.prerequisite_probe import run_monitor_qwen as runner


BASE = Path('/root/autodl-tmp/monitor2')
MODEL = Path('/root/autodl-tmp/hf/hub/models--Qwen--Qwen3-VL-8B-Instruct/snapshots/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b')
INPUT = BASE / 'experiments/prerequisite_probe/artifacts/model_input'
OUT = BASE / 'new_tests/server_results/old_dev_endpoint_slots_v2.jsonl'
if OUT.exists():
    raise FileExistsError(OUT)
processor = AutoProcessor.from_pretrained(MODEL, local_files_only=True)
model = Qwen3VLForConditionalGeneration.from_pretrained(
    MODEL, dtype=torch.bfloat16, attn_implementation='flash_attention_2',
    local_files_only=True).to('cuda').eval()
for row in runner.collect_inputs(INPUT):
    images, _ = runner.decode_selected(INPUT / row['video'])
    for second in (0, 14):
        prompt = (
            f'Final goal: {row["instruction"]}\n'
            f'Inspect ONLY the frame marked second {second}. Answer visual facts, not task progress. '
            'destination_non_goal_present means an object other than the goal object is inside '
            'or directly over the usable interior of the goal destination, including overhead '
            'approach space. source_non_goal_present means an object other than the goal object '
            'is in or directly above the goal object\'s grasp area. '
            'A nearby object does not count without visible overlap. '
            'Return exactly one short JSON object with string values "true", "false", or '
            '"unknown" for destination_non_goal_present and source_non_goal_present, '
            'plus short strings destination_evidence and source_evidence. '
            'The evidence must describe what is visible in that frame. No markdown.'
        )
        runner.FRAME_SECONDS = (second,)
        call = runner.model_call(model, processor, [images[0] if second == 0 else images[-1]], prompt, 192)
        with OUT.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'video': row['video'], 'second': second, **call}, ensure_ascii=False) + '\n')
            stream.flush()
        print(row['video'], second, call['raw'], flush=True)

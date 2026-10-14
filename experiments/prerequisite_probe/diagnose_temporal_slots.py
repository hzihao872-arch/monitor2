"""Development-only temporal scene-fact extraction on the old six videos."""

import json
from pathlib import Path

import torch
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

from experiments.prerequisite_probe.run_monitor_qwen import collect_inputs, decode_selected, model_call


BASE = Path('/root/autodl-tmp/monitor2')
MODEL = Path('/root/autodl-tmp/hf/hub/models--Qwen--Qwen3-VL-8B-Instruct/snapshots/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b')
INPUT = BASE / 'experiments/prerequisite_probe/artifacts/model_input'
OUT = BASE / 'new_tests/server_results/old_dev_temporal_slots_v1.jsonl'
if OUT.exists():
    raise FileExistsError(OUT)
processor = AutoProcessor.from_pretrained(MODEL, local_files_only=True)
model = Qwen3VLForConditionalGeneration.from_pretrained(
    MODEL, dtype=torch.bfloat16, attn_implementation='flash_attention_2',
    local_files_only=True).to('cuda').eval()
for row in collect_inputs(INPUT):
    images, _ = decode_selected(INPUT / row['video'])
    prompt = (
        f'Final goal: {row["instruction"]}\n'
        'Describe only visual facts at second 0 and second 14 using the video frames. '
        'Identify the goal object and its destination from the goal. '
        'A non-goal object includes a loose object or fixed barrier, but excludes the robot arm. '
        'For each endpoint, state whether any non-goal object is inside or directly over the '
        'destination interior, and whether one directly covers the goal object\'s top-down grasp '
        'area. Nearby objects with no visible overlap do not count. '
        'Track an object that leaves and returns; judge the final endpoint, not an intermediate frame. '
        'Do not judge task progress or relevance. Return exactly one JSON object with these '
        'string fields: goal_object, destination, moved_object, '
        'destination_non_goal_0, destination_non_goal_14, source_non_goal_0, source_non_goal_14 '
        '(each true/false/unknown), and evidence_0, evidence_14 (short visible descriptions). '
        'No markdown and no other keys.'
    )
    call = model_call(model, processor, images, prompt, 256)
    with OUT.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'video': row['video'], **call}, ensure_ascii=False) + '\n')
        stream.flush()
    print(row['video'], call['raw'], flush=True)

"""Development-only fact-first prerequisite probe on the original six videos."""

import json
from pathlib import Path

import torch
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

from experiments.prerequisite_probe.run_monitor_qwen import (
    COMMON, collect_inputs, decode_selected, model_call,
)


BASE = Path('/root/autodl-tmp/monitor2')
MODEL = Path('/root/autodl-tmp/hf/hub/models--Qwen--Qwen3-VL-8B-Instruct/snapshots/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b')
INPUT = BASE / 'experiments/prerequisite_probe/artifacts/model_input'
OUT = BASE / 'new_tests/server_results/old_dev_two_stage_v1.jsonl'
if OUT.exists():
    raise FileExistsError(OUT)
processor = AutoProcessor.from_pretrained(MODEL, local_files_only=True)
model = Qwen3VLForConditionalGeneration.from_pretrained(
    MODEL, dtype=torch.bfloat16, attn_implementation='flash_attention_2',
    local_files_only=True).to('cuda').eval()
for row in collect_inputs(INPUT):
    images, _ = decode_selected(INPUT / row['video'])
    visual_prompt = (
        'Describe only visible changes in this tabletop robot video. State what the robot moved, '
        'where that object was at second 0 and second 14, and whether the source and destination '
        'areas are occupied or obstructed at those times. Distinguish moving an object away from '
        'returning it to the same place. Do not judge task progress. Reply in at most 70 words.'
    )
    visual = model_call(model, processor, images, visual_prompt, 192)
    p_prompt = COMMON.format(instruction=row['instruction']) + '\n' + (
        'The following preliminary visual description came from the same video. It can be wrong; '
        'verify every claim against the supplied frames before using it:\n' + visual['raw'] + '\n'
        'Choose a goal-relevant physical condition changed by the observed action. For a single-arm '
        'pick-and-place goal, consider grasp access at the source, transfer clearance, and usable '
        'placement space and top-down access at the destination. An unnamed object can matter. '
        'If an obstacle leaves the destination and stays away, usable placement may improve; '
        'if it returns, there is no net improvement; if one enters, usability may worsen. '
        'Apply the analogous source-access check when the change is at the source. Do not infer a '
        'path obstruction without visible path geometry. State the one decisive condition in '
        'relation, with first/last evidence. If occupancy or alternative access is not visible, '
        'use unknown and specify why.'
    )
    p2 = model_call(model, processor, images, p_prompt, 512)
    with OUT.open('a', encoding='utf-8') as stream:
        for method, call in [('V', visual), ('P2', p2)]:
            stream.write(json.dumps({'video': row['video'], 'method': method, **call}, ensure_ascii=False) + '\n')
            stream.flush()
    print(row['video'], p2['validity'], (p2['record'] or {}).get('relation'),
          (p2['record'] or {}).get('comparison'), flush=True)

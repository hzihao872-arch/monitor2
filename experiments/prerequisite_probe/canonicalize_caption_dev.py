"""Development-only text fact canonicalization of saved visual captions."""

import json
from pathlib import Path

import torch
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration


BASE = Path('/root/autodl-tmp/monitor2')
MODEL = Path('/root/autodl-tmp/hf/hub/models--Qwen--Qwen3-VL-8B-Instruct/snapshots/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b')
SOURCE = BASE / 'new_tests/server_results/old_dev_two_stage_v1.jsonl'
OUT = BASE / 'new_tests/server_results/old_dev_caption_canonical_v1.jsonl'
if OUT.exists():
    raise FileExistsError(OUT)
captions = [json.loads(line) for line in SOURCE.read_text().splitlines()
            if json.loads(line).get('method') == 'V']
processor = AutoProcessor.from_pretrained(MODEL, local_files_only=True)
model = Qwen3VLForConditionalGeneration.from_pretrained(
    MODEL, dtype=torch.bfloat16, attn_implementation='flash_attention_2',
    local_files_only=True).to('cuda').eval()
for row in captions:
    prompt = (
        'Final goal: Put the blue cube in the green tray. A fallible observer wrote this about '
        'the same preparation video: ' + row['raw'] + '\n'
        'Extract only what this text claims about the first and last state. Do not infer task '
        'progress or whether an object is relevant. If the text does not support a value, use '
        '"unknown". Treat objects other than the blue cube, excluding the robot arm, as non-goal. '
        'Return exactly one JSON object with string fields destination_non_goal_0, '
        'destination_non_goal_14, source_non_goal_0, source_non_goal_14, '
        'goal_complete_0, goal_complete_14; values are only "true", "false", "unknown". '
        'destination_non_goal means one is in or above the green tray interior. '
        'source_non_goal means one is in or above the blue cube grasp area. '
        'Use the first and last states, ignoring temporary movements. No markdown.'
    )
    inputs = processor.apply_chat_template(
        [{'role': 'user', 'content': [{'type': 'text', 'text': prompt}]}],
        tokenize=True, add_generation_prompt=True, return_dict=True,
        return_tensors='pt').to('cuda')
    with torch.inference_mode():
        output = model.generate(**inputs, max_new_tokens=192, do_sample=False)
    raw = processor.batch_decode(output[:, inputs['input_ids'].shape[-1]:], skip_special_tokens=True)[0]
    with OUT.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'video': row['video'], 'caption': row['raw'], 'raw': raw}, ensure_ascii=False) + '\n')
        stream.flush()
    print(row['video'], raw, flush=True)

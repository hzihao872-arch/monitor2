"""Development-only visual change diagnostic. Never run on frozen new tests."""

import json
from pathlib import Path

import torch
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

from experiments.prerequisite_probe.run_monitor_qwen import FRAME_SECONDS, decode_selected


BASE = Path('/root/autodl-tmp/monitor2')
MODEL = Path('/root/autodl-tmp/hf/hub/models--Qwen--Qwen3-VL-8B-Instruct/snapshots/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b')
INPUT = BASE / 'experiments/prerequisite_probe/artifacts/model_input/0001.mp4'
OUT = BASE / 'new_tests/server_results/old_dev_visual_change_diag.json'
images, _ = decode_selected(INPUT)
processor = AutoProcessor.from_pretrained(MODEL, local_files_only=True)
model = Qwen3VLForConditionalGeneration.from_pretrained(
    MODEL, dtype=torch.bfloat16, attn_implementation='flash_attention_2',
    local_files_only=True).to('cuda').eval()
prompts = [
    'Describe only what happens to the red cube and green tray between the first and last frames. Cite seconds. Do not discuss the blue cube.',
    'Final goal: Put the blue cube in the green tray. Describe the robot action visible in this preparation video, including which object it moves and from where to where. Then say whether that changes any condition needed for the final goal. If uncertain, say so.',
]
rows = []
for prompt in prompts:
    content = [{'type': 'text', 'text': prompt}]
    for second, image in zip(FRAME_SECONDS, images):
        content.extend(({'type': 'text', 'text': f'Second {second}:'}, {'type': 'image', 'image': image}))
    inputs = processor.apply_chat_template(
        [{'role': 'user', 'content': content}], tokenize=True,
        add_generation_prompt=True, return_dict=True, return_tensors='pt').to('cuda')
    with torch.inference_mode():
        output = model.generate(**inputs, max_new_tokens=256, do_sample=False)
    raw = processor.batch_decode(output[:, inputs['input_ids'].shape[-1]:], skip_special_tokens=True)[0]
    rows.append({'prompt': prompt, 'raw': raw})
prompt = (
    'Final goal: Put the blue cube in the green tray. A visual observer of this same video reported: '
    + rows[0]['raw'] + '\nTreat that report as a fallible observation and verify it against the frames. '
    'For a single-arm top-down placement, compare whether the tray has usable space and access '
    'for the blue cube at second 0 versus second 14. Does removing the red cube change a necessary '
    'physical condition, even though the blue cube itself stays still? Identify an alternate route '
    'if visible, and say unknown if the geometry does not decide it.'
)
content = [{'type': 'text', 'text': prompt}]
for second, image in zip(FRAME_SECONDS, images):
    content.extend(({'type': 'text', 'text': f'Second {second}:'}, {'type': 'image', 'image': image}))
inputs = processor.apply_chat_template(
    [{'role': 'user', 'content': content}], tokenize=True,
    add_generation_prompt=True, return_dict=True, return_tensors='pt').to('cuda')
with torch.inference_mode():
    output = model.generate(**inputs, max_new_tokens=256, do_sample=False)
raw = processor.batch_decode(output[:, inputs['input_ids'].shape[-1]:], skip_special_tokens=True)[0]
rows.append({'prompt': prompt, 'raw': raw})
OUT.write_text(json.dumps(rows, indent=2), encoding='utf-8')
print(OUT)

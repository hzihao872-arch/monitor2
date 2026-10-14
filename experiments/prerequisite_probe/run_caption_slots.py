"""Frozen two-call action-caption / endpoint-fact Monitor candidate.

Inputs are only a goal instruction and its preparation video. The first call
describes visible motion; the second canonicalizes the caption into endpoint
facts. Fixed comparison logic does not inspect ground truth or continuations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path

from experiments.prerequisite_probe.run_monitor_qwen import (
    FRAME_SECONDS, collect_inputs, decode_selected, sha256,
)


TRI = {'true', 'false', 'unknown'}
FACT_KEYS = (
    'destination_non_goal_0', 'destination_non_goal_14',
    'source_non_goal_0', 'source_non_goal_14',
    'goal_complete_0', 'goal_complete_14',
)
VISUAL_PROMPT = (
    'Describe only visible changes in this tabletop robot video. State what the robot moved, '
    'where that object was at second 0 and second 14, and whether the source and destination '
    'areas are occupied or obstructed at those times. Distinguish moving an object away from '
    'returning it to the same place. Do not judge task progress. Reply in at most 70 words.'
)


def goal_parts(instruction: str) -> tuple[str, str]:
    match = re.fullmatch(r'Put the (.+?) in the (.+?)\.', instruction.strip())
    if not match:
        raise ValueError('unsupported goal grammar; abstain rather than guess source/destination')
    return match.group(1), match.group(2)


def canonical_prompt(instruction: str, caption: str) -> str:
    goal_object, destination = goal_parts(instruction)
    return (
        f'Final goal: {instruction} A fallible observer wrote this about the same '
        f'preparation video: {caption}\n'
        'Extract only what this text claims about the first and last state. Do not infer task '
        'progress or whether an object is relevant. If the text does not support a value, use '
        f'"unknown". Treat objects other than the {goal_object}, excluding the robot arm, as non-goal. '
        'Return exactly one JSON object with string fields destination_non_goal_0, '
        'destination_non_goal_14, source_non_goal_0, source_non_goal_14, '
        'goal_complete_0, goal_complete_14; values are only "true", "false", "unknown". '
        f'destination_non_goal means one is in or above the {destination} interior. '
        f'source_non_goal means one is in or above the {goal_object} grasp area. '
        'Use the first and last states, ignoring temporary movements. No markdown.'
    )


def parse_facts(raw: str) -> tuple[dict | None, list[str]]:
    try:
        facts = json.loads(raw)
    except (TypeError, ValueError) as exc:
        return None, [f'json_parse:{type(exc).__name__}']
    if not isinstance(facts, dict):
        return None, ['not_object']
    errors = ['bad_' + key for key in FACT_KEYS if facts.get(key) not in TRI]
    if errors:
        return facts, errors
    return facts, []


def direction(facts: dict | None, caption: str, errors: list[str]) -> tuple[str, str]:
    if errors or facts is None:
        return 'invalid', 'canonical_facts_invalid'
    if facts['goal_complete_0'] == 'false' and facts['goal_complete_14'] == 'true':
        return 'positive', 'goal_observed_complete'
    if facts['goal_complete_0'] == 'true' and facts['goal_complete_14'] == 'false':
        return 'negative', 'goal_observed_lost'
    clears = blocks = 0
    known_equal = 0
    unknown = 0
    for prefix in ('destination_non_goal', 'source_non_goal'):
        before, after = facts[prefix + '_0'], facts[prefix + '_14']
        if before == 'true' and after == 'false':
            clears += 1
        elif before == 'false' and after == 'true':
            blocks += 1
        elif before == after and before != 'unknown':
            known_equal += 1
        else:
            unknown += 1
    if clears and not blocks:
        return 'positive', 'visible_non_goal_slot_cleared_provisional'
    if blocks and not clears:
        return 'negative', 'visible_non_goal_slot_blocked_provisional'
    if clears and blocks:
        return 'uncertain', 'opposed_slot_changes'
    if known_equal == 2:
        return 'zero', 'both_slots_unchanged'
    if ('No visible object movement occurred' in caption or
            'remained in identical positions' in caption):
        return 'zero', 'caption_explicitly_static_provisional'
    return 'uncertain', 'insufficient_endpoint_facts'


def progress(facts: dict | None, label: str) -> list[dict]:
    points = [{'second': second, 'point': None, 'lower': 0, 'upper': 100}
              for second in range(15)]
    if facts is not None and facts.get('goal_complete_0') == 'true':
        points[0].update(point=100, lower=100, upper=100)
    elif label != 'invalid':
        points[0].update(point=0, lower=0, upper=25)
    if label == 'positive':
        end = 100 if facts and facts.get('goal_complete_14') == 'true' else 25
        points[14].update(point=end, lower=end, upper=end)
    elif label == 'negative':
        points[14].update(point=0, lower=0, upper=0)
    elif label == 'zero':
        points[14].update(point=points[0]['point'], lower=points[0]['lower'], upper=points[0]['upper'])
    return points


def generate(model, processor, content: list[dict], max_tokens: int) -> dict:
    import torch
    started = time.perf_counter()
    inputs = processor.apply_chat_template(
        [{'role': 'user', 'content': content}], tokenize=True,
        add_generation_prompt=True, return_dict=True, return_tensors='pt')
    input_tokens = int(inputs['input_ids'].shape[-1])
    inputs = inputs.to('cuda')
    torch.cuda.reset_peak_memory_stats()
    with torch.inference_mode():
        output = model.generate(**inputs, max_new_tokens=max_tokens, do_sample=False)
    raw = processor.batch_decode(output[:, input_tokens:], skip_special_tokens=True)[0]
    torch.cuda.synchronize()
    return {'raw': raw, 'input_tokens': input_tokens,
            'output_tokens': int(output.shape[-1] - input_tokens),
            'elapsed_ms': round((time.perf_counter() - started) * 1000),
            'peak_vram_bytes': int(torch.cuda.max_memory_allocated())}


def append(path: Path, row: dict) -> None:
    with path.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(row, ensure_ascii=False) + '\n')
        stream.flush()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', required=True, type=Path)
    parser.add_argument('--model-path', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    rows = collect_inputs(args.input_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    append(args.output, {'kind': 'configuration', 'input_dir': str(args.input_dir.resolve()),
                         'model_path': str(args.model_path.resolve()), 'visual_prompt': VISUAL_PROMPT,
                         'frame_seconds': FRAME_SECONDS, 'max_visual_tokens': 192,
                         'max_canonical_tokens': 192,
                         'runner_sha256': sha256(Path(__file__)),
                         'progress_semantics': 'endpoint evidence index, interior unknown'})
    import torch
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
    processor = AutoProcessor.from_pretrained(args.model_path, local_files_only=True)
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        args.model_path, dtype=torch.bfloat16, attn_implementation='flash_attention_2',
        local_files_only=True).to('cuda').eval()
    for row in rows:
        video = row['video']
        try:
            goal_parts(row['instruction'])
            images, frame_hashes = decode_selected(args.input_dir / video)
            content = [{'type': 'text', 'text': VISUAL_PROMPT}]
            for second, image in zip(FRAME_SECONDS, images):
                content.extend(({'type': 'text', 'text': f'Second {second}:'},
                                {'type': 'image', 'image': image}))
            visual = generate(model, processor, content, 192)
            append(args.output, {'kind': 'visual_call', 'video': video,
                                 'video_sha256': row['sha256'],
                                 'decoded_pixel_sha256': frame_hashes, **visual})
            prompt = canonical_prompt(row['instruction'], visual['raw'])
            canonical = generate(model, processor, [{'type': 'text', 'text': prompt}], 192)
            append(args.output, {'kind': 'canonical_call', 'video': video,
                                 'prompt': prompt, **canonical})
            facts, errors = parse_facts(canonical['raw'])
            label, reason = direction(facts, visual['raw'], errors)
            append(args.output, {'kind': 'result', 'video': video, 'facts': facts,
                                 'errors': errors, 'direction': label, 'reason': reason,
                                 'evidence_caption': visual['raw'],
                                 'requires_evidence_audit': True,
                                 'points': progress(facts, label)})
        except Exception as exc:
            append(args.output, {'kind': 'runtime_failure', 'video': video,
                                 'error': f'{type(exc).__name__}: {exc}',
                                 'direction': 'invalid', 'points': progress(None, 'invalid')})
    print(args.output.resolve())


if __name__ == '__main__':
    main()

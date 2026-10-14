"""Isolated, bounded R-C interface repair; original runners remain unchanged."""
import hashlib
import json
import time
from pathlib import Path

import experiments.monitor_eval as evaluation
import experiments.qwen_backend as qwen
from experiments.run_online import validate_media
from experiments.trace_diagnostic_20261003 import build_prompt as original_prompt, SUMMARY

ROOT = Path('experiments/artifacts/r1_interface_repair_20261003')
SOURCE = Path('research/sources/recovery_search_20261003/upstream_trace')
VARIANT = 'A'
BOUNDARY = '\nYour response must start with { and end with }. Return exactly one complete JSON object. Do not use code fences, markdown, explanations, or repeated keys. Keep the response short enough to finish within 256 tokens.'
SHORT_SUMMARY = ('Use the prior generic visual summary and supplied frames. Assess historical achievement H, current relation C, and whole-task completion G separately. '
                 'Write memory as a chronological visual summary in at most 35 English words, preserving earlier clear achievement and the latest arrangement, action, or uncertainty. '
                 'Correct unsupported earlier claims. Do not create a condition ledger or use future information.')


def build_prompt(method, instruction, objects, memory, tick):
    if method not in ('S0', 'S1'):
        raise ValueError('Only S0/S1 allowed')
    if VARIANT == 'A':
        return original_prompt(method, instruction, objects, memory, tick) + BOUNDARY
    if VARIANT != 'B':
        raise ValueError('Unknown frozen candidate')
    if method == 'S0':
        return original_prompt(method, instruction, objects, memory, tick) + BOUNDARY
    return original_prompt(method, instruction, objects, memory, tick).replace(SUMMARY, SHORT_SUMMARY) + BOUNDARY


def probe_usable(s0, s1):
    if len(s0) != 3 or len(s1) != 3:
        return False
    for rows in (s0, s1):
        if [r['tick'] for r in rows] != [0, 1, 2]:
            return False
        if any(r['parse_status'] != 'valid' or r.get('budget_reason') or
               r['cost']['output_tokens_known'] >= 256 or r['cost']['memory_tokens'] > 512 for r in rows):
            return False
    if any(not isinstance(r.get('memory_out'), str) or not r['memory_out'].strip() for r in s1):
        return False
    return all(s1[i]['memory_in'] == s1[i-1]['memory_out'] and bool(s1[i]['memory_in'].strip()) for i in (1, 2))


def save(name, obj):
    (ROOT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def run(track, backend, method, out):
    print(f'{VARIANT} {method} {out}', flush=True)
    summary = evaluation.run_track(track, backend, method, ROOT / out, 'experiments/run_ledger.csv')
    print(json.dumps(summary), flush=True)
    rows = [json.loads(x) for x in (ROOT / out / 'records.jsonl').read_text('utf-8').splitlines()]
    return summary, rows


def main():
    global VARIANT
    prereg = json.loads((ROOT / 'preregistration.json').read_text('utf-8'))
    assert prereg['max_model_calls'] == 74 and prereg['candidate_order'] == ['A', 'B']
    for row in prereg['frozen_files']:
        assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest() == row['sha256'], row['path']
    for ep in (618, 621):
        validate_media(evaluation.load_online_track(SOURCE / f'p0/ep{ep}/online_track.json'))
    evaluation.build_prompt = build_prompt
    qwen.build_prompt = build_prompt
    start = time.perf_counter()
    try:
        backend = qwen.QwenBackend('.models/qwen3-vl-2b-instruct')
    except Exception as exc:
        save('initialization.json', {'status': 'failed', 'error': repr(exc), 'seconds': time.perf_counter()-start})
        evaluation._append_ledger('experiments/run_ledger.csv', {'run_id': 'r1-interface-repair-init', 'kind': 'exploratory_init', 'status': 'failed', 'error': repr(exc)})
        raise
    save('initialization.json', {'status': 'loaded', 'seconds': time.perf_counter()-start})
    selected = None
    selection = []
    for variant in prereg['candidate_order']:
        VARIANT = variant
        evaluation.PROMPT_VERSION = f'r1-interface-repair-{variant}'
        results = []
        for method in ('S0', 'S1'):
            summary, rows = run(ROOT / 'probe_track.json', backend, method, f'probe_{variant}_{method}')
            results.append(rows)
            if summary['status'] != 'completed':
                save('selection.json', {'status': 'runtime_failure_stop', 'attempted': selection, 'failed_candidate': variant, 'method': method})
                return
        usable = probe_usable(*results)
        selection.append({'candidate': variant, 'interface_gate_passed': usable})
        save('selection.json', {'status': 'probing', 'attempted': selection})
        if usable:
            selected = variant
            break
    save('selection.json', {'status': 'selected' if selected else 'both_candidates_failed_stop', 'selected': selected, 'attempted': selection, 'uses_truth_labels': False})
    if selected is None:
        return
    for ep in (618, 621):
        for method in ('S0', 'S1'):
            summary, _ = run(SOURCE / f'p0/ep{ep}/online_track.json', backend, method, f'full_ep{ep}_{method}')
            if summary['status'] != 'completed':
                return


if __name__ == '__main__':
    main()

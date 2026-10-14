"""Post-seal offline scoring of frozen caption-slot runs; never uploaded to cloud."""

import argparse
import json
from pathlib import Path

from experiments.prerequisite_probe.run_monitor_qwen import sha256


EXPECTED = {'B+': 'positive', 'B0': 'zero', 'U0': 'zero',
            'H-': 'negative', 'G+': 'positive', 'N0': 'zero'}
RANK = {'negative': -1, 'zero': 0, 'positive': 1}
PAIRS = [('B+', 'B0', '>'), ('B+', 'U0', '>'),
         ('H-', 'N0', '<'), ('G+', 'N0', '>')]


def score(root: Path, jsonl: Path, output: Path) -> dict:
    if output.exists():
        raise FileExistsError(output)
    freeze = root / 'truth/frozen_test.json'
    if sha256(freeze) != (root / 'truth/frozen_test.sha256').read_text().strip():
        raise ValueError('frozen truth hash mismatch')
    manifest = json.loads(freeze.read_text(encoding='utf-8'))
    labels = {f'{stem}.mp4': case['condition'] for stem, case in manifest['cases'].items()}
    rows = [json.loads(line) for line in jsonl.read_text(encoding='utf-8').splitlines()
            if line.strip()]
    by_video = {}
    for row in rows:
        if row.get('kind') in ('result', 'runtime_failure'):
            if row['video'] in by_video:
                raise ValueError(f'duplicate result: {row["video"]}')
            by_video[row['video']] = row
    if set(by_video) - set(labels):
        raise ValueError('unmanifested result')
    counts = {key: 0 for key in ('correct', 'wrong', 'uncertain', 'invalid', 'missing')}
    cases = {}
    for video, condition in labels.items():
        row = by_video.get(video)
        direction = row.get('direction') if row else None
        if row is None:
            counts['missing'] += 1
        elif direction == 'uncertain':
            counts['uncertain'] += 1
        elif direction not in RANK:
            counts['invalid'] += 1
        elif direction == EXPECTED[condition]:
            counts['correct'] += 1
        else:
            counts['wrong'] += 1
        cases[condition] = {'video': video, 'direction': direction,
                            'expected': EXPECTED[condition],
                            'reason': row.get('reason') if row else None,
                            'errors': row.get('errors') if row else None}
    pairs = {}
    for left, right, operator in PAIRS:
        a, b = cases[left]['direction'], cases[right]['direction']
        if a not in RANK or b not in RANK:
            pairs[f'{left}{operator}{right}'] = None
        else:
            pairs[f'{left}{operator}{right}'] = (
                RANK[a] > RANK[b] if operator == '>' else RANK[a] < RANK[b])
    calls = [row for row in rows if row.get('kind') in ('visual_call', 'canonical_call')]
    budget = {'calls': len(calls),
              'input_tokens': sum(row.get('input_tokens', 0) for row in calls),
              'output_tokens': sum(row.get('output_tokens', 0) for row in calls),
              'elapsed_ms': sum(row.get('elapsed_ms', 0) for row in calls),
              'peak_vram_bytes_max': max((row.get('peak_vram_bytes', 0) for row in calls), default=0)}
    report = {'scene': manifest['scene_family'], 'total': len(labels), **counts,
              'pairs': pairs, 'cases': cases, 'budget': budget,
              'model_output_sha256': sha256(jsonl),
              'truth_freeze_sha256': sha256(freeze),
              'evidence_audit': 'pending',
              'caveat': 'Clearance-slot direction is provisional, not causal necessity proof.'}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--jsonl', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(score(args.root, args.jsonl, args.output), ensure_ascii=False))


if __name__ == '__main__':
    main()

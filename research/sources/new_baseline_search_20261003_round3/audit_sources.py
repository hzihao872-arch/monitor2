from pathlib import Path
from collections import Counter
import hashlib, json, re

B = Path(__file__).resolve().parent
def read(name):
    return json.loads((B / name).read_text(encoding='utf-8'))

manifest = read('fetch_manifest.json')
checks = []
for row in manifest:
    if 'sha256' in row:
        data = (B / row['file']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == row['sha256'], row['file']
        assert len(data) == row['bytes'], row['file']
        checks.append(row['file'])
episodes = read('pro_data_failtime_long_test.json')
assert len({e['sample'] for e in episodes}) == len(episodes)
failures = [e for e in episodes if e['verdict'] == 'fail']
stats = {
    'episodes': len(episodes), 'tasks': len({e['task_id'] for e in episodes}),
    'verdicts': dict(Counter(e['verdict'] for e in episodes)),
    'robots': dict(Counter(e['robot'] for e in episodes)),
    'failure_types_multilabel': dict(Counter(t for e in failures for t in e['type'])),
    'prediction_outputs_found_in_inspected_repo_tree': [x['path'] for x in read('protracer_tree.json')['tree'] if re.search(r'(prediction|results|runs)/.*\.(json|jsonl|csv)$',x['path'])],
    'paper_long_onset_at_half_second_count_if_57_denominator': round(40.35 * 57 / 100),
    'paper_long_onset_at_one_second_count_if_57_denominator': round(49.12 * 57 / 100),
    'note': 'Metadata audit only. Counts inferred from rounded paper percentages are not recovered per-example model predictions.',
    'protracer_commit': read('protracer_tree.json')['sha'],
    'sarm2_commit': read('sarm2_tree.json')['sha'],
    'failtime_revision': read('failtime_api.json')['sha'],
    'source_files_verified': len(checks),
    'source_bytes': sum(r.get('bytes',0) for r in manifest),
    'fetch_errors': [r for r in manifest if 'error' in r]
}
(B/'metadata_audit.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(stats,ensure_ascii=False,indent=2))

"""Read-only source audit; no model imports, inference, or experiment records."""
from pathlib import Path
from hashlib import sha256
import json
import subprocess
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REV = '34e8cd4396fe903d6205028da17e32ba01d723d9'

def digest(p):
    return sha256(p.read_bytes()).hexdigest()

def save_json(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

if (OUT / 'before_edit.json').exists():
    raise SystemExit('Baseline already exists; do not overwrite history.')

paths = [
    'research/status.md', 'research/decision_log.md',
    'research/07_alternative_sources_review.md', 'research/existing_problem_evidence.md',
    'docs/plans/2026-10-03-task-progress-research-replan.md',
    'experiments/data_manifest.json', 'experiments/run_ledger.csv',
    'research/07_evaluation_protocol.md', 'research/08_pilot_report.md',
    'experiments/config_stage7.json',
]
baseline = []
for name in paths:
    p = ROOT / name
    backup = OUT / 'before' / name
    backup.parent.mkdir(parents=True, exist_ok=True)
    backup.write_bytes(p.read_bytes())
    baseline.append({'path': name, 'sha256': digest(p), 'bytes': p.stat().st_size})
save_json('before_edit.json', baseline)

tree = json.loads(subprocess.check_output([
    'gh', 'api', f'repos/YuyangLiu2003/PRM-as-a-Judge/git/trees/{REV}',
    '-f', 'recursive=1', '--method', 'GET'], text=True, encoding='utf-8'))
save_json('official_repo_tree.json', tree)
assert tree['sha'] == REV and not tree.get('truncated')

fetches = []
for name in ['README.md', 'eval/README.md', 'eval/prm_judge/prm/robometer.py',
             'eval/prm_judge/prm/dopamine_inference.py', 'eval/examples/manifest_recorded.jsonl']:
    url = f'https://raw.githubusercontent.com/YuyangLiu2003/PRM-as-a-Judge/{REV}/{name}'
    with urllib.request.urlopen(url, timeout=30) as r:
        data = r.read(600001)
    assert len(data) <= 600000
    p = OUT / 'official' / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    fetches.append({'url': url, 'path': p.relative_to(ROOT).as_posix(),
                    'bytes': len(data), 'sha256': digest(p), 'revision': REV})
url = 'https://prm-as-a-judge.github.io/advanced.html'
with urllib.request.urlopen(url, timeout=30) as r:
    data = r.read(600001)
assert len(data) <= 600000
p = OUT / 'official' / 'advanced.html'
p.write_bytes(data)
fetches.append({'url': url, 'path': p.relative_to(ROOT).as_posix(), 'bytes': len(data),
                'sha256': digest(p), 'revision': 'retrieval snapshot; unpinned website'})
save_json('source_manifest.json', {
    'date': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
    'purpose': 'Targeted paper scope and available author resources; no inference',
    'repo_revision': REV,
    'files': fetches,
    'reused_paper': {'path': 'research/sources/recovery_search_20261003/robopulse_paper.html',
                     'sha256': digest(ROOT / 'research/sources/recovery_search_20261003/robopulse_paper.html'),
                     'url': 'https://arxiv.org/html/2608.14284v1'},
    'access_notes': ['Unauthenticated urllib GitHub API tree request returned HTTP 403 rate limit exceeded; no content saved as success.',
                     'git ls-remote resolved HEAD; existing authenticated gh read-only API retrieved pinned complete tree.',
                     'web tool eval-directory fetch failed; tree API used instead.'],
    'no_models_run': True,
})
print(json.dumps({'repo_revision': REV, 'tree_blobs': sum(x['type']=='blob' for x in tree['tree']),
                  'downloaded_text_bytes': sum(x['bytes'] for x in fetches),
                  'preserved_files': len(baseline)}, ensure_ascii=False))

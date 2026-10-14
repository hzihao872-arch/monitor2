"""Validate this documentation-only audit without loading any model code."""
from pathlib import Path
import hashlib
import json
import re
from urllib.parse import unquote, urlsplit
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
DOCS = [
    'research/status.md', 'research/decision_log.md',
    'research/07_alternative_sources_review.md', 'research/existing_problem_evidence.md',
    'docs/plans/2026-10-03-task-progress-research-replan.md',
    'research/prm_robopulse_scope_review.md',
]
UNCHANGED = ['experiments/data_manifest.json', 'experiments/run_ledger.csv',
             'research/07_evaluation_protocol.md', 'research/08_pilot_report.md',
             'experiments/config_stage7.json']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def text(path):
    return path.read_text(encoding='utf-8-sig')

def slug(heading):
    heading = re.sub(r'[`*_]', '', heading).strip().lower()
    heading = re.sub(r'[^\w\- ]', '', heading, flags=re.UNICODE)
    return heading.replace(' ', '-')

errors = []
baseline = json.loads(text(OUT / 'before_edit.json'))
unchanged = []
history = []
for entry in baseline:
    p = ROOT / entry['path']
    if entry['path'] in UNCHANGED:
        ok = sha(p) == entry['sha256']
        unchanged.append({'path': entry['path'], 'byte_identical': ok, 'sha256': sha(p)})
        if not ok:
            errors.append('Unexpected mutation: ' + entry['path'])
    else:
        old = text(OUT / 'before' / entry['path']).splitlines()
        new = iter(text(p).splitlines())
        ok = all(any(v == line for v in new) for line in old)
        history.append({'path': entry['path'], 'all_prior_lines_preserved_in_order': ok})
        if not ok:
            errors.append('History changed: ' + entry['path'])

links = []
paper = BeautifulSoup(text(ROOT / 'research/sources/recovery_search_20261003/robopulse_paper.html'), 'html.parser')
paper_anchors = []
for name in DOCS:
    p = ROOT / name
    for target in re.findall(r'!?\[[^\]\n]*\]\(([^)\n]+)\)', text(p)):
        target = target.strip('<>')
        parsed = urlsplit(target)
        if parsed.scheme in ('http', 'https', 'mailto', 'app', 'codex'):
            if parsed.netloc == 'arxiv.org' and parsed.path == '/html/2608.14284v1' and parsed.fragment:
                ok = paper.find(id=parsed.fragment) is not None
                paper_anchors.append({'source': name, 'anchor': parsed.fragment, 'exists_in_fixed_html': ok})
                if not ok:
                    errors.append('Paper anchor missing: ' + target)
            continue
        dest, _, fragment = unquote(target).partition('#')
        path = (p.parent / dest).resolve() if dest else p
        ok = path.exists()
        if ok and fragment and path.suffix.lower() == '.md':
            anchors = [slug(x) for x in re.findall(r'^#{1,6}\s+(.+?)\s*#*$', text(path), re.M)]
            ok = fragment in anchors
        links.append({'source': name, 'target': target, 'valid': ok})
        if not ok:
            errors.append('Broken local link: ' + name + ' -> ' + target)

json_count = 0
for area in [ROOT / 'research', ROOT / 'experiments']:
    for path in area.rglob('*.json'):
        if 'before' in path.parts or path == OUT / 'validation.json':
            continue
        try:
            json.loads(text(path))
            json_count += 1
        except Exception as exc:
            errors.append('JSON parse: ' + str(path.relative_to(ROOT)) + ': ' + str(exc))

manifest = json.loads(text(ROOT / 'experiments/data_manifest.json'))
hash_checks = []
for source in manifest['sources']:
    for entry in source.get('files', []):
        p = ROOT / entry['path']
        ok = p.is_file() and sha(p) == entry['sha256']
        hash_checks.append({'path': entry['path'], 'match': ok})
        if not ok:
            errors.append('Data manifest hash: ' + entry['path'])
sources = json.loads(text(OUT / 'source_manifest.json'))
for entry in sources['files'] + [sources['reused_paper']]:
    p = ROOT / entry['path']
    ok = p.is_file() and sha(p) == entry['sha256']
    hash_checks.append({'path': entry['path'], 'match': ok})
    if not ok:
        errors.append('Source hash: ' + entry['path'])

decisions = re.findall(r'^\| (D\d+) /', text(ROOT / 'research/decision_log.md'), re.M)
if decisions != [f'D{i:03}' for i in range(1, 58)]:
    errors.append('Decision sequence not D001..D057')
if manifest['version'] != 'S7-screening-4':
    errors.append('Manifest version changed')
if '版本：`S6-draft-4`' not in text(ROOT / 'research/07_evaluation_protocol.md'):
    errors.append('Protocol version changed')

index = {
    'paper_url': 'https://arxiv.org/html/2608.14284v1',
    'paper_sha256': sources['reused_paper']['sha256'],
    'sections_read': ['S2', 'S3 introductory text', 'S5', 'A2.SS1', 'A3', 'A4', 'A6.SS1'],
    'table8_author_reported_accuracy': {
        'Robo-Dopamine Forward': {'Rising': .844, 'Falling': .408, 'Overall': .746},
        'RoboMeter': {'Rising': .951, 'Falling': .901, 'Overall': .940}},
    'table8_subset_ids_and_per_example_predictions': 'Not supplied in C.5.2; not found in inspected toolkit tree',
    'table7_denominator': '155 intervals annotated Falling, not established as 155 judge prediction errors',
    'scope': 'source review, no new model experiment or independent labels',
    'next_source': 'https://github.com/robometer/robometer/blob/352d160389daa964788de1ec933d1925f3a6de4f/robometer/evals/eval_server.py',
    'remaining_question': 'Frame visibility of use_frame_steps on server; then whether native/adapted strong method can answer condition validity',
}
(OUT / 'evidence_index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
result = {
    'date': '2026-10-03 Asia/Shanghai',
    'scope': 'Documentation, provenance and file integrity only; no model/label agreement test',
    'passed': not errors, 'errors': errors,
    'modified_document_count': len(DOCS), 'unchanged_files': unchanged,
    'history_preservation': history, 'local_link_count': len(links),
    'local_links': links, 'paper_anchor_checks': paper_anchors,
    'parsed_json_files': json_count, 'hash_check_count': len(hash_checks), 'hash_checks': hash_checks,
    'decisions_last': decisions[-1], 'protocol': 'S6-draft-4', 'manifest': manifest['version'],
    'model_runs_this_audit': 0, 'new_run_ledger_entries': 0,
}
(OUT / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: result[k] for k in ['passed', 'errors', 'local_link_count', 'parsed_json_files', 'hash_check_count', 'decisions_last']}, ensure_ascii=False, indent=2))
raise SystemExit(0 if not errors else 1)

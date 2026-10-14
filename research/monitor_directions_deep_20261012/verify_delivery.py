"""Verify document links, structured artifacts, and archived-source hashes."""
from pathlib import Path
import csv, hashlib, json, re
from datetime import datetime, timezone
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parent
required=['FOR_SENIOR_REPORT_zh.md','REPORT_zh.md','OVERLAP_MATRIX_zh.md','overlap_matrix.csv','LITERATURE_SOURCES_zh.md','literature_sources.json','DISCUSSION_WITH_SENIOR_zh.md','DISCUSSION_WITH_SENIOR_previous_zh.md','README.md','evidence_a.md','evidence_b.md','evidence_c.md','evidence_root.md','SOURCE_MANIFEST_root.json']
errors=[]
for name in required:
    p=ROOT/name
    if not p.exists() or p.stat().st_size==0: errors.append('Missing/empty: '+name)
local_links=0
for name in required:
    if not name.endswith('.md'): continue
    p=ROOT/name
    content=p.read_text(encoding='utf-8')
    if re.search(r'arxiv\.org/(?:abs|html)/\d{4}\.\d+(?:v\d+){2}',content): errors.append('Malformed repeated arXiv version: '+name)
    for target in re.findall(r'\]\(([^\n]+?)\)',content):
        target=target.strip('<>').split(' "')[0]
        if re.match(r'^(https?://|#|codex://)',target): continue
        target=unquote(target.split('#')[0])
        local_links+=1
        if not (p.parent/target).exists(): errors.append(f'Broken local link {name}: {target}')
    if content.count('```')%2: errors.append('Unbalanced fenced code: '+name)
    # Ensure each contiguous Markdown table has a consistent width.
    widths=[]
    for line in content.splitlines()+['']:
        if line.startswith('|'):
            widths.append(len(re.split(r'(?<!\\)\|',line))-2)
        else:
            if len(set(widths))>1: errors.append(f'Inconsistent table width: {name} {widths}')
            widths=[]
sources=json.loads((ROOT/'literature_sources.json').read_text(encoding='utf-8'))['sources']
if len(sources)!=56: errors.append('Source count mismatch')
if len({s['id'] for s in sources})!=len(sources): errors.append('Duplicate source IDs')
with (ROOT/'overlap_matrix.csv').open(encoding='utf-8-sig',newline='') as f:
    matrix=list(csv.DictReader(f))
if len(matrix)!=27 or len({r['id'] for r in matrix})!=27: errors.append('Matrix row/ID mismatch')
if any(any(v is None or not v for v in r.values()) for r in matrix): errors.append('Empty matrix cell')
manifest=json.loads((ROOT/'SOURCE_MANIFEST_root.json').read_text(encoding='utf-8'))
verified=0
archived_errors=[]
for item in manifest:
    if 'error' in item:
        archived_errors.append(item); continue
    p=ROOT/item['file']
    if not p.exists(): errors.append('Missing source snapshot: '+item['file']); continue
    b=p.read_bytes()
    if len(b)!=item['bytes'] or hashlib.sha256(b).hexdigest()!=item['sha256']:
        errors.append('Source hash/size mismatch: '+item['file'])
    else: verified+=1
report=(ROOT/'REPORT_zh.md').read_text(encoding='utf-8')
for marker in ['oracle下游价值诊断','冻结V-JEPA2','同样action/skill','失败后果尚未发生','RSI不纳入','标注分钟','固定遗忘集']:
    if marker not in report: errors.append('Missing review correction: '+marker)
senior=(ROOT/'FOR_SENIOR_REPORT_zh.md').read_text(encoding='utf-8')
for heading in ['### 1．师姐的直觉','### 2．相关论文已经做到哪里','### 3．从这些边界提出一个idea']:
    if senior.count(heading)!=3: errors.append('Senior report must contain exactly three sections of: '+heading)
if senior.count('**候选问题：')!=3: errors.append('Senior report must contain exactly one candidate question per direction')
if '有条件优先A' in senior or 'B作为第二候选' in senior: errors.append('Old route ranking leaked into senior report')
if '最终取舍留给师姐' not in senior: errors.append('Missing decision role in senior report')
result={'verified_utc':datetime.now(timezone.utc).isoformat(),'required_files':len(required),'local_links_checked':local_links,'matrix_rows':len(matrix),'source_entries':len(sources),'archived_source_hashes_verified':verified,'recorded_source_fetch_errors':archived_errors,'errors':errors,'scope':'Document integrity and recorded source hashes only; no experimental replication or proof of novelty.'}
(ROOT/'DELIVERY_VERIFICATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
files=[]
for name in required+['build_delivery.py','verify_delivery.py','snapshot_sources.py','DELIVERY_VERIFICATION.json']:
    p=ROOT/name
    if p.exists(): files.append({'file':name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(ROOT/'DELIVERY_MANIFEST.json').write_text(json.dumps({'created_utc':datetime.now(timezone.utc).isoformat(),'files':files},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))

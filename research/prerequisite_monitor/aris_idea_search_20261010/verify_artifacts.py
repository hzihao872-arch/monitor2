from pathlib import Path
import json, re
from datetime import datetime
root = Path(r'D:\monitor2\research\prerequisite_monitor\aris_idea_search_20261010')
pool = json.loads((root/'idea-stage/CANDIDATE_POOL.json').read_text(encoding='utf-8-sig'))
report = (root/'idea-stage/IDEA_REPORT.md').read_text(encoding='utf-8-sig')
ids = [c['id'] for c in pool['candidates']]
keys = [c['dedup_key'] for c in pool['candidates']]
required = [
'idea-stage/RESEARCH_BRIEF.md', 'idea-stage/CANDIDATE_POOL.json',
'idea-stage/LITERATURE_EVIDENCE.md', 'idea-stage/ADDITIONAL_PRIOR_WORK.md',
'idea-stage/IDEA_REPORT.md', 'refine-logs/FINAL_PROPOSAL.md',
'refine-logs/EXPERIMENT_PLAN.md',
'.aris/traces/novelty-check/2026-10-10_run01/001-fresh-jury.response.md',
'.aris/traces/research-review/2026-10-10_run01/001-critical-review.response.md',
'.aris/traces/research-review/2026-10-10_run01/002-revision-check.response.md']
missing = [p for p in required if not (root/p).is_file() or not (root/p).stat().st_size]
missing_refs=[]
for name in ['idea-stage/IDEA_REPORT.md','refine-logs/FINAL_PROPOSAL.md','refine-logs/EXPERIMENT_PLAN.md']:
    for ref in re.findall(r'\]\((D:/[^)]+)\)', (root/name).read_text(encoding='utf-8-sig')):
        if not Path(ref).exists(): missing_refs.append(ref)
missing_ids=[i for i in ids if not re.search(r'\b'+i+r'\b',report)]
json_paths=list((root/'.aris').rglob('*.json'))
json_fail=[]
for p in json_paths:
    try: json.loads(p.read_text(encoding='utf-8-sig'))
    except Exception as e: json_fail.append({'file':str(p),'error':str(e)})
checks={
'required_artifacts_present':not missing,
'candidate_count_17':len(ids)==17,
'unique_ids_and_dedup_keys':len(set(ids))==17 and len(set(keys))==17,
'all_candidates_in_report':not missing_ids,
'local_document_links_resolve':not missing_refs,
'latest_report_matches_timestamp':(root/'idea-stage/IDEA_REPORT.md').read_bytes()==(root/'idea-stage/IDEA_REPORT_20261010_114500.md').read_bytes(),
'latest_plan_matches_timestamp':(root/'refine-logs/EXPERIMENT_PLAN.md').read_bytes()==(root/'refine-logs/EXPERIMENT_PLAN_20261010_114325.md').read_bytes(),
'latest_proposal_matches_timestamp':(root/'refine-logs/FINAL_PROPOSAL.md').read_bytes()==(root/'refine-logs/FINAL_PROPOSAL_20261010_114325.md').read_bytes(),
'trace_json_parse':not json_fail,
'no_empirical_acceptance_claim':all(x in report for x in ['实验未执行','same-family / provisional','不能预设ARS','不是change-first独占']),
}
validation={'checked_at':datetime.now().isoformat(timespec='seconds'),'kind':'document_completeness_only','checks':checks,'missing_files':missing,'missing_links':missing_refs,'missing_candidate_ids':missing_ids,'invalid_trace_json':json_fail,'research_effectiveness_verified':False}
(root/'VERIFICATION.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
outputs=[]
for p in sorted(root.rglob('*')):
    if not p.is_file(): continue
    rel=p.relative_to(root).as_posix()
    if rel.startswith(('remote/','aris_skills/')) or rel=='MANIFEST.md': continue
    outputs.append((p,rel))
rows=['# Research Output Manifest','','Scope: generated research outputs, review traces and cached evidence in this ARIS run. Borrowed skill source trees are excluded. No experiment outputs were generated.','','| Timestamp | Skill | File | Stage | Description |','|---|---|---|---|---|']
for p,rel in outputs:
    if rel.startswith('.aris/traces/novelty-check'): skill='novelty-check'; desc='review trace'
    elif rel.startswith('.aris/traces/research-review'): skill='research-review'; desc='review trace'
    elif rel.startswith('sources/'): skill='research-lit'; desc='cached primary evidence or search receipt'
    else: skill='idea-discovery-robot'; desc='research-only artifact'
    stamp=datetime.fromtimestamp(p.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    rows.append(f'| {stamp} | {skill} | [{rel}]({rel}) | idea-discovery | {desc} |')
(root/'MANIFEST.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')
print(json.dumps({'checks':checks,'indexed_files':len(outputs),'missing_files':missing,'missing_links':missing_refs},ensure_ascii=False))
if not all(checks.values()): raise SystemExit(1)


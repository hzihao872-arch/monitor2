from pathlib import Path
from itertools import combinations
from collections import Counter
import json,hashlib,re
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf-8')
clips=read(OUT/'clip_registry.json');order={'failure':1,'suboptimal':2,'success':3};pairs=[]
for a,b in combinations(clips,2):
 if a['quality_label']==b['quality_label']:continue
 chosen,rejected=(a,b) if order[a['quality_label']]>order[b['quality_label']] else (b,a)
 pairs.append(dict(pair_id=f'Q{len(pairs)+1:02d}',task='Unzip the pencil case',preferred_id=chosen['id'],rejected_id=rejected['id'],preferred_clip=chosen['path'],rejected_clip=rejected['path'],quality_pair=[chosen['quality_label'],rejected['quality_label']],prediction=None))
save(OUT/'native_pair_input_manifest.json',dict(status='input inventory only; not inference preregistration or paper retrieval reproduction',rule='all unordered cross-quality pairs from all seven author-labelled task clips',quality_normalization='standalone success corresponds to sampler successful; no change to source labels',unique_episodes=7,pair_count=len(pairs),pairs=pairs,missing=['exact local checkpoint and runtime readiness','actual paper wrist-camera configuration','fixed A/B presentation and frame sampling before inference','Table XXVI retrieval win-matrix aggregation and exact candidate IDs'],new_task_output=False,models_run=0))
save(OUT/'visual_notes.json',dict(status='single reviewer exploratory observation; not independent relabeling',frames_per_video=[0,8,16,24,32,40,48,63],all_seven_included=True,observations='All quality groups show approaching the same pencil-case and manipulation around its zipper; fine local opening, gripper occlusion and wrist-camera motion are competing explanations, not established monitor error causes.',author_labels_unchanged=True,author_selected_failure_id=None))
dm_path=ROOT/'experiments/data_manifest.json';dm=read(dm_path)
dm['native_error_leads_20261003']=dict(report='research/native_error_direction_update_20261003.md',dataset='robometer/rbm-1m-ood',revision='3f3ee69ecc0ee0db627684da7d599ec26d08175c',source_manifest=(OUT/'fetch_manifest.json').relative_to(ROOT).as_posix(),clip_registry=(OUT/'clip_registry.json').relative_to(ROOT).as_posix(),binding=(OUT/'task_episode_bindings.json').relative_to(ROOT).as_posix(),task='Unzip the pencil case',seven_clips=7,quality_counts=dict(Counter(c['quality_label'] for c in clips)),derived_frames=56,author_error='Table XXVI task-level Pref retrieval includes one failure; exact selected ID unavailable',per_episode_predictions=False,split='development only; all matched physical duplicates and views; no new UUID creates holdout eligibility',models_run=0,license='Apache-2.0 dataset card; original upstream not separately re-audited',cross_layout_identity='ordinal/task/source/quality matches only, not pixel verified')
save(dm_path,dm)
fetch=read(OUT/'fetch_manifest.json');checks={}
checks['download_hashes']=all((ROOT/x['path']).stat().st_size==x['bytes'] and sha(ROOT/x['path'])==x['sha256'] for x in fetch)
checks['existing_source_hashes']=all(sha(ROOT/x['path'])==x['sha256'] for x in read(OUT/'source_hashes.json'))
old=read(ROOT/'research/sources/replan_r1/fetch_manifest.json')['records']
checks['reused_against_original_manifest']=all(sha(ROOT/x['path'])==x['sha256'] for x in old if Path(x['path']).name in ['rbm_tasks.parquet','rbm_data.parquet','rbm_episodes.parquet','rbm_tree.json','rbm_README.md','rbm_export_summary.json','rbm_code_tree.json'])
checks['budget']=5402835+sum(x['bytes'] for x in fetch)<=6*1024*1024
checks['seven_labels']=Counter(c['quality_label'] for c in clips)=={'success':3,'suboptimal':2,'failure':2}
checks['sixteen_pairs']=len(pairs)==16
checks['56_derived_frames']=len(read(OUT/'derived_frames.json'))==56 and all(sha(OUT/x['path'])==x['sha256'] for x in read(OUT/'derived_frames.json'))
checks['no_predictions']=all(p['prediction'] is None for p in pairs)
before=read(OUT/'before_edit.json');protected=['experiments/run_ledger.csv','research/08_pilot_report.md','research/07_evaluation_protocol.md','experiments/config_stage7.json']
checks['protected_unchanged']=all(sha(ROOT/x['path'])==x['sha256'] for x in before if x['path'] in protected)
save(OUT/'validation.json',dict(status='pending'))
report=ROOT/'research/native_error_direction_update_20261003.md'
links=re.findall(r'\]\(([^)]+)\)',report.read_text('utf-8'))
bad=[s for s in links if not s.startswith(('http:','https:','#')) and not (report.parent/s.split('#')[0]).exists()]
checks['report_links']=not bad
checks['json_valid']=all(read(p) is not None for p in OUT.glob('*.json')) and read(dm_path) is not None
save(OUT/'validation.json',dict(passed=all(checks.values()),checks=checks,bad_links=bad,source_bytes=sum(x['bytes'] for x in fetch),combined_bytes=5402835+sum(x['bytes'] for x in fetch),models_run=0))
files=[p for p in OUT.rglob('*') if p.is_file() and p.name!='artifact_hashes.json']
save(OUT/'artifact_hashes.json',[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in files])
print(json.dumps(checks,ensure_ascii=False));assert all(checks.values())

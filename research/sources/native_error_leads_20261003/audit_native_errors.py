"""Native author-error audit. Run with existing Python312 / PyArrow25."""
from pathlib import Path
import json,hashlib,collections,urllib.request,datetime
import pyarrow.parquet as pq
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
OLD=ROOT/'research/sources/replan_r1'
REV='3f3ee69ecc0ee0db627684da7d599ec26d08175c'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,obj):(OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n','utf-8')
if not (OUT/'before_edit.json').exists():
 save('before_edit.json',[dict(path=p,sha256=sha(ROOT/p)) for p in ['research/status.md','research/decision_log.md','experiments/data_manifest.json','experiments/run_ledger.csv','research/08_pilot_report.md','research/07_evaluation_protocol.md','experiments/config_stage7.json']])
save('scope.json',dict(purpose='Find author-reported native errors first; exploratory teacher-discussion leads, not established new gaps',models_run=0,new_weights=0,max_additional_download_bytes=524288,inclusion='All native RoboMeter failure-detection task rows and both controlled retrieval task rows; all seven public pencil-case episodes, no selection by model output',holdout_eligible=False,excluded_as_new_gap=['known task-context problem','correct failure detections presented as errors','HD prescreen']))
tasks={r['task_index']:r['__index_level_0__'] for r in pq.read_table(OLD/'rbm_tasks.parquet').to_pylist()}
frames=pq.read_table(OLD/'rbm_data.parquet').to_pylist();first={}
for r in frames:first.setdefault(r['episode_index'],r)
eps={r['episode_index']:r for r in pq.read_table(OLD/'rbm_episodes.parquet').to_pylist()}
tree=json.loads((OLD/'rbm_tree.json').read_text('utf-8'))
entry=next(r for r in tree if r['path']=='train/metadata.parquet')
p=OUT/'train_metadata.parquet';url=f'https://huggingface.co/datasets/robometer/rbm-1m-ood/resolve/{REV}/train/metadata.parquet'
if not p.exists():
 assert entry['size']<524288
 req=urllib.request.Request(url,method='HEAD');res=urllib.request.urlopen(req,timeout=35);head=dict(res.headers)
 res=urllib.request.urlopen(url,timeout=35);b=res.read(entry['size']+1)
 assert len(b)==entry['size']
 assert hashlib.sha256(b).hexdigest()==entry['lfs']['oid']
 p.write_bytes(b)
 save('fetch_manifest.json',[dict(url=url,revision=REV,path=p.relative_to(ROOT).as_posix(),bytes=len(b),sha256=sha(p),size_check='fixed tree size and LFS oid before GET; HEAD',head_content_length=head.get('Content-Length'),retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())])
rows=pq.read_table(p).to_pylist()
byid=collections.defaultdict(list)
for r in rows:byid[r['id']].append(r)
bindings=[]
for r in first.values():
 if r['task_index'] not in [1,3,6,10,11,12]:continue
 e=eps[r['episode_index']]
 bindings.append(dict(task=tasks[r['task_index']],id=r['id'],episode_index=r['episode_index'],quality_label=r['quality_label'],data_source=r['data_source'],length=e['length'],aggregate_video=f"videos/video/chunk-{e['videos/video/chunk_index']:03d}/file-{e['videos/video/file_index']:03d}.mp4",aggregate_from=e['videos/video/from_timestamp'],aggregate_to=e['videos/video/to_timestamp'],time_semantics='resampled export playback seconds; NOT original robot time',standalone_matches=byid[r['id']],author_prediction=None,paper_exact_pool_identity='task/source/count matched only; no author evaluation ID list'))
save('task_episode_bindings.json',dict(revision=REV,license='Apache-2.0 dataset card; original upstream license not independently re-audited',split='export calls train; export_summary says eval; all inspected material development-only',pencil_case=[r for r in bindings if r['task']=='Unzip the pencil case'],red_drawer=[r for r in bindings if r['task']=='Open the red drawer'],other_task_candidates=[r for r in bindings if r['task'] not in ['Unzip the pencil case','Open the red drawer']]))
sources=[OLD/n for n in ['rbm_tasks.parquet','rbm_data.parquet','rbm_episodes.parquet','rbm_tree.json','rbm_README.md','rbm_export_summary.json']]+[ROOT/'research/sources/native_gap_audit_20261003/robometer_v2.html',p]
save('source_hashes.json',[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sources])
print(json.dumps(dict(metadata_rows=len(rows),schema=list(rows[0]),pencil_case=[r for r in bindings if r['task']=='Unzip the pencil case']),ensure_ascii=False,indent=2))

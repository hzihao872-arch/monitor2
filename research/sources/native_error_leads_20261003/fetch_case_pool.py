"""Bounded download of all seven author-labelled pencil-case clips."""
from pathlib import Path
import json,hashlib,urllib.request,datetime,subprocess
import pyarrow.parquet as pq
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
REV='3f3ee69ecc0ee0db627684da7d599ec26d08175c'
def save(n,x):(OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf-8')
tree=json.loads((ROOT/'research/sources/replan_r1/rbm_tree.json').read_text('utf-8'))
rows=[x for x in pq.read_table(OUT/'train_metadata.parquet').to_pylist() if x['data_source']=='usc_trossen' and x['task']=='Unzip the pencil case']
assert len(rows)==7
manifest=json.loads((OUT/'fetch_manifest.json').read_text('utf-8'))
entries={r['file_name']:next(x for x in tree if x['path']=='train/'+r['file_name']) for r in rows}
prior_bytes=5402835;budget=6*1024*1024-prior_bytes
expected=57703+sum(x['size'] for x in entries.values());assert expected<=budget
save('media_scope.json',dict(rule='all seven records for task/source, before visual inspection; no author predictions seen',previous_batch_bytes=prior_bytes,existing_combined_budget=6*1024*1024,remaining_budget=budget,expected_batch_bytes=expected,metadata_only_scope_amendment='512KiB initial text-only cap expanded to existing 6MiB batch remainder after checking all seven exact file sizes; no overall budget increase',records=rows))
clips=[]
for r in rows:
 e=entries[r['file_name']];p=OUT/r['file_name'];url=f"https://huggingface.co/datasets/robometer/rbm-1m-ood/resolve/{REV}/{e['path']}"
 if not p.exists():
  with urllib.request.urlopen(urllib.request.Request(url,method='HEAD'),timeout=35) as h:head=h.headers.get('Content-Length')
  with urllib.request.urlopen(url,timeout=35) as res:b=res.read(e['size']+1)
  assert len(b)==e['size'] and hashlib.sha256(b).hexdigest()==e['lfs']['oid'];p.write_bytes(b)
  manifest.append(dict(url=url,revision=REV,path=p.relative_to(ROOT).as_posix(),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),lfs_verified=True,head_content_length=head,size_check='fixed tree bytes+LFS before GET',retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
  save('fetch_manifest.json',manifest)
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_frames,duration','-of','json',str(p)]))
 clips.append(dict(**r,path=p.relative_to(ROOT).as_posix(),probe=probe,author_prediction=None,export_episode_match='same numeric ordinal, task, source and normalized quality; identity not pixel-verified',original_time_unknown=True,holdout_eligible=False))
save('clip_registry.json',clips)
print(json.dumps(dict(files=len(manifest),bytes=sum(x['bytes'] for x in manifest),budget=budget,clips=clips),ensure_ascii=False))

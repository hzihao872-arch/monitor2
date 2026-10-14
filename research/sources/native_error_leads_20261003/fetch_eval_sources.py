from pathlib import Path
import json,hashlib,urllib.request,datetime
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
tree=json.loads((ROOT/'research/sources/replan_r1/rbm_code_tree.json').read_text('utf-8'))
names=['robometer/evals/eval_utils.py','robometer/evals/eval_metrics_utils.py','robometer/evals/compile_results.py','robometer/evals/README.md','robometer/data/samplers/eval/quality_preference.py']
entries=[x for x in tree['tree'] if x['path'] in names]
m=json.loads((OUT/'fetch_manifest.json').read_text('utf-8'))
assert 5402835+sum(x['bytes'] for x in m)+sum(x['size'] for x in entries if not (OUT/'code'/x['path']).exists())<=6*1024*1024
for e in entries:
 p=OUT/'code'/e['path'];url=f"https://raw.githubusercontent.com/robometer/robometer/{tree['sha']}/{e['path']}"
 if p.exists():continue
 with urllib.request.urlopen(urllib.request.Request(url,method='HEAD'),timeout=35) as h:head=h.headers.get('Content-Length')
 with urllib.request.urlopen(url,timeout=35) as res:b=res.read(e['size']+1)
 assert len(b)==e['size']
 blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();assert blob==e['sha']
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 m.append(dict(url=url,revision=tree['sha'],path=p.relative_to(ROOT).as_posix(),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),git_blob_verified=blob,size_check='fixed git tree before GET and HEAD',head_content_length=head,retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
 (OUT/'fetch_manifest.json').write_text(json.dumps(m,indent=2)+'\n','utf-8')
print('files',len(m),'bytes',sum(x['bytes'] for x in m))

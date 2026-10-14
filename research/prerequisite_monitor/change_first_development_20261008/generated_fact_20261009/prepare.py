import hashlib,json,pathlib,zipfile
from fact_runner import derive
H=pathlib.Path(__file__).resolve().parent;S=H.parent/'dense_discovery_20261009'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
req=[];sources={}
for f in sorted((S/'download/run/results').glob('*.json')):
 r=json.loads(f.read_text());sources[r['query_id']]=sha(f)
 if r['validation']['valid']:req.extend(x|{'source_sha256':sha(f)} for x in derive(r['query_id'],r['validation']['payload']))
assert len(sources)==8 and len(req)<=48
cfg={'parent':{'path':'/root/autodl-tmp/monitor2/fresh_prerequisite_runs/change_first_dense_discovery_20261009_v1/run/requests.jsonl','sha256':sha(S/'download/run/requests.jsonl')},'requests':req,'source_results':sources,'protocol':'all valid model-generated before/after clauses verbatim, no human selection or oracle; <=8 past full frames per target; as_of14 generated predicates, not prospective monitor at earlier target; no utility judgement'}
(H/'config.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8');(H/'freeze.json').write_text(json.dumps({'files':{n:sha(H/n) for n in ('config.json','fact_runner.py')}},indent=2),encoding='utf-8')
with zipfile.ZipFile(H/'fact_v1.zip','w') as z:
 for n in ('config.json','freeze.json','fact_runner.py','test_fact.py'):z.write(H/n,n)
t=(S/'remote_ops.py').read_text().replace('change_first_dense_discovery_20261009_v1','change_first_generated_fact_20261009_v1').replace('dense_v1.zip','fact_v1.zip').replace('test_dense.py','test_fact.py').replace('dense_runner.py','fact_runner.py').replace('dense_FINAL.tar.gz','fact_FINAL.tar.gz');(H/'remote_ops.py').write_text(t,encoding='utf-8')
t=(S/'seal_remote.py').read_text().replace('dense_runner.py','fact_runner.py').replace('dense_FINAL.tar.gz','fact_FINAL.tar.gz');(H/'seal_remote.py').write_text(t,encoding='utf-8');print(json.dumps({'requests':len(req),'zip_sha256':sha(H/'fact_v1.zip')}))

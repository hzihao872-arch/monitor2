import hashlib,json,pathlib,zipfile
H=pathlib.Path(__file__).resolve().parent;S=H.parent/'prefix_sampling_20261009';B=H.parent/'runs/diagnostic_20261009_window/delivery/window_v9/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
req=[]
for f in sorted(B.glob('compact2_predicted_*.json')):
 r=json.loads(f.read_text());req.append({'query_id':r['query_id'],'prompt_base':r['v1']['request']['prompt'].split('\nEVIDENCE_TIME_MS:')[0],'baseline_sha256':sha(f)})
assert len(req)==8
(H/'contracts.py').write_bytes((H.parent/'diagnostic_20261009_v9/contracts.py').read_bytes());cfg={'parent':{'path':'/root/autodl-tmp/monitor2/fresh_prerequisite_runs/change_first_prefix_sampling_20261009_v1/run/requests.jsonl','sha256':sha(S/'download/run/requests.jsonl')},'requests':req,'comparison':'unchanged compact2 prompt and output contract, replace automatic 8-frame+4-crop policy by all15 legal full frames; unequal pixel budget and natural cost'}
(H/'config.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8');(H/'freeze.json').write_text(json.dumps({'files':{n:sha(H/n) for n in ('config.json','dense_runner.py','contracts.py')}},indent=2),encoding='utf-8')
with zipfile.ZipFile(H/'dense_v1.zip','w') as z:
 for n in ('config.json','freeze.json','dense_runner.py','contracts.py','test_dense.py'):z.write(H/n,n)
t=(S/'remote_ops.py').read_text().replace('change_first_prefix_sampling_20261009_v1','change_first_dense_discovery_20261009_v1').replace('sampling_v1.zip','dense_v1.zip').replace('test_sampling.py','test_dense.py').replace('sampling_runner.py','dense_runner.py').replace('sampling_FINAL.tar.gz','dense_FINAL.tar.gz');(H/'remote_ops.py').write_text(t,encoding='utf-8')
t=(S/'seal_remote.py').read_text().replace('sampling_runner.py','dense_runner.py').replace('sampling_FINAL.tar.gz','dense_FINAL.tar.gz');(H/'seal_remote.py').write_text(t,encoding='utf-8');print(json.dumps({'requests':len(req),'zip_sha256':sha(H/'dense_v1.zip')}))

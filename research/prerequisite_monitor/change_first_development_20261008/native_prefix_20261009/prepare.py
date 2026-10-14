import hashlib,json,pathlib,zipfile
H=pathlib.Path(__file__).resolve().parent;S=H.parent/'joint_choice_20261009'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
items=[r for r in json.loads((S/'config.json').read_text())['requests'] if r['kind']=='rgb' and r['ref']=='f0014'];req=[]
for r in items:
 for rep in ('images','video'):req.append({k:r[k] for k in ('query_id','probe_id','positive','opposed','order','split')}|{'representation':rep,'id':r['probe_id']+'_'+rep+'_'+r['order']})
cfg={'parent':{'path':'/root/autodl-tmp/monitor2/fresh_prerequisite_runs/change_first_joint_choice_20261009_v1/run/requests.jsonl','sha256':sha(S/'download/run/requests.jsonl')},'requests':req,'status':'representation comparison; token budgets unequal; no goal status or automatic monitor claim'}
(H/'config.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8');(H/'freeze.json').write_text(json.dumps({'files':{n:sha(H/n) for n in ('config.json','native_runner.py')}},indent=2),encoding='utf-8')
(H/'private_eval').mkdir(exist_ok=True);(H/'private_eval/labels.json').write_bytes((S/'private_eval/labels.json').read_bytes())
with zipfile.ZipFile(H/'native_v1.zip','w') as z:
 for n in ('config.json','freeze.json','native_runner.py','test_native.py'):z.write(H/n,n)
t=(S/'remote_ops.py').read_text().replace('change_first_joint_choice_20261009_v1','change_first_native_prefix_20261009_v1').replace('choice_v1.zip','native_v1.zip').replace('test_choice.py','test_native.py').replace('choice_runner.py','native_runner.py').replace('choice_FINAL.tar.gz','native_FINAL.tar.gz').replace("['deploy','run','status','collect','seal','get']","['deploy','processor','run','status','collect','seal','get']").replace("elif a.op=='run':","elif a.op in ('run','processor'):").replace("r=cmd(c,f'nohup {command}","command+= ' --processor-only' if a.op=='processor' else ''\n            r=cmd(c,f'nohup {command}")
(H/'remote_ops.py').write_text(t,encoding='utf-8')
t=(S/'seal_remote.py').read_text().replace('choice_runner.py','native_runner.py').replace('choice_FINAL.tar.gz','native_FINAL.tar.gz');(H/'seal_remote.py').write_text(t,encoding='utf-8')
print(json.dumps({'requests':len(req),'zip_sha256':sha(H/'native_v1.zip')}))

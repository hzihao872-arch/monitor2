import hashlib,json,pathlib,zipfile
H=pathlib.Path(__file__).resolve().parent;S=H.parent/'atomic_contrast_20261009'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
t=(S/'contrast_runner.py').read_text(encoding='utf-8')
t=t.replace('contrast_runner.py','prior_runner.py').replace("'atomic_contrast_v1'","'prior_control_v1'").replace('parent_count!=80','parent_count!=188').replace('}),48)','}),16)').replace('>48','>16')
t=t.replace("H.parent/'atomic_state_20261009/remote_verified/run/requests.jsonl']","H.parent/'atomic_state_20261009/remote_verified/run/requests.jsonl',H.parent/'atomic_contrast_20261009/download/run/requests.jsonl',H.parent/'joint_choice_20261009/download/run/requests.jsonl',H.parent/'native_prefix_20261009/download/run/requests.jsonl']")
t=t.replace("planned=config['requests'];planned=[r for r in planned if r['input_kind']==('rgb' if a.block=='rgb' else 'oracle')]","planned=config['requests']")
t=t.replace("'extra_ai_fact_control'","'prior_only_ablation_control'")
(H/'prior_runner.py').write_text(t,encoding='utf-8')
c=json.loads((S/'config.json').read_text());req=[r.copy() for r in c['requests'] if r['input_kind']=='rgb' and r['template']=='chat']
for r in req:r['input_kind']='prior';r['id']=r['id'].replace('_rgb_','_prior_')
parents=c['parents']
for local,remote in [('atomic_contrast_20261009','change_first_contrast_20261009_v1'),('joint_choice_20261009','change_first_joint_choice_20261009_v1'),('native_prefix_20261009','change_first_native_prefix_20261009_v1')]:parents.append({'path':f'/root/autodl-tmp/monitor2/fresh_prerequisite_runs/{remote}/run/requests.jsonl','sha256':sha(H.parent/local/'download/run/requests.jsonl')})
(H/'config.json').write_text(json.dumps({'parents':parents,'requests':req,'control':'zero pixels, zero oracle facts, identical statement prompts; tests language priors, never primary score'},indent=2),encoding='utf-8')
(H/'freeze.json').write_text(json.dumps({'files':{n:sha(H/n) for n in ('prior_runner.py','config.json')},'derived_from_sha256':sha(S/'contrast_runner.py')},indent=2),encoding='utf-8')
t=(S/'test_contrast.py').read_text().replace('contrast_runner','prior_runner');(H/'test_prior.py').write_text(t,encoding='utf-8')
with zipfile.ZipFile(H/'prior_v1.zip','w') as z:
 for n in ('prior_runner.py','config.json','freeze.json','test_prior.py'):z.write(H/n,n)
t=(S/'remote_ops.py').read_text().replace('change_first_contrast_20261009_v1','change_first_prior_control_20261009_v1').replace('contrast_v1.zip','prior_v1.zip').replace('test_contrast.py','test_prior.py').replace('contrast_runner.py','prior_runner.py').replace('contrast_FINAL.tar.gz','prior_FINAL.tar.gz').replace("['deploy','rgb','oracle','status','collect','seal','get']","['deploy','run','status','collect','seal','get']").replace("elif a.op in ('rgb','oracle'):","elif a.op=='run':").replace(' --block {a.op}','').replace('{R}/rgb.log','{R}/run.log');(H/'remote_ops.py').write_text(t,encoding='utf-8')
t=(S/'seal_remote.py').read_text().replace('contrast_runner.py','prior_runner.py').replace('contrast_FINAL.tar.gz','prior_FINAL.tar.gz');(H/'seal_remote.py').write_text(t,encoding='utf-8')
print(json.dumps({'requests':len(req),'zip_sha256':sha(H/'prior_v1.zip')}))

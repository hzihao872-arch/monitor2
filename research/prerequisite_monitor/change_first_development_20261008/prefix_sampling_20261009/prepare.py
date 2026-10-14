import hashlib,json,pathlib,zipfile
H=pathlib.Path(__file__).resolve().parent;S=H.parent/'native_prefix_20261009'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
t=(S/'native_runner.py').read_text().replace('native_runner.py','sampling_runner.py').replace("H.parent/'joint_choice_20261009/download/run/requests.jsonl'","H.parent/'prior_control_20261009/download/run/requests.jsonl'").replace(')!=36',')!=16').replace("'native_prefix_v1'","'prefix_sampling_v1'").replace("'parent_issued':164","'parent_issued':204").replace("'parent':164,'total':164+","'parent':204,'total':204+")
t=t.replace('def video_times(n):',"def subset(ids,n):\n return [ids[round(i*(len(ids)-1)/(n-1))] for i in range(n)]\ndef video_times(n):")
t=t.replace("positive_first=item['order']=='positive_first'","ids=subset(ids,item['sample_count']);times=[pkg.handles[i]['time_ms'] for i in ids]\n   positive_first=item['order']=='positive_first'")
t=t.replace("'arm':item['representation']+'_'+item['order']","'arm':'n'+str(item['sample_count'])+'_'+item['order']").replace("'representation':item['representation'],'images':pixels","'sample_count':item['sample_count'],'representation':item['representation'],'images':pixels").replace("'probe_id':item['probe_id'],'representation':item['representation'],'order':item['order']","'probe_id':item['probe_id'],'sample_count':item['sample_count'],'representation':item['representation'],'order':item['order']")
(H/'sampling_runner.py').write_text(t,encoding='utf-8');items=[r for r in json.loads((S/'config.json').read_text())['requests'] if r['representation']=='images'];req=[]
for r in items:
 for n in (2,8):req.append(r.copy()|{'sample_count':n,'id':r['probe_id']+'_n'+str(n)+'_'+r['order']})
cfg={'parent':{'path':'/root/autodl-tmp/monitor2/fresh_prerequisite_runs/change_first_prior_control_20261009_v1/run/requests.jsonl','sha256':sha(H.parent/'prior_control_20261009/download/run/requests.jsonl')},'requests':req,'mechanism':'uniform legal full-frame prefix sampling, 2 vs 8 vs previously frozen 15; same exact query text; no private inputs'}
(H/'config.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8');(H/'freeze.json').write_text(json.dumps({'files':{n:sha(H/n) for n in ('config.json','sampling_runner.py')},'derived_from_sha256':sha(S/'native_runner.py')},indent=2),encoding='utf-8')
t=(S/'remote_ops.py').read_text().replace('change_first_native_prefix_20261009_v1','change_first_prefix_sampling_20261009_v1').replace('native_v1.zip','sampling_v1.zip').replace('test_native.py','test_sampling.py').replace('native_runner.py','sampling_runner.py').replace('native_FINAL.tar.gz','sampling_FINAL.tar.gz');(H/'remote_ops.py').write_text(t,encoding='utf-8')
t=(S/'seal_remote.py').read_text().replace('native_runner.py','sampling_runner.py').replace('native_FINAL.tar.gz','sampling_FINAL.tar.gz');(H/'seal_remote.py').write_text(t,encoding='utf-8')
(H/'private_eval').mkdir(exist_ok=True);(H/'private_eval/labels.json').write_bytes((S/'private_eval/labels.json').read_bytes())
with zipfile.ZipFile(H/'sampling_v1.zip','w') as z:
 for n in ('config.json','freeze.json','sampling_runner.py','test_sampling.py'):z.write(H/n,n)
print(json.dumps({'requests':len(req),'zip_sha256':sha(H/'sampling_v1.zip')}))

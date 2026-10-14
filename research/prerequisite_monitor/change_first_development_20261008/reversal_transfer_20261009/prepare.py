import hashlib,json,pathlib,zipfile
H=pathlib.Path(__file__).resolve().parent;S=H.parent/'native_prefix_20261009'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
t=(S/'native_runner.py').read_text().replace('native_runner.py','reversal_runner.py').replace("H.parent/'joint_choice_20261009/download/run/requests.jsonl'","H.parent/'generated_fact_20261009/download/run/requests.jsonl'").replace(')!=36',')!=47').replace("'native_prefix_v1'","'reversal_transfer_v1'").replace("'parent_issued':164","'parent_issued':283").replace("'parent':164,'total':164+","'parent':283,'total':283+")
t=t.replace('def video_times(n):',"def select(ids,mode):\n if mode=='current':return ids[-1:]\n if len(ids)<=8:return ids\n return [ids[round(i*(len(ids)-1)/7)] for i in range(8)]\ndef video_times(n):")
t=t.replace('target=14000;ids=causal_ids','target=item["time_ms"];ids=causal_ids').replace("if times!=list(range(0,15000,1000)):","if times!=list(range(0,target+1,1000)):")
t=t.replace("positive_first=item['order']=='positive_first'","ids=select(ids,item['mode']);times=[pkg.handles[i]['time_ms'] for i in ids]\n   positive_first=item['order']=='positive_first'")
t=t.replace('through 14.0 seconds. At TARGET 14.0 seconds','through {target/1000:.1f} seconds. At TARGET {target/1000:.1f} seconds').replace("'arm':item['representation']+'_'+item['order']","'arm':item['mode']+'_'+item['order']").replace("'representation':item['representation'],'images':pixels","'mode':item['mode'],'representation':item['representation'],'images':pixels").replace("'probe_id':item['probe_id'],'representation':item['representation'],'order':item['order']","'probe_id':item['probe_id'],'mode':item['mode'],'representation':item['representation'],'order':item['order']")
(H/'reversal_runner.py').write_text(t,encoding='utf-8')
orig=json.loads((H.parent/'joint_choice_20261009/config.json').read_text())['requests'];groups={'opening':'q07108c1875aa88b5','plate':'qbb0dbd57d63ce6a9'};req=[];labels={}
for group,qid in groups.items():
 src=next(r for r in orig if r['probe_id'].startswith(group+'_'))
 for sec in (0,7,14):
  pid=group+'_R_'+str(sec);labels[pid]={'reference':'True' if sec==7 else 'False','status':'AI full RGB development pre-audit; exposed reversal example, not blind'}
  for mode in ('current','prefix8'):
   for order in ('positive_first','opposed_first'):req.append({'id':pid+'_'+mode+'_'+order,'probe_id':pid,'query_id':qid,'time_ms':sec*1000,'positive':src['positive'],'opposed':src['opposed'],'mode':mode,'order':order,'representation':'images','split':'development_reversal_confirmation'})
cfg={'parent':{'path':'/root/autodl-tmp/monitor2/fresh_prerequisite_runs/change_first_generated_fact_20261009_v1/run/requests.jsonl','sha256':sha(H.parent/'generated_fact_20261009/download/run/requests.jsonl')},'requests':req,'protocol':'new exposed reversal development transfer, same state descriptions, current vs <=8 past full frames; selected times and predicates directed, no primary accuracy claim'}
(H/'config.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8');(H/'freeze.json').write_text(json.dumps({'files':{n:sha(H/n) for n in ('config.json','reversal_runner.py')},'derived_from_sha256':sha(S/'native_runner.py')},indent=2),encoding='utf-8');(H/'private_eval').mkdir(exist_ok=True);(H/'private_eval/labels.json').write_text(json.dumps(labels,indent=2),encoding='utf-8')
with zipfile.ZipFile(H/'reversal_v1.zip','w') as z:
 for n in ('config.json','freeze.json','reversal_runner.py','test_reversal.py'):z.write(H/n,n)
t=(S/'remote_ops.py').read_text().replace('change_first_native_prefix_20261009_v1','change_first_reversal_transfer_20261009_v1').replace('native_v1.zip','reversal_v1.zip').replace('test_native.py','test_reversal.py').replace('native_runner.py','reversal_runner.py').replace('native_FINAL.tar.gz','reversal_FINAL.tar.gz');(H/'remote_ops.py').write_text(t,encoding='utf-8');t=(S/'seal_remote.py').read_text().replace('native_runner.py','reversal_runner.py').replace('native_FINAL.tar.gz','reversal_FINAL.tar.gz');(H/'seal_remote.py').write_text(t,encoding='utf-8');print(json.dumps({'requests':len(req),'zip_sha256':sha(H/'reversal_v1.zip')}))

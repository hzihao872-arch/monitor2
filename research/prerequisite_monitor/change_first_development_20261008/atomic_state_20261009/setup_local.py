import datetime,hashlib,json,pathlib,zipfile
H=pathlib.Path(__file__).resolve().parent
def write(n,x): (H/n).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
probes=[];facts={};labels={}
groups=[
 ('opening','q613a0d8ddf5acc68',[0,14],'The rectangular top opening of the box is visibly uncovered.',
  ['The orange panel covers the rectangular top opening of the box.','The orange panel is behind the box opening. The rectangular hole is exposed.'],['False','True']),
 ('plate','q07e7773ad34d85f6',[0,14],'The yellow rectangular plate lies across the two green-marked rail sections.',
  ['The yellow rectangular plate is at the rear, spanning the green marked sections of both rails.','The yellow rectangular plate is at the front. The green marked rear sections of both rails are exposed.'],['True','False']),
 ('grasp','qf2bed1caaecc37a0',[7,14],'The blue cube is visibly held between the robot gripper fingers.',
  ['The blue cube is between the gripper fingers above the table, outside the box.','The blue cube is inside the box. The gripper is away from the cube, with empty separated fingers.'],['True','False']),
 ('inside','qf2bed1caaecc37a0',[7,14],'The blue cube is visibly inside the transparent box.',
  ['The blue cube is between the gripper fingers above the table, outside the box.','The blue cube is inside the transparent box, below the top rim and on the visible floor.'],['False','True'])]
for name,qid,times,statement,descriptions,answers in groups:
    for i,t in enumerate(times):
        pid=f'{name}_{t:02d}'
        probes.append({'id':pid,'query_id':qid,'ref':f'f{t:04d}','statement':statement})
        facts[pid]={'current':f'At {t*1000} ms: '+descriptions[i],
                    'timeline':f'At {times[0]*1000} ms: {descriptions[0]}\nAt {times[1]*1000} ms: {descriptions[1]}' if i else f'At {t*1000} ms: '+descriptions[i]}
        labels[pid]={'reference':answers[i],'reviewer':'Codex AI visual development pre-audit only; no independent human labels',
                     'pixel_sha256':sha(H/'source_core/model_input/pilot_v5'/qid/'frames'/f'{t:04d}.png')}
write('probes.json',{'scope':'exposed development directed atom diagnostics; no full monitor scores','probes':probes,
    'context_ids':['opening_14','plate_14','inside_14']})
write('oracle_text.json',facts); (H/'private_eval').mkdir(exist_ok=True);write('private_eval/labels.json',labels)
old=H.parent/'runs/diagnostic_20261009_window/delivery/window_v9/requests.jsonl'
stop=datetime.datetime(2026,10,9,14,39,56,tzinfo=datetime.timezone.utc).timestamp()
write('window.json',{'parent_ledger_sha256':sha(old),'parent_issued':50,'new_request_cap':30,'total_cap':80,'old_separate_requests':96,
    'model_stop_epoch':stop,'hard_deadline_epoch':stop+1200,'platform_expiry_verified':False,
    'extension_authorization':'User: 时间我延长了你不用担心时间，还有一个小时. Recorded UTC 2026-10-09 13:59:56.',
    'original_model_stop_epoch':1791556400,'original_hard_deadline_epoch':1791557600,
    'primary_requests':24,'conditional_context_requests':6,'primary_revisions':0})
write('freeze.json',{'series':'atomic_state_v1','files':{n:sha(H/n) for n in ('atomic_runner.py','probes.json','window.json','oracle_text.json')}})
with zipfile.ZipFile(H/'atomic_state_v1.zip','w',zipfile.ZIP_DEFLATED) as z:
    for n in ('atomic_runner.py','test_atomic.py','probes.json','window.json','oracle_text.json','freeze.json'): z.write(H/n,n)
print(json.dumps({'zip_sha256':sha(H/'atomic_state_v1.zip'),'probes':len(probes),'hard_end_beijing':'2026-10-09 23:59:56','model_stop_beijing':'23:39:56'}))

import hashlib,json,pathlib,sys,zipfile
H=pathlib.Path(__file__).resolve().parent;A=H.parent/'atomic_state_20261009';C=H.parent/'atomic_contrast_20261009'
sys.path.insert(0,str(C));from contrast_runner import opposition
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
probes=json.loads((A/'probes.json').read_text())['probes'];facts=json.loads((A/'oracle_text.json').read_text());labels=json.loads((A/'private_eval/labels.json').read_text())
new=[('confirm_o_00','q0d6f6ef3062d4d34',0,'opening','True','The box top rectangular opening is exposed. The orange panel is behind it.'),
 ('confirm_o_14','q0d6f6ef3062d4d34',14,'opening','False','The orange panel covers the top rectangular hole of the box.'),
 ('confirm_p_00','qcde827bb66b99fd4',0,'plate','False','The yellow plate is at the front. Both green-marked rear rail sections are exposed.'),
 ('confirm_p_14','qcde827bb66b99fd4',14,'plate','True','The yellow plate spans the green-marked rear rail sections.')]
for pid,qid,t,group,reference,fact in new:
 statement=next(p['statement'] for p in probes if p['id'].startswith(group+'_'))
 probes.append({'id':pid,'query_id':qid,'ref':f'f{t:04d}','statement':statement,'group':group});facts[pid]={'current':fact};labels[pid]={'reference':reference,'reviewer':'AI development pre-audit; development confirmation, not blind'}
requests=[]
for p in probes:
 group=p.get('group',p['id'].split('_')[0]);isnew=p['id'].startswith('confirm_')
 for kind in ('rgb','oracle'):
  if kind=='oracle' and not isnew and p['id'] not in ('opening_00','plate_14'):continue
  for order in ('positive_first','opposed_first'):
   requests.append({'id':p['id']+'_'+kind+'_'+order,'probe_id':p['id'],'query_id':p['query_id'],'ref':p['ref'],'positive':p['statement'],'opposed':opposition(group),
    'kind':kind,'order':order,'split':'development_confirmation' if isnew else 'development_seen',**({'fact':facts[p['id']]['current']} if kind=='oracle' else {})})
cfg={'parent':{'path':'/root/autodl-tmp/monitor2/fresh_prerequisite_runs/change_first_contrast_20261009_v1/run/requests.jsonl','sha256':sha(C/'download/run/requests.jsonl')},
 'requests':requests,'authorization':'User raised cap, continue while reachable; per-block seals. 36 bounded planned requests; prior 128 remain unchanged.',
 'hypothesis':'Joint selection reduces independently affirmative contradictory judgments; swapping A/B tests position bias. 4 new atoms are development confirmation.'}
(H/'config.json').write_text(json.dumps(cfg,indent=2));(H/'private_eval').mkdir(exist_ok=True);(H/'private_eval/labels.json').write_text(json.dumps(labels,indent=2))
(H/'freeze.json').write_text(json.dumps({'files':{n:sha(H/n) for n in ('choice_runner.py','config.json')}},indent=2))
with zipfile.ZipFile(H/'choice_v1.zip','w',zipfile.ZIP_DEFLATED) as z:
 for n in ('choice_runner.py','config.json','freeze.json','test_choice.py'):z.write(H/n,n)
print(json.dumps({'requests':len(requests),'zip_sha256':sha(H/'choice_v1.zip')}))

import hashlib,json,pathlib,zipfile
H=pathlib.Path(__file__).resolve().parent;A=H.parent/'atomic_state_20261009'
from contrast_runner import opposition
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
spec=json.loads((A/'probes.json').read_text());facts=json.loads((A/'oracle_text.json').read_text());requests=[]
for p in spec['probes']:
    for kind in ('rgb','oracle'):
        if kind=='oracle' and p['id'] not in ('opening_00','plate_14','grasp_07','inside_14'):continue
        for template in ('chat','raw'):
            for polarity in ('positive','opposed'):
                requests.append({'id':p['id']+'_'+kind+'_'+template+'_'+polarity,'probe_id':p['id'],'query_id':p['query_id'],'ref':p['ref'],
                    'statement':p['statement'] if polarity=='positive' else opposition(p['id'].split('_')[0]),'template':template,'polarity':polarity,'input_kind':kind,
                    **({'fact':facts[p['id']]['current']} if kind=='oracle' else {})})
parents=[{'path':'/root/autodl-tmp/monitor2/fresh_prerequisite_runs/change_first_diag_20261009_v9/runs/window_v9/requests.jsonl',
    'sha256':sha(A.parent/'runs/diagnostic_20261009_window/delivery/window_v9/requests.jsonl')},
    {'path':'/root/autodl-tmp/monitor2/fresh_prerequisite_runs/change_first_atomic_20261009_v1/run/requests.jsonl','sha256':sha(A/'remote_verified/run/requests.jsonl')}]
cfg={'parents':parents,'requests':requests,'authorization':'2026-10-09 user raised call cap and requested ongoing work while server is reachable. Prior frozen 80 ledger remains unchanged.',
    'stop_rule':'Stop on connection loss, GPU occupation, backend failure; seal/download each complete block. No new global fixed request cap inferred from prior 80.',
    'block_cap':48,'notes':'48 planned requests, not a new user-imposed global cap. Visual-first layout shared across chat/raw arms; 2 mutually opposed positive state statements. No timeline min-max.'}
(H/'config.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
freeze={'files':{n:sha(H/n) for n in ('contrast_runner.py','config.json')}};(H/'freeze.json').write_text(json.dumps(freeze,indent=2))
with zipfile.ZipFile(H/'contrast_v1.zip','w',zipfile.ZIP_DEFLATED) as z:
    for n in ('contrast_runner.py','test_contrast.py','config.json','freeze.json'):z.write(H/n,n)
print(json.dumps({'requests':len(requests),'zip_sha256':sha(H/'contrast_v1.zip')}))

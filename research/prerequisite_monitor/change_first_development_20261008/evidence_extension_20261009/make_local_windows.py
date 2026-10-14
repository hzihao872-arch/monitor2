import hashlib,json,pathlib,zipfile
H=pathlib.Path(__file__).resolve().parent;B=H.parent;S=B/'dense_discovery_20261009';D=B/'local_windows_20261009';D.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cfg=json.loads((S/'config.json').read_text());requests=[]
for old in cfg['requests']:
 for start in range(0,14,2):
  requests.append(dict(old,id=old['query_id']+f'_{start:02}_{start+2:02}',frame_ids=[f'f{t:04}' for t in range(start,start+3)],as_of_ms=(start+2)*1000))
cfg={'parent':{'path':'/root/autodl-tmp/monitor2/fresh_prerequisite_runs/change_first_inventory_binding_20261009_v1/run/requests.jsonl','sha256':sha(B/'inventory_binding_20261009/download/run/requests.jsonl')},'requests':requests,'protocol':'Same goal-blind dense discovery prompt, deterministic seven overlapping 2-second windows per query; all 15 distinct fullframes, no hand-picked changes/objects/regions/labels. Independent run, 56 calls. Retrospective development package validation, not end-to-end online validation.'}
(D/'config.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8');(D/'contracts.py').write_bytes((S/'contracts.py').read_bytes())
t=(S/'dense_runner.py').read_text().replace('dense_runner.py','window_runner.py').replace("'prefix_sampling_20261009/download/run/requests.jsonl'","'inventory_binding_20261009/download/run/requests.jsonl'").replace("!=24:raise RuntimeError('parent changed')","!=15:raise RuntimeError('parent changed')").replace("'dense_discovery_v1'","'local_windows_v1'").replace('}),8)','}),56)').replace('item["query_id"]}.json','item["id"]}.json')
t=t.replace("frames=[f for f in pkg.manifest['frames'] if f['time_ms']<=14000];ids=[f['evidence_id'] for f in frames]","ids=item['frame_ids']").replace("len(ids)!=15","len(ids)!=3").replace("'arm':'dense_full15'","'arm':'local_window3'").replace("'as_of_ms':14000","'as_of_ms':item['as_of_ms']").replace("'parent_issued':228","'parent_issued':483").replace("'parent':228,'total':228+ledger.issued_count","'parent':483,'total':483+ledger.issued_count")
(D/'window_runner.py').write_text(t,encoding='utf-8')
(D/'test_windows.py').write_text("import json,pathlib\nc=json.loads((pathlib.Path(__file__).parent/'config.json').read_text())\nassert len(c['requests'])==56\nfor q in {r['query_id'] for r in c['requests']}:\n r=[r for r in c['requests'] if r['query_id']==q];assert len(r)==7;assert {i for x in r for i in x['frame_ids']}=={f'f{n:04}' for n in range(15)}\n for x in r:assert len(x['frame_ids'])==3 and max(int(i[1:])*1000 for i in x['frame_ids'])==x['as_of_ms']\nprint('window coverage and time checks passed')\n",encoding='utf-8')
(D/'freeze.json').write_text(json.dumps({'files':{n:sha(D/n) for n in ('config.json','window_runner.py','contracts.py')}},indent=2),encoding='utf-8')
with zipfile.ZipFile(D/'window_v1.zip','w') as z:
 for n in ('config.json','freeze.json','window_runner.py','contracts.py','test_windows.py'):z.write(D/n,n)
t=(B/'inventory_binding_20261009/remote_ops.py').read_text().replace('change_first_inventory_binding_20261009_v1','change_first_local_windows_20261009_v1').replace('inventory_v1.zip','window_v1.zip').replace('inventory_runner.py','window_runner.py').replace('test_inventory.py','test_windows.py').replace('inventory_FINAL.tar.gz','window_FINAL.tar.gz');(D/'remote_ops.py').write_text(t,encoding='utf-8')
t=(B/'inventory_binding_20261009/seal_remote.py').read_text().replace('inventory_runner.py','window_runner.py').replace('inventory_FINAL.tar.gz','window_FINAL.tar.gz');(D/'seal_remote.py').write_text(t,encoding='utf-8');print(sha(D/'window_v1.zip'))

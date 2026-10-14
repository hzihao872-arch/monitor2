import pathlib,json,hashlib,zipfile
H=pathlib.Path(__file__).resolve().parent;B=H.parent;S=B/'generated_fact_20261009';D=B/'cross_fact_20261009';D.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cfg=json.loads((S/'config.json').read_text());groups={}
for r in cfg['requests']:groups.setdefault((r['query_id'],r['change']),{})[r['side']]=r
requests=[]
for pair in groups.values():
 for side,r in pair.items():requests.append(dict(r,id=r['id']+'_cross',ref=pair['after' if side=='before' else 'before']['ref']))
cfg={'parent':{'path':'/root/autodl-tmp/monitor2/fresh_prerequisite_runs/change_first_native_discovery_20261009_v1/run/requests.jsonl','sha256':sha(B/'native_discovery_20261009/remote_verified/run/requests.jsonl')},'requests':requests,'protocol':'Generated dense predicates copied verbatim, same fact prompt/backend/causal8 prefix; swap target to opposite transition endpoint. Source predicates generated at14, retrospective as_of14, no manually correct condition or oracle. Combine old own-endpoint outputs with new crossed-endpoint outputs, inspect within-statement temporal True logp delta; not calibrated success. Layout8 separately counted, cumulative prior555.'}
(D/'config.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
t=(S/'fact_runner.py').read_text().replace('fact_runner.py','cross_runner.py').replace("'dense_discovery_20261009/download/run/requests.jsonl'","'native_discovery_20261009/remote_verified/run/requests.jsonl'").replace("'generated_fact_v1'","'cross_fact_v1'").replace("'parent_issued':236","'parent_issued':555").replace("'parent':236,'total':236+ledger.issued_count","'parent':555,'total':555+ledger.issued_count")
(D/'cross_runner.py').write_text(t,encoding='utf-8');(D/'test_cross.py').write_text("import json,pathlib\nh=pathlib.Path(__file__).parent;c=json.loads((h/'config.json').read_text());old=json.loads((h.parent/'generated_fact_20261009/config.json').read_text())['requests'];a={r['id']:r for r in old}\nassert len(c['requests'])==48\nfor r in c['requests']:\n o=a[r['id'].removesuffix('_cross')];assert r['condition']==o['condition'] and r['object']==o['object'];other=a[o['id'].rsplit('_',1)[0]+'_'+('after' if o['side']=='before' else 'before')];assert r['ref']==other['ref']\nprint('all 48 predicates unchanged and targets crossed passed')\n",encoding='utf-8')
(D/'freeze.json').write_text(json.dumps({'files':{n:sha(D/n) for n in ('config.json','cross_runner.py')}},indent=2),encoding='utf-8')
with zipfile.ZipFile(D/'cross_v1.zip','w') as z:
 for n in ('config.json','freeze.json','cross_runner.py','test_cross.py'):z.write(D/n,n)
t=(B/'inventory_binding_20261009/remote_ops.py').read_text().replace('change_first_inventory_binding_20261009_v1','change_first_cross_fact_20261009_v1').replace('inventory_v1.zip','cross_v1.zip').replace('inventory_runner.py','cross_runner.py').replace('test_inventory.py','test_cross.py').replace('inventory_FINAL.tar.gz','cross_FINAL.tar.gz')
# The preparation-only test compares a local parent config; upload its immutable reference for the remote test.
(D/'own_endpoint_config.json').write_bytes((S/'config.json').read_bytes());test=(D/'test_cross.py').read_text().replace("h.parent/'generated_fact_20261009/config.json'","h/'own_endpoint_config.json'");(D/'test_cross.py').write_text(test,encoding='utf-8')
with zipfile.ZipFile(D/'cross_v1.zip','a') as z:z.write(D/'own_endpoint_config.json','own_endpoint_config.json')
# Replace the zipped test after its local-reference adaptation without duplicate members.
with zipfile.ZipFile(D/'cross_v1.zip','w') as z:
 for n in ('config.json','freeze.json','cross_runner.py','test_cross.py','own_endpoint_config.json'):z.write(D/n,n)
(D/'remote_ops.py').write_text(t,encoding='utf-8');t=(B/'inventory_binding_20261009/seal_remote.py').read_text().replace('inventory_runner.py','cross_runner.py').replace('inventory_FINAL.tar.gz','cross_FINAL.tar.gz');(D/'seal_remote.py').write_text(t,encoding='utf-8');print(sha(D/'cross_v1.zip'))

"""Seal only this diagnostic run after all owned compute has stopped."""
import hashlib,json,pathlib,shutil,subprocess,sys,time
root=pathlib.Path('/root/autodl-tmp/monitor2/fresh_prerequisite_runs/change_first_diag_20261009_v9')
run=root/'runs/window_v9'; prov=run/'provenance'
ps=subprocess.check_output(['ps','-eo','pid,args'],text=True)
owned=[s for s in ps.splitlines() if any(x in s for x in ('diagnostic_runner.py','legacy_oracle_probe.py','relation_text_probe.py','order_probe.py')) and ('python' in s or 'timeout' in s)]
gpu=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,used_memory','--format=csv,noheader'],text=True)
if owned or gpu.strip():raise RuntimeError('compute is not idle; refuse final seal')
prov.mkdir(exist_ok=True)
for name in ('code','code_v10'):
    shutil.copytree(root/name,prov/name,ignore=shutil.ignore_patterns('__pycache__'),dirs_exist_ok=True)
for p in root.iterdir():
    if p.is_file() and (p.suffix in ('.log','.json','.zip') or p.name.endswith('.pid')):
        shutil.copy2(p,prov/p.name)
rows=[json.loads(s) for s in (run/'requests.jsonl').read_text().splitlines()]
counts={k:sum(r['kind']==k for r in rows) for k in ('issued','completed','failed')}
issued={r['request_id'] for r in rows if r['kind']=='issued'}
resolved={r['request_id'] for r in rows if r['kind'] in ('completed','failed')}
if issued-resolved:raise RuntimeError('unresolved requests')
status={'time_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'epoch':time.time(),'ledger':counts,'ambiguous':len(issued-resolved),'owned_processes':owned,'gpu_compute':gpu.strip(),'new_request_stop':'50 requests; frozen diagnostics exhausted; no further model calls','platform_expiry':'unavailable; user accepted conservative absolute cutoff'}
(prov/'FINAL_IDLE_STATUS.json').write_text(json.dumps(status,indent=2))
sys.path.insert(0,'/root/autodl-tmp/monitor2/fresh_prerequisite_runs/change_first_s1_20261009/bundle_v8_clean/research/prerequisite_monitor/change_first_development_20261008')
from collect_and_seal import seal
archive=root/'runs/window_v9_FINAL_20261009.tar.gz'
print(json.dumps({'status':status,'seal':seal(run,archive)},indent=2))

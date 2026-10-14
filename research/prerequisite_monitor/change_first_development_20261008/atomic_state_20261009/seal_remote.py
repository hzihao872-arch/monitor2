"""Read-only core/parent audit and per-member sealing after the bounded runner exits."""
import datetime,hashlib,json,pathlib,subprocess,tarfile
H=pathlib.Path(__file__).resolve().parent
CORE=pathlib.Path('/root/autodl-tmp/monitor2/fresh_prerequisite_runs/change_first_s1_20261009/bundle_v8_clean')
MODEL=pathlib.Path('/root/autodl-tmp/hf/hub/models--Qwen--Qwen3-VL-8B-Instruct/snapshots/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b')
PARENT=pathlib.Path('/root/autodl-tmp/monitor2/fresh_prerequisite_runs/change_first_diag_20261009_v9/runs/window_v9/requests.jsonl')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cmd(xs):return subprocess.check_output(xs,text=True).strip()
if (H/'run/.run.lock').exists():raise RuntimeError('runner lock exists; do not seal while active')
procs=cmd(['ps','-eo','pid,args']).splitlines()
active=[p for p in procs if str(H/'atomic_runner.py') in p]
if active:raise RuntimeError('atomic runner is still active')
ledger=[json.loads(s) for s in (H/'run/requests.jsonl').read_text().splitlines() if s.strip()]
parent=[json.loads(s) for s in PARENT.read_text().splitlines() if s.strip()]
issued={r['request_id'] for r in ledger if r['kind']=='issued'};done={r['request_id'] for r in ledger if r['kind'] in ('completed','failed')}
status={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'atomic_processes':active,
    'gpu_compute_apps':cmd(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv']),
    'gpu':cmd(['nvidia-smi','--query-gpu=name,memory.total,memory.used,utilization.gpu','--format=csv']),
    'parent_sha256':sha(PARENT),'parent_issued':sum(r['kind']=='issued' for r in parent),
    'new_issued':len(issued),'new_terminal':len(done),'ambiguous':len(issued-done),
    'model_small_file_hashes':{p.name:sha(p) for p in MODEL.glob('*') if p.is_file() and p.stat().st_size<20_000_000},
    'model_shards':{p.name:p.stat().st_size for p in MODEL.glob('*.safetensors')},
    'core_hashes':{str(p.relative_to(CORE)):sha(p) for p in (CORE/'experiments/prerequisite_probe/change_first_monitor').rglob('*') if p.is_file() and '__pycache__' not in p.parts}}
(H/'FINAL_REMOTE_STATUS.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
files=[p for p in H.rglob('*') if p.is_file() and p.name not in ('atomic_state_FINAL.tar.gz','remote_seal.json','seal.json') and '__pycache__' not in p.parts]
members={str(p.relative_to(H)):sha(p) for p in files}
(H/'seal.json').write_text(json.dumps({'members':members,'scope':'bounded atomic diagnostics only; no session credentials or private evaluation labels'},indent=2),encoding='utf-8')
archive=H/'atomic_state_FINAL.tar.gz'
with tarfile.open(archive,'w:gz') as t:
    for p in files+[H/'seal.json']:t.add(p,arcname=str(p.relative_to(H)))
seal={'sha256':sha(archive),'files':len(members),'utc':status['utc'],'new_issued':len(issued)}
(H/'remote_seal.json').write_text(json.dumps(seal,indent=2),encoding='utf-8')
print(json.dumps(seal));print(json.dumps({'gpu_compute_apps':status['gpu_compute_apps'],'atomic_processes':active}))

import datetime,hashlib,json,pathlib,subprocess,tarfile
H=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if (H/'run/.run.lock').exists():raise RuntimeError('runner active')
active=[p for p in subprocess.check_output(['ps','-eo','pid,args'],text=True).splitlines() if str(H/'precision_runner.py') in p]
if active:raise RuntimeError('runner process active')
config=json.loads((H/'config.json').read_text());status={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'active':active,
 'gpu_compute_apps':subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv'],text=True),
 'parents':[{**p,'actual_sha256':sha(pathlib.Path(p['path']))} for p in config['parents']]}
(H/'FINAL_REMOTE_STATUS.json').write_text(json.dumps(status,indent=2))
files=[p for p in H.rglob('*') if p.is_file() and p.name not in ('precision_FINAL.tar.gz','remote_seal.json','seal.json') and '__pycache__' not in p.parts]
members={str(p.relative_to(H)):sha(p) for p in files};(H/'seal.json').write_text(json.dumps({'members':members},indent=2))
with tarfile.open(H/'precision_FINAL.tar.gz','w:gz') as t:
 for p in files+[H/'seal.json']:t.add(p,arcname=str(p.relative_to(H)))
seal={'sha256':sha(H/'precision_FINAL.tar.gz'),'files':len(members),'utc':status['utc']};(H/'remote_seal.json').write_text(json.dumps(seal,indent=2));print(json.dumps(seal))

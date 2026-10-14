import argparse,hashlib,json,os,pathlib,subprocess,sys
H=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(p,x):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True),encoding='utf-8');os.replace(tmp,p)
def run(a):
 sys.path.insert(0,a.core)
 from experiments.prerequisite_probe.change_first_monitor.qwen_backend import QwenBackend
 from experiments.prerequisite_probe.change_first_monitor.prefix import PrefixPackage
 from experiments.prerequisite_probe.change_first_monitor.runner import RequestLedger,hash_obj
 from contracts import validate
 cfg=json.loads((H/'config.json').read_text());freeze=json.loads((H/'freeze.json').read_text())
 if freeze['files']!={n:sha(H/n) for n in ('config.json','dense_runner.py','contracts.py')}:raise RuntimeError('freeze changed')
 parent=H.parent/'prefix_sampling_20261009/download/run/requests.jsonl' if a.mock else pathlib.Path(cfg['parent']['path'])
 if sha(parent)!=cfg['parent']['sha256'] or sum(json.loads(s)['kind']=='issued' for s in parent.read_text().splitlines())!=24:raise RuntimeError('parent changed')
 root=pathlib.Path(a.output);root.mkdir(parents=True,exist_ok=True);lock=root/'.run.lock';os.close(os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY))
 try:
  class Backend(QwenBackend):
   def generate(self,req):
    if a.mock:
     self.last_metrics={'elapsed_seconds':0,'input_tokens':0,'output_tokens':0,'peak_vram_bytes':0,'hit_output_cap':False};return json.dumps({'context':'mock','changes':[],'coverage':'no_observable_change'})
    return super().generate(req)
  backend=Backend(a.model or 'mock');ledger=RequestLedger(root,hash_obj({'series':'dense_discovery_v1','freeze':freeze,'mock':a.mock,'model':backend.identity}),8)
  if not a.mock and subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():raise RuntimeError('GPU occupied')
  for item in cfg['requests']:
   dst=root/'results'/f'{item["query_id"]}.json'
   if dst.exists():continue
   pkg=PrefixPackage(pathlib.Path(a.input)/item['query_id']);frames=[f for f in pkg.manifest['frames'] if f['time_ms']<=14000];ids=[f['evidence_id'] for f in frames];handles={i:pkg.handles[i] for i in ids}
   if len(ids)!=15 or any(i.startswith('c') for i in ids):raise RuntimeError('full frame contract')
   pixels=[pkg.read(i,'V1') for i in ids];times={i:pkg.handles[i]['time_ms'] for i in ids};prompt=item['prompt_base']+'\nEVIDENCE_TIME_MS: '+json.dumps(times,sort_keys=True,separators=(',',':'))
   req={'query_id':item['query_id'],'stage':'V1','arm':'dense_full15','prompt':prompt,'images':pixels,'image_ids':ids,'image_hashes':[hashlib.sha256(b).hexdigest() for b in pixels],'image_meta':[{'time_ms':times[i]} for i in ids],'limits':[5000,768],'as_of_ms':14000,'input_type':'legal_rgb_goal_blind_automatic_discovery','parent_issued':228,'baseline_source_sha256':item['baseline_sha256']}
   raw=ledger.invoke(req,backend.generate);validation=validate('V1',raw,handles);save(dst,{'query_id':item['query_id'],'raw':raw,'validation':validation,'request':{k:v for k,v in req.items() if k!='images'},'baseline_sha256':item['baseline_sha256']});save(root/'progress.json',{'issued':ledger.issued_count,'parent':228,'total':228+ledger.issued_count,'last':item['query_id']});print(json.dumps({'query':item['query_id'],'valid':validation['valid'],'issued':ledger.issued_count}),flush=True)
 finally:lock.unlink(missing_ok=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--core',required=True);p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--model');p.add_argument('--mock',action='store_true');run(p.parse_args())

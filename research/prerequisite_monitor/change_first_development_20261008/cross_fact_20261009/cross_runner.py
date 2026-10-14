import argparse,hashlib,json,os,pathlib,subprocess,sys,time
H=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def derive(qid,payload):
 out=[]
 for j,c in enumerate(payload['changes']):
  for side,key in [('before','b'),('after','a')]:out.append({'id':f'{qid}_{j}_{side}','query_id':qid,'change':j,'side':side,'ref':c[key],'object':c['object'],'condition':c[side]})
 return out
def save(p,x):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True),encoding='utf-8');os.replace(tmp,p)
def subset(ids,n=8):
 if len(ids)<=n:return ids
 return [ids[round(i*(len(ids)-1)/(n-1))] for i in range(n)]
def run(a):
 sys.path.insert(0,a.core)
 from experiments.prerequisite_probe.change_first_monitor.qwen_backend import QwenBackend,prepare_content
 from experiments.prerequisite_probe.change_first_monitor.prefix import PrefixPackage
 from experiments.prerequisite_probe.change_first_monitor.runner import RequestLedger,hash_obj
 cfg=json.loads((H/'config.json').read_text());freeze=json.loads((H/'freeze.json').read_text())
 if freeze['files']!={n:sha(H/n) for n in ('config.json','cross_runner.py')}:raise RuntimeError('freeze changed')
 parent=H.parent/'native_discovery_20261009/remote_verified/run/requests.jsonl' if a.mock else pathlib.Path(cfg['parent']['path'])
 if sha(parent)!=cfg['parent']['sha256'] or sum(json.loads(s)['kind']=='issued' for s in parent.read_text().splitlines())!=8:raise RuntimeError('parent changed')
 root=pathlib.Path(a.output);root.mkdir(parents=True,exist_ok=True);lock=root/'.run.lock';os.close(os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY))
 try:
  class Backend(QwenBackend):
   def generate(self,req):
    if a.mock:
     self.last_metrics={'elapsed_seconds':0,'input_tokens':0,'output_tokens':0,'peak_vram_bytes':0,'hit_output_cap':False};return json.dumps({'value':'Unknown'})
    self._load();import torch
    t=time.perf_counter();content=prepare_content(req);content=content[1:]+content[:1];inputs=self.processor.apply_chat_template([{'role':'user','content':content}],tokenize=True,add_generation_prompt=True,return_dict=True,return_tensors='pt');n=int(inputs['input_ids'].shape[-1]);values=['True','False','Unknown'];ids={s:self.processor.tokenizer.encode(s,add_special_tokens=False) for s in values}
    if n>5000 or any(len(i)!=1 for i in ids.values()):raise RuntimeError('token contract')
    torch.cuda.reset_peak_memory_stats()
    with torch.inference_mode():
     output=self.model(**inputs.to('cuda'),logits_to_keep=1);lp=torch.log_softmax(output.logits[0,-1].float(),dim=-1);probs={s:float(lp[i[0]]) for s,i in ids.items()}
    torch.cuda.synchronize();self.last_metrics={'elapsed_seconds':time.perf_counter()-t,'input_tokens':n,'output_tokens':0,'peak_vram_bytes':int(torch.cuda.max_memory_allocated()),'hit_output_cap':False,'forward_count':1,'candidate_token_ids':ids}
    return json.dumps({'value':max(values,key=lambda s:probs[s]),'logp':probs,'calibrated':False})
  backend=Backend(a.model or 'mock');ledger=RequestLedger(root,hash_obj({'series':'cross_fact_v1','freeze':freeze,'mock':a.mock,'model':backend.identity}),48)
  if not a.mock and subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():raise RuntimeError('GPU occupied')
  for item in cfg['requests']:
   dst=root/'results'/f'{item["id"]}.json'
   if dst.exists():continue
   pkg=PrefixPackage(pathlib.Path(a.input)/item['query_id']);target=pkg.handles[item['ref']]['time_ms'];ids=subset([f['evidence_id'] for f in pkg.manifest['frames'] if f['time_ms']<=target]);pixels=[pkg.read(i,'V3') for i in ids]
   prompt=f'At TARGET {item["ref"]} ({target} ms), check the stated visible condition of the named object using only RGB evidence at or before TARGET. Object: {item["object"]}. Stated condition: {item["condition"]}. Answer True if the full stated condition is visibly supported, False if visibly contradicted, or Unknown if evidence cannot decide. Answer exactly one token.'
   req={'query_id':item['query_id'],'stage':'AUTO_FACT','arm':item['side'],'prompt':prompt,'images':pixels,'image_ids':ids,'image_hashes':[hashlib.sha256(b).hexdigest() for b in pixels],'image_meta':[{'time_ms':pkg.handles[i]['time_ms']} for i in ids],'as_of_ms':14000,'target_ms':target,'limits':[5000,0],'input_type':'legal_rgb_goal_blind_generated_condition','parent_issued':555,'generated_from_as_of_ms':14000,'source_result_sha256':item['source_sha256']}
   raw=ledger.invoke(req,backend.generate);payload=json.loads(raw);save(dst,{'query_id':item['query_id'],'change':item['change'],'side':item['side'],'object':item['object'],'condition':item['condition'],'payload':payload,'raw':raw,'request':{k:v for k,v in req.items() if k!='images'}});save(root/'progress.json',{'issued':ledger.issued_count,'parent':555,'total':555+ledger.issued_count,'last':item['id']});print(json.dumps({'id':item['id'],'value':payload['value'],'issued':ledger.issued_count}),flush=True)
 finally:lock.unlink(missing_ok=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--core',required=True);p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--model');p.add_argument('--mock',action='store_true');run(p.parse_args())

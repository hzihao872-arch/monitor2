import argparse,hashlib,io,json,os,pathlib,subprocess,sys,time
H=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def options(p,q,order):return {'A':p,'B':q} if order=='positive_first' else {'A':q,'B':p}
def state_from_choice(value,order):
 if value=='Unknown':return value
 return 'True' if (value=='A')==(order=='positive_first') else 'False'
def save(p,x):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(canonical(x),encoding='utf-8');os.replace(tmp,p)
def run(a):
 sys.path.insert(0,a.core)
 from experiments.prerequisite_probe.change_first_monitor.qwen_backend import QwenBackend,prepare_content
 from experiments.prerequisite_probe.change_first_monitor.prefix import PrefixPackage
 from experiments.prerequisite_probe.change_first_monitor.runner import RequestLedger,hash_obj
 cfg=json.loads((H/'config.json').read_text());freeze=json.loads((H/'freeze.json').read_text())
 if freeze['files']!={n:sha(H/n) for n in ('config.json','scale_runner.py')}:raise RuntimeError('freeze changed')
 parent=H.parent/'reversal_transfer_20261009/download/run/requests.jsonl' if a.mock else pathlib.Path(cfg['parent']['path'])
 if sha(parent)!=cfg['parent']['sha256']:raise RuntimeError('parent ledger changed')
 if sum(json.loads(s)['kind']=='issued' for s in parent.read_text().splitlines())!=24:raise RuntimeError('parent count')
 root=pathlib.Path(a.output);root.mkdir(parents=True,exist_ok=True);lock=root/'.run.lock';os.close(os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY))
 try:
  class Backend(QwenBackend):
   def generate(self,req):
    if a.mock:
     self.last_metrics={'elapsed_seconds':0,'input_tokens':0,'output_tokens':0,'peak_vram_bytes':0,'hit_output_cap':False};return canonical({'choice':'Unknown','state':'Unknown'})
    self._load();import torch
    start=time.perf_counter();content=prepare_content(req);content=content[1:]+content[:1]
    from PIL import Image, __version__ as pillow_version
    transformed=[]
    for x in content:
     if x['type']=='image':
      source_size=x['image'].size;x['image']=x['image'].resize((source_size[0]*2,source_size[1]*2),Image.Resampling.BICUBIC);buf=io.BytesIO();x['image'].save(buf,format='PNG');transformed.append({'source_size':source_size,'input_size':x['image'].size,'sha256':hashlib.sha256(buf.getvalue()).hexdigest()})
    inputs=self.processor.apply_chat_template([{'role':'user','content':content}],tokenize=True,add_generation_prompt=True,return_dict=True,return_tensors='pt')
    n=int(inputs['input_ids'].shape[-1]);candidates=['A','B','Unknown'];ids={s:self.processor.tokenizer.encode(s,add_special_tokens=False) for s in candidates}
    if n>5000 or any(len(v)!=1 for v in ids.values()):raise RuntimeError('token contract')
    torch.cuda.reset_peak_memory_stats()
    with torch.inference_mode():
     output=self.model(**inputs.to('cuda'),logits_to_keep=1);lp=torch.log_softmax(output.logits[0,-1].float(),dim=-1);probs={s:float(lp[v[0]]) for s,v in ids.items()}
    torch.cuda.synchronize();choice=max(candidates,key=lambda s:probs[s])
    self.last_metrics={'input_tokens':n,'output_tokens':0,'elapsed_seconds':time.perf_counter()-start,'peak_vram_bytes':int(torch.cuda.max_memory_allocated()),'hit_output_cap':False,'candidate_token_ids':ids,'forward_count':1,'transform':'full-frame bicubic 2x','pillow_version':pillow_version,'transformed':transformed,'image_grid_thw':inputs['image_grid_thw'].tolist()}
    return canonical({'choice':choice,'state':state_from_choice(choice,req['order']),'logp':probs,'calibrated':False})
  backend=Backend(a.model or 'mock');ledger=RequestLedger(root,hash_obj({'series':'fullframe_scale_v1','freeze':freeze,'mock':a.mock,'model':backend.identity}),24)
  if not a.mock and subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():raise RuntimeError('GPU occupied')
  for item in cfg['requests']:
   dst=root/'results'/f'{item["id"]}.json'
   if dst.exists():continue
   pkg=PrefixPackage(pathlib.Path(a.input)/item['query_id']);target=pkg.handles[item['ref']]['time_ms'];ids=[item['ref']] if item['kind']=='rgb' else [];pixels=[pkg.read(item['ref'],'V3')] if ids else []
   opts=options(item['positive'],item['opposed'],item['order'])
   prompt=f'At TARGET {item["ref"]} ({target} ms), which positive visible-state description matches the evidence? A: {opts["A"]} B: {opts["B"]} '
   if item['kind']=='oracle':prompt+='Supplied visible facts at TARGET (extra-input diagnostic): '+item['fact']+' '
   prompt+='Choose A or B, or Unknown if the evidence cannot decide. Answer exactly one token.'
   req={'query_id':item['query_id'],'probe_id':item['probe_id'],'stage':'CHOICE','arm':item['kind']+'_'+item['order'],'prompt':prompt,'order':item['order'],
    'images':pixels,'image_ids':ids,'image_hashes':[hashlib.sha256(b).hexdigest() for b in pixels],'image_meta':[{'time_ms':target}] if ids else [],'limits':[5000,0],'as_of_ms':target,
    'transform':{'factor':2,'resample':'bicubic','scope':'entire frame'},'input_type':'legal_rgb_directed_diagnostic','parent_issued':307}
   raw=ledger.invoke(req,backend.generate);payload=json.loads(raw)
   save(dst,{'probe_id':item['probe_id'],'kind':item['kind'],'order':item['order'],'development_split':item['split'],'raw':raw,'payload':payload,'request':{k:v for k,v in req.items() if k!='images'}})
   save(root/'progress.json',{'issued':ledger.issued_count,'parent':307,'total':307+ledger.issued_count,'last':item['id']});print(canonical({'id':item['id'],'state':payload['state'],'issued':ledger.issued_count}),flush=True)
 finally:lock.unlink(missing_ok=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--core',required=True);p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--model');p.add_argument('--mock',action='store_true');run(p.parse_args())

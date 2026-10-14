import argparse,hashlib,io,json,os,pathlib,subprocess,sys,time
H=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def causal_ids(frames,t):return [f['evidence_id'] for f in frames if f['time_ms']<=t]
def subset(ids,n):
 return [ids[round(i*(len(ids)-1)/(n-1))] for i in range(n)]
def video_times(n):
 ids=list(range(n));ids+=ids[-1:] if n%2 else [];return [(a+b)/2 for a,b in zip(ids[::2],ids[1::2])]
def save(p,x):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(canonical(x),encoding='utf-8');os.replace(tmp,p)
def encode(processor,req):
 from PIL import Image
 images=[Image.open(io.BytesIO(b)).convert('RGB') for b in req['images']]
 if req['representation']=='images':
  content=[]
  for im,m in zip(images,req['image_meta']):content.extend([{'type':'text','text':f'Frame at {m["time_ms"]/1000:.1f} seconds:'},{'type':'image','image':im}])
  content.append({'type':'text','text':req['prompt']})
  return processor.apply_chat_template([{'role':'user','content':content}],tokenize=True,add_generation_prompt=True,return_dict=True,return_tensors='pt')
 import numpy as np
 from transformers.video_utils import VideoMetadata
 meta=VideoMetadata(total_num_frames=len(images),fps=1.,frames_indices=list(range(len(images))))
 content=[{'type':'video'},{'type':'text','text':req['prompt']}]
 text=processor.apply_chat_template([{'role':'user','content':content}],tokenize=False,add_generation_prompt=True)
 return processor(text=[text],videos=[np.stack([np.asarray(i) for i in images])],video_metadata=[meta],do_sample_frames=False,return_tensors='pt')
def run(a):
 sys.path.insert(0,a.core)
 from experiments.prerequisite_probe.change_first_monitor.qwen_backend import QwenBackend
 from experiments.prerequisite_probe.change_first_monitor.prefix import PrefixPackage
 from experiments.prerequisite_probe.change_first_monitor.runner import RequestLedger,hash_obj
 cfg=json.loads((H/'config.json').read_text());freeze=json.loads((H/'freeze.json').read_text())
 if freeze['files']!={n:sha(H/n) for n in ('config.json','sampling_runner.py')}:raise RuntimeError('freeze changed')
 parent=H.parent/'prior_control_20261009/download/run/requests.jsonl' if a.mock else pathlib.Path(cfg['parent']['path'])
 if sha(parent)!=cfg['parent']['sha256']:raise RuntimeError('parent changed')
 if sum(json.loads(s)['kind']=='issued' for s in parent.read_text().splitlines())!=16:raise RuntimeError('parent count')
 root=pathlib.Path(a.output);root.mkdir(parents=True,exist_ok=True)
 if a.processor_only:
  from transformers import AutoProcessor
  processor=AutoProcessor.from_pretrained(a.model,local_files_only=True)
  item=cfg['requests'][0];pkg=PrefixPackage(pathlib.Path(a.input)/item['query_id']);ids=causal_ids(pkg.manifest['frames'],14000)
  result={}
  for rep in ('images','video'):
   req={'images':[pkg.read(i,'V1') for i in ids],'image_meta':[{'time_ms':pkg.handles[i]['time_ms']} for i in ids],'prompt':'At 14.0 seconds, choose A or B.','representation':rep}
   encoded=encode(processor,req);text=processor.tokenizer.decode(encoded['input_ids'][0]);result[rep]={'input_tokens':encoded['input_ids'].shape[-1],'shapes':{k:list(v.shape) for k,v in encoded.items() if hasattr(v,'shape')},'native_times_found':[f'<{t:.1f} seconds>' in text for t in video_times(len(ids))] if rep=='video' else []}
  save(root/'processor_check.json',result);print(canonical(result));return
 lock=root/'.run.lock';os.close(os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY))
 try:
  class Backend(QwenBackend):
   def generate(self,req):
    if a.mock:
     self.last_metrics={'elapsed_seconds':0,'input_tokens':0,'output_tokens':0,'peak_vram_bytes':0,'hit_output_cap':False};return canonical({'choice':'Unknown','state':'Unknown'})
    self._load();import torch
    start=time.perf_counter();inputs=encode(self.processor,req);n=int(inputs['input_ids'].shape[-1]);candidates=['A','B','Unknown'];ids={s:self.processor.tokenizer.encode(s,add_special_tokens=False) for s in candidates}
    if n>5000 or any(len(v)!=1 for v in ids.values()):raise RuntimeError('token contract')
    decoded=self.processor.tokenizer.decode(inputs['input_ids'][0]);times=video_times(len(req['images']))
    if req['representation']=='video' and not all(f'<{t:.1f} seconds>' in decoded for t in times):raise RuntimeError('timestamp contract')
    shapes={k:list(v.shape) for k,v in inputs.items() if hasattr(v,'shape')};torch.cuda.reset_peak_memory_stats()
    with torch.inference_mode():
     output=self.model(**inputs.to('cuda'),logits_to_keep=1);lp=torch.log_softmax(output.logits[0,-1].float(),dim=-1);probs={s:float(lp[v[0]]) for s,v in ids.items()}
    torch.cuda.synchronize();choice=max(candidates,key=lambda s:probs[s]);state='Unknown' if choice=='Unknown' else ('True' if (choice=='A')==(req['order']=='positive_first') else 'False')
    self.last_metrics={'input_tokens':n,'output_tokens':0,'elapsed_seconds':time.perf_counter()-start,'peak_vram_bytes':int(torch.cuda.max_memory_allocated()),'hit_output_cap':False,'candidate_token_ids':ids,'forward_count':1,'tensor_shapes':shapes,'native_timestamps':times if req['representation']=='video' else []}
    return canonical({'choice':choice,'state':state,'logp':probs,'calibrated':False})
  backend=Backend(a.model or 'mock');ledger=RequestLedger(root,hash_obj({'series':'prefix_sampling_v1','freeze':freeze,'mock':a.mock,'model':backend.identity}),24)
  if not a.mock and subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():raise RuntimeError('GPU occupied')
  for item in cfg['requests']:
   dst=root/'results'/f'{item["id"]}.json'
   if dst.exists():continue
   pkg=PrefixPackage(pathlib.Path(a.input)/item['query_id']);target=14000;ids=causal_ids(pkg.manifest['frames'],target);times=[pkg.handles[i]['time_ms'] for i in ids]
   if times!=list(range(0,15000,1000)):raise RuntimeError('regular sparse prefix required')
   ids=subset(ids,item['sample_count']);times=[pkg.handles[i]['time_ms'] for i in ids]
   positive_first=item['order']=='positive_first';aa=item['positive'] if positive_first else item['opposed'];bb=item['opposed'] if positive_first else item['positive']
   prompt=f'Use the chronological RGB prefix through 14.0 seconds. At TARGET 14.0 seconds, which positive visible-state description matches the evidence? A: {aa} B: {bb} Choose A or B, or Unknown if the evidence cannot decide. Answer exactly one token.'
   pixels=[pkg.read(i,'V1') for i in ids]
   req={'query_id':item['query_id'],'probe_id':item['probe_id'],'stage':'PREFIX_CHOICE','arm':'n'+str(item['sample_count'])+'_'+item['order'],'prompt':prompt,'order':item['order'],'sample_count':item['sample_count'],'representation':item['representation'],'images':pixels,'image_ids':ids,'image_hashes':[hashlib.sha256(b).hexdigest() for b in pixels],'image_meta':[{'time_ms':t} for t in times],'limits':[5000,0],'as_of_ms':target,'input_type':'legal_rgb_directed_diagnostic','parent_issued':204,'native_metadata':{'fps':1,'do_sample_frames':False,'temporal_patch_size':2,'padding':'repeat last past frame'} if item['representation']=='video' else None}
   raw=ledger.invoke(req,backend.generate);payload=json.loads(raw);save(dst,{'probe_id':item['probe_id'],'sample_count':item['sample_count'],'representation':item['representation'],'order':item['order'],'development_split':item['split'],'raw':raw,'payload':payload,'request':{k:v for k,v in req.items() if k!='images'}})
   save(root/'progress.json',{'issued':ledger.issued_count,'parent':204,'total':204+ledger.issued_count,'last':item['id']});print(canonical({'id':item['id'],'state':payload['state'],'issued':ledger.issued_count}),flush=True)
 finally:lock.unlink(missing_ok=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--core',required=True);p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--model');p.add_argument('--mock',action='store_true');p.add_argument('--processor-only',action='store_true');run(p.parse_args())

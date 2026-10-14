import argparse,hashlib,io,json,os,pathlib,subprocess,sys,time
H=pathlib.Path(__file__).resolve().parent
BASE='The above video shows a robot manipulation trajectory that completes the following task: '
AUG=' Therefore given the above description and the video, the video shows a robot manipulation trajectory that **completes** the following instruction: '
SUFFIX=' Decide whether the above statement is True or not. The answer is: '
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(p,x):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True),encoding='utf-8');os.replace(tmp,p)
def last_forms(tokenizer,rendered):
 forms={s:tokenizer.encode(rendered+s,add_special_tokens=False) for s in ('True','False','Unknown')};prefix=forms['True'][:-1]
 if any(v[:-1]!=prefix for v in forms.values()):raise RuntimeError('label changes prefix tokenization')
 return {s:v[-1] for s,v in forms.items()}
def run(a):
 sys.path.insert(0,a.core)
 from experiments.prerequisite_probe.change_first_monitor.qwen_backend import QwenBackend
 from experiments.prerequisite_probe.change_first_monitor.prefix import PrefixPackage
 from experiments.prerequisite_probe.change_first_monitor.runner import RequestLedger,hash_obj
 from native_encoder import encode,video_times
 cfg=json.loads((H/'config.json').read_text());freeze=json.loads((H/'freeze.json').read_text())
 if freeze['files']!={n:sha(H/n) for n in ('config.json','context_runner.py','native_encoder.py')}:raise RuntimeError('freeze changed')
 parent=H.parent/'fullframe_scale_20261009/download/run/requests.jsonl' if a.mock else pathlib.Path(cfg['parent']['path'])
 if sha(parent)!=cfg['parent']['sha256'] or sum(json.loads(s)['kind']=='issued' for s in parent.read_text().splitlines())!=24:raise RuntimeError('parent changed')
 root=pathlib.Path(a.output);root.mkdir(parents=True,exist_ok=True);lock=root/'.run.lock';os.close(os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY))
 try:
  class Backend(QwenBackend):
   def generate(self,req):
    if a.mock:
     self.last_metrics={'elapsed_seconds':0,'input_tokens':0,'output_tokens':0,'peak_vram_bytes':0,'hit_output_cap':False};return 'Mock description.' if req['arm']=='description' else json.dumps({'value':'Unknown','true_logp':-3,'logp':{'True':-3,'False':-2,'Unknown':-1}})
    self._load();import numpy as np,torch
    from PIL import Image
    from transformers.video_utils import VideoMetadata
    t=time.perf_counter();torch.cuda.reset_peak_memory_stats()
    if req['arm']=='description':
     inputs=encode(self.processor,req);n=int(inputs['input_ids'].shape[-1])
     if n>5000:raise RuntimeError('input cap')
     with torch.inference_mode():output=self.model.generate(**inputs.to('cuda'),max_new_tokens=256,do_sample=False)
     completion=output[:,n:];raw=self.processor.batch_decode(completion,skip_special_tokens=True)[0];out_n=int(completion.shape[-1]);extra={}
    else:
     content=[{'type':'video'},{'type':'text','text':req['base']}];rendered=self.processor.apply_chat_template([{'role':'user','content':content}],tokenize=False,add_generation_prompt=False);before=rendered;eos=self.processor.tokenizer.eos_token
     if eos:rendered=rendered.split(eos)[0]
     if rendered.count('<|video_pad|>')!=before.count('<|video_pad|>'):raise RuntimeError('EOS removed vision')
     rendered+=req['instruction']+SUFFIX;forms=last_forms(self.processor.tokenizer,rendered)
     frames=np.stack([np.asarray(Image.open(io.BytesIO(b)).convert('RGB')) for b in req['images']]);meta=VideoMetadata(total_num_frames=len(frames),fps=1.,frames_indices=list(range(len(frames))))
     inputs=self.processor(text=[rendered+'True'],videos=[frames],video_metadata=[meta],do_sample_frames=False,return_tensors='pt');n=int(inputs['input_ids'].shape[-1]);label=int(inputs['input_ids'][0,-1])
     if n>5000 or label!=forms['True']:raise RuntimeError('label token contract')
     decoded=self.processor.tokenizer.decode(inputs['input_ids'][0])
     if not all(f'<{v:.1f} seconds>' in decoded for v in video_times(len(frames))):raise RuntimeError('timestamps')
     with torch.inference_mode():output=self.model(**inputs.to('cuda'),logits_to_keep=2);lp=torch.log_softmax(output.logits[0,-2].float(),dim=-1);logp={s:float(lp[i]) for s,i in forms.items()}
     raw=json.dumps({'true_logp':logp['True'],'logp':logp,'value':max(logp,key=logp.get),'calibrated':False,'objective':'exact conditional probability of final appended True token; no full trajectory normalization'});out_n=0;extra={'label_token_ids':forms,'true_label':label,'vision_grid':inputs['video_grid_thw'].tolist(),'context_generated':req['arm']=='augmented'}
    torch.cuda.synchronize();self.last_metrics={'elapsed_seconds':time.perf_counter()-t,'input_tokens':n,'output_tokens':out_n,'peak_vram_bytes':int(torch.cuda.max_memory_allocated()),'hit_output_cap':out_n>=256,'forward_count':None if req['arm']=='description' else 1,**extra};return raw
  backend=Backend(a.model or 'mock');ledger=RequestLedger(root,hash_obj({'series':'author_context_v1','freeze':freeze,'mock':a.mock,'model':backend.identity}),24)
  if not a.mock and subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():raise RuntimeError('GPU occupied')
  for item in cfg['queries']:
   pkg=PrefixPackage(pathlib.Path(a.input)/item['query_id']);frames=[f for f in pkg.manifest['frames'] if f['time_ms']<=14000];ids=[f['evidence_id'] for f in frames];pixels=[pkg.read(i,'V1') for i in ids]
   if len(ids)!=15:raise RuntimeError('prefix')
   description=None
   for arm in ('description','direct','augmented'):
    dst=root/'results'/f'{item["query_id"]}_{arm}.json'
    if dst.exists():
     if arm=='description':description=json.loads(dst.read_text())['raw']
     continue
    base=BASE if arm!='augmented' else description+AUG
    prompt='Describe the robot manipulation trajectory in this video:' if arm=='description' else base+item['goal']+SUFFIX+'True'
    req={'query_id':item['query_id'],'stage':'AUTHOR_CONTEXT','arm':arm,'prompt':prompt,'base':base,'instruction':item['goal'] if arm!='description' else None,'representation':'video','images':pixels,'image_ids':ids,'image_hashes':[hashlib.sha256(b).hexdigest() for b in pixels],'image_meta':[{'time_ms':pkg.handles[i]['time_ms']} for i in ids],'as_of_ms':14000,'limits':[5000,256 if arm=='description' else 0],'input_type':'legal_rgb_goal_blind_description' if arm=='description' else 'legal_rgb_author_completion_score','parent_issued':331,'source_commit':cfg['source_commit'],'constant_scoring_label':'True' if arm!='description' else None}
    raw=ledger.invoke(req,backend.generate)
    if arm=='description':description=raw
    save(dst,{'query_id':item['query_id'],'arm':arm,'raw':raw,'payload':None if arm=='description' else json.loads(raw),'request':{k:v for k,v in req.items() if k!='images'}});save(root/'progress.json',{'issued':ledger.issued_count,'parent':331,'total':331+ledger.issued_count,'last':item['query_id']+'_'+arm});print(json.dumps({'query':item['query_id'],'arm':arm,'issued':ledger.issued_count}),flush=True)
 finally:lock.unlink(missing_ok=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--core',required=True);p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--model');p.add_argument('--mock',action='store_true');run(p.parse_args())

import argparse,hashlib,io,json,os,pathlib,subprocess,sys,time
H=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(p,x):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True),encoding='utf-8');os.replace(tmp,p)
def validate(raw):
 try:
  obj=json.loads(raw)
  if type(obj)!=list or len(obj)!=5:raise ValueError('five frames required')
  if {r.get('frame_number') for r in obj}!={1,2,3,4,5}:raise ValueError('exact frame numbers')
  for r in obj:
   if set(r)!={'frame_number','frame_description','task_completion_percentage'} or type(r['frame_number'])!=int:raise ValueError('contract')
   if type(r['task_completion_percentage'])!=int or not 0<=r['task_completion_percentage']<=100:raise ValueError('integer percentage')
   if type(r['frame_description'])!=str or len(r['frame_description'])>160:raise ValueError('description length/type')
  return {'valid':True,'payload':obj,'errors':[]}
 except (ValueError,TypeError,AttributeError,KeyError) as e:return {'valid':False,'payload':None,'errors':[str(e)]}
def run(a):
 sys.path.insert(0,a.core)
 from experiments.prerequisite_probe.change_first_monitor.qwen_backend import QwenBackend
 from experiments.prerequisite_probe.change_first_monitor.prefix import PrefixPackage
 from experiments.prerequisite_probe.change_first_monitor.runner import RequestLedger,hash_obj
 cfg=json.loads((H/'config.json').read_text());freeze=json.loads((H/'freeze.json').read_text())
 if freeze['files']!={n:sha(H/n) for n in ('config.json','gvl_runner.py')}:raise RuntimeError('freeze changed')
 parent=H.parent/'gvl_order_20261009/download/run/requests.jsonl' if a.mock else pathlib.Path(cfg['parent']['path'])
 if sha(parent)!=cfg['parent']['sha256'] or sum(json.loads(s)['kind']=='issued' for s in parent.read_text().splitlines())!=16:raise RuntimeError('parent changed')
 root=pathlib.Path(a.output);root.mkdir(parents=True,exist_ok=True);lock=root/'.run.lock';os.close(os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY))
 try:
  class Backend(QwenBackend):
   def generate(self,req):
    if a.mock:
     self.last_metrics={'elapsed_seconds':0,'input_tokens':0,'output_tokens':0,'peak_vram_bytes':0,'hit_output_cap':False};return json.dumps([{'frame_number':i,'frame_description':'mock','task_completion_percentage':0} for i in range(1,6)])
    self._load();import torch
    from PIL import Image
    t=time.perf_counter();ims=[Image.open(io.BytesIO(b)).convert('RGB') for b in req['images']]
    content=[{'type':'text','text':req['prompt']+' Initial scene:'},{'type':'image','image':ims[0]},{'type':'text','text':'The initial scene defines the zero-percent reference. Now score these individual frames, which may be in any order:'}]
    for i,im in enumerate(ims[1:],1):content.extend([{'type':'text','text':f'Frame {i}:'},{'type':'image','image':im}])
    inputs=self.processor.apply_chat_template([{'role':'user','content':content}],tokenize=True,add_generation_prompt=True,return_dict=True,return_tensors='pt');n=int(inputs['input_ids'].shape[-1])
    if n>5000:raise RuntimeError('input cap')
    torch.cuda.reset_peak_memory_stats()
    with torch.inference_mode():output=self.model.generate(**inputs.to('cuda'),max_new_tokens=1024,do_sample=False)
    completion=output[:,n:];raw=self.processor.batch_decode(completion,skip_special_tokens=True)[0];torch.cuda.synchronize();out_n=int(completion.shape[-1]);self.last_metrics={'elapsed_seconds':time.perf_counter()-t,'input_tokens':n,'output_tokens':out_n,'peak_vram_bytes':int(torch.cuda.max_memory_allocated()),'hit_output_cap':out_n>=1024};return raw
  backend=Backend(a.model or 'mock');ledger=RequestLedger(root,hash_obj({'series':'gvl_order_v2','freeze':freeze,'mock':a.mock,'model':backend.identity}),16)
  if not a.mock and subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():raise RuntimeError('GPU occupied')
  for item in cfg['requests']:
   dst=root/'results'/f'{item["query_id"]}_{item["order"]}.json'
   if dst.exists():continue
   pkg=PrefixPackage(pathlib.Path(a.input)/item['query_id']);ids=['f0000']+item['ids'];pixels=[pkg.read(i,'V1') for i in ids]
   prompt=f'Estimate progress toward this robot task: {item["goal"]} Use integer percentages from 0 to 100, with 100 meaning complete task execution. The separately supplied initial scene is the zero-percent reference. Assess each shown frame on its own visible state, rather than assuming later presentation means more progress. Return only a JSON array of exactly five objects, with exact keys frame_number (integer shown label 1..5), frame_description (brief visible description, at most 160 characters), task_completion_percentage (integer 0..100). Include every shown frame once. Do not infer hidden actions or add a task plan. The first output character must be [. Do not use code fences, markdown, or prose outside the array.'
   req={'query_id':item['query_id'],'stage':'GVL_ORDER','arm':item['order'],'prompt':prompt,'images':pixels,'image_ids':ids,'image_hashes':[hashlib.sha256(b).hexdigest() for b in pixels],'image_meta':[{'time_ms':pkg.handles[i]['time_ms']} for i in ids],'as_of_ms':14000,'limits':[5000,1024],'input_type':'legal_rgb_progress_zero_shot_gvl_adaptation','parent_issued':388,'source_commit':cfg['source_commit'],'host_only_frame_mapping':{str(j):i for j,i in enumerate(item['ids'],1)},'model_time_labels':False,'scope':'retrospective past-frame scoring at as_of14; not prospective score at each older frame'}
   raw=ledger.invoke(req,backend.generate);v=validate(raw);save(dst,{'query_id':item['query_id'],'order':item['order'],'raw':raw,'validation':v,'request':{k:v for k,v in req.items() if k!='images'}});save(root/'progress.json',{'issued':ledger.issued_count,'parent':388,'total':388+ledger.issued_count,'last':item['query_id']+'_'+item['order']});print(json.dumps({'query':item['query_id'],'order':item['order'],'valid':v['valid'],'issued':ledger.issued_count}),flush=True)
 finally:lock.unlink(missing_ok=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--core',required=True);p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--model');p.add_argument('--mock',action='store_true');run(p.parse_args())

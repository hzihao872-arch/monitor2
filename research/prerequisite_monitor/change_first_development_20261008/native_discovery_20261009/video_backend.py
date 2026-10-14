import argparse,hashlib,io,json,os,pathlib,subprocess,sys,time
H=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def causal_ids(frames,t):return [f['evidence_id'] for f in frames if f['time_ms']<=t]
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
 content=[{'type':'text','text':req['prompt']},{'type':'video'}]
 text=processor.apply_chat_template([{'role':'user','content':content}],tokenize=False,add_generation_prompt=True)
 return processor(text=[text],videos=[np.stack([np.asarray(i) for i in images])],video_metadata=[meta],do_sample_frames=False,return_tensors='pt')

def generate_video(backend,req):
 backend._load();import torch
 start=time.perf_counter();req=dict(req,representation='video');encoded=encode(backend.processor,req);n=int(encoded['input_ids'].shape[-1]);cap_in,cap_out=req['limits']
 if n>cap_in:raise RuntimeError('input cap')
 decoded=backend.processor.tokenizer.decode(encoded['input_ids'][0]);times=video_times(len(req['images']))
 if not all(f'<{t:.1f} seconds>' in decoded for t in times):raise RuntimeError('timestamp contract')
 torch.cuda.reset_peak_memory_stats()
 with torch.inference_mode():output=backend.model.generate(**encoded.to('cuda'),max_new_tokens=cap_out,do_sample=False)
 completion=output[:,n:];raw=backend.processor.batch_decode(completion,skip_special_tokens=True)[0];torch.cuda.synchronize()
 backend.last_metrics={'input_tokens':n,'output_tokens':int(completion.shape[-1]),'elapsed_seconds':time.perf_counter()-start,'peak_vram_bytes':int(torch.cuda.max_memory_allocated()),'hit_output_cap':int(completion.shape[-1])>=cap_out,'native_timestamps':times,'fps':1.,'do_sample_frames':False,'query_first':True}
 return raw

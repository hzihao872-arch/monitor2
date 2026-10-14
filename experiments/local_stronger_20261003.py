"""Existing local Qwen3-VL 8B Ollama diagnostic, separate from BF16 protocol runs."""
import argparse,base64,hashlib,json,time,urllib.request
from datetime import datetime,timezone
from pathlib import Path
import experiments.monitor_eval as ev
import experiments.summary_isolation_20261003 as isolation
from experiments.run_online import validate_media
ROOT=Path('experiments/artifacts/r1_local_stronger_20261003')
SOURCE=isolation.SOURCE
MODEL='qwen3-vl:8b-instruct'
BASE='http://127.0.0.1:11434'
OPTIONS={'temperature':0,'seed':0,'repeat_penalty':1.0,'num_ctx':4096,'num_predict':256}
NEUTRAL='Describe only what is visible in this image: the colors and relative positions of the cubes, and any occlusion. Use at most 35 English words. Do not infer a task, intended action, or completion. Return plain text.'

def api(path,data=None,timeout=240):
 req=urllib.request.Request(BASE+path,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=timeout) as response:return json.load(response)

def accept_response(raw,tick,previous,input_tokens,output_tokens):
 parsed=ev.parse_output(raw,['green_on_blue'],tick)
 reason='input_tokens' if input_tokens>3840 else ('output_tokens' if output_tokens>256 else None)
 if len(parsed.get('memory','').encode('utf-8'))>512:reason=reason or 'memory_utf8_bytes'
 if reason:parsed['parse_status']='budget_failure';parsed['judgments']={'green_on_blue':ev._invalid_judgment()}
 parsed['memory']=parsed['memory'] if not reason and parsed['parse_status']=='valid' else previous
 parsed['budget_reason']=reason
 return parsed

def save(name,obj):
 (ROOT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n','utf-8')

def call(track,tick,method,memory,phase):
 start=time.perf_counter();frames=ev.frame_packet(track,tick);instruction=ev.instruction_at(track,tick)
 prompt=NEUTRAL if method=='neutral' else isolation.prompt(method,instruction,track['objects'],memory,tick)
 prompt+='\nImages are supplied in the following order (video playback seconds): '+', '.join(str(f['time']) for f in frames)+'.'
 assert max(f['time'] for f in frames)<=tick and len(frames)<=4
 image_bytes=[Path(f['path']).read_bytes() for f in frames]
 assert [hashlib.sha256(x).hexdigest() for x in image_bytes]==[f['sha256'] for f in frames]
 assert len(memory.encode('utf-8'))<=512
 payload={'model':MODEL,'messages':[{'role':'user','content':prompt,'images':[base64.b64encode(x).decode() for x in image_bytes]}],'stream':False,'options':OPTIONS,'keep_alive':'10m'}
 status='returned';error='';response={}
 try:
  response=api('/api/chat',payload)
  raw=response['message']['content'];input_tokens=response['prompt_eval_count'];output_tokens=response['eval_count']
  parsed=accept_response(raw,tick,memory,input_tokens,output_tokens) if method!='neutral' else {'parse_status':'plain_text','memory':'','judgments':{},'budget_reason':None}
 except Exception as exc:
  status='runtime_failure';error=repr(exc);raw=None;input_tokens=output_tokens=0
  parsed={'parse_status':'runtime_failure','memory':memory,'judgments':{'green_on_blue':ev._invalid_judgment()},'budget_reason':None}
 elapsed=(time.perf_counter()-start)*1000
 try:ps=api('/api/ps',timeout=15)
 except Exception as exc:ps={'telemetry_error':repr(exc)}
 row={'model':MODEL,'phase':phase,'trajectory_id':track['trajectory_id'],'tick':tick,'method':method,'prompt':prompt,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'frame_times':[f['time'] for f in frames],'frame_paths':[f['path'] for f in frames],'frame_sha256':[f['sha256'] for f in frames],'request_sha256':hashlib.sha256(json.dumps(payload).encode()).hexdigest(),'memory_in':memory,'raw':raw,'memory_out':parsed['memory'] if method=='S1' else None,'parse_status':parsed['parse_status'],'judgments':parsed['judgments'],'budget_reason':parsed['budget_reason'],'status':status,'error':error,'native_response':response,'model_residency_after':ps,'cost':{'calls':1,'input_tokens_ollama':input_tokens,'output_tokens_ollama':output_tokens,'memory_in_utf8_bytes':len(memory.encode('utf-8')),'memory_out_utf8_bytes':len(parsed['memory'].encode('utf-8')),'request_wall_ms':elapsed,'peak_vram_bytes':None}}
 return row

def run(track_path,method,ticks,outdir,phase):
 track=ev.load_online_track(track_path);validate_media(track)
 out=ROOT/outdir;out.mkdir(exist_ok=False);memory='';rows=[]
 for tick in ticks:
  r=call(track,tick,method,memory if method=='S1' else '',phase);rows.append(r)
  ev._append_jsonl(out/'records.jsonl',r)
  ev._append_ledger('experiments/run_ledger.csv',{'run_id':f'local8b-{outdir}-q{tick}','utc':datetime.now(timezone.utc).isoformat(),'kind':'local8b_exploratory','track':str(out/'records.jsonl'),'method':method,'backend':'Ollama-local-Q4_K_M','status':r['status'],'ticks_recorded':1,'call_attempts':1,'input_tokens_known':r['cost']['input_tokens_ollama'],'output_tokens_known':r['cost']['output_tokens_ollama'],'elapsed_ms_known':r['cost']['request_wall_ms'],'error':r['error']})
  print(outdir,tick,r['parse_status'],repr(r['raw']),flush=True)
  if method=='S1':memory=r['memory_out']
  if r['status']=='runtime_failure' or r['budget_reason']:break
 save(str(Path(outdir)/'summary.json'),{'calls':len(rows),'valid':sum(r['parse_status']=='valid' for r in rows),'input_tokens_ollama':sum(r['cost']['input_tokens_ollama'] for r in rows),'output_tokens_ollama':sum(r['cost']['output_tokens_ollama'] for r in rows),'request_wall_ms':sum(r['cost']['request_wall_ms'] for r in rows)})
 return all(r['status']=='returned' and not r['budget_reason'] for r in rows)

def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=['probe','chain','full'],required=True);args=p.parse_args()
 pre=json.loads((ROOT/'preregistration.json').read_text('utf-8'))
 for f in pre['frozen_files']:assert hashlib.sha256(Path(f['path']).read_bytes()).hexdigest()==f['sha256'],f['path']
 tags=api('/api/tags');found=[m for m in tags['models'] if m['name']==MODEL];assert len(found)==1 and found[0]['digest']==pre['model_digest']
 if args.phase!='probe':assert json.loads((ROOT/('probe_review.json' if args.phase=='chain' else 'chain_review.json')).read_text('utf-8'))['pass']
 track=SOURCE/'p0/ep618/online_track.json'
 if args.phase=='probe':
  if not run(track,'neutral',[0],'probe_neutral_q0','probe'):return
  for q in (0,2,6):
   if not run(track,'S1',[q],f'probe_joint_q{q}','probe'):return
 elif args.phase=='chain':run(track,'S1',range(9),'chain_ep618','chain')
 else:
  for ep,n in [(618,16),(621,15)]:
   for method in ['S0','S1']:
    if not run(SOURCE/f'p0/ep{ep}/online_track.json',method,range(n),f'full_ep{ep}_{method}','full'):return
if __name__=='__main__':main()

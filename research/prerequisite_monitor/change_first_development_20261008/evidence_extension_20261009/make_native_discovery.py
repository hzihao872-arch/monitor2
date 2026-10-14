import pathlib,json,hashlib,zipfile
H=pathlib.Path(__file__).resolve().parent;B=H.parent;S=B/'dense_discovery_20261009';D=B/'native_discovery_20261009';D.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cfg=json.loads((S/'config.json').read_text());cfg['parent']={'path':'/root/autodl-tmp/monitor2/fresh_prerequisite_runs/change_first_local_windows_20261009_v1/run/requests.jsonl','sha256':sha(B/'local_windows_20261009/remote_verified/run/requests.jsonl')};cfg['protocol']='Same goal-blind dense prompt and same15 legal frames, native temporal representation, query first, honest fps1 and indices0..14, no resampling. Individual original frame IDs are host timestamp mapping, not literal per-image labels in native paired video. Natural token/representation comparison, not equal compute.'
(D/'config.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8');(D/'contracts.py').write_bytes((S/'contracts.py').read_bytes())
t=(B/'native_prefix_20261009/native_runner.py').read_text().split('def run(a):')[0].replace("content=[{'type':'video'},{'type':'text','text':req['prompt']}]","content=[{'type':'text','text':req['prompt']},{'type':'video'}]")
t+='''
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
'''
(D/'video_backend.py').write_text(t,encoding='utf-8')
t=(S/'dense_runner.py').read_text().replace('dense_runner.py','video_runner.py').replace("'contracts.py')","'contracts.py','video_backend.py')").replace("'prefix_sampling_20261009/download/run/requests.jsonl'","'local_windows_20261009/remote_verified/run/requests.jsonl'").replace("!=24:raise RuntimeError('parent changed')","!=56:raise RuntimeError('parent changed')").replace("'dense_discovery_v1'","'native_discovery_v1'").replace("'arm':'dense_full15'","'arm':'native_full15'").replace("'parent_issued':228","'parent_issued':539").replace("'parent':228,'total':228+ledger.issued_count","'parent':539,'total':539+ledger.issued_count").replace('return super().generate(req)','from video_backend import generate_video\n    return generate_video(self,req)')
(D/'video_runner.py').write_text(t,encoding='utf-8');(D/'test_video.py').write_text("from video_backend import video_times\nassert video_times(15)==[.5,2.5,4.5,6.5,8.5,10.5,12.5,14.]\nassert video_times(1)==[0.]\nprint('odd native padding and temporal checks passed')\n",encoding='utf-8')
(D/'freeze.json').write_text(json.dumps({'files':{n:sha(D/n) for n in ('config.json','video_runner.py','contracts.py','video_backend.py')}},indent=2),encoding='utf-8')
with zipfile.ZipFile(D/'video_v1.zip','w') as z:
 for n in ('config.json','freeze.json','video_runner.py','contracts.py','video_backend.py','test_video.py'):z.write(D/n,n)
t=(B/'inventory_binding_20261009/remote_ops.py').read_text().replace('change_first_inventory_binding_20261009_v1','change_first_native_discovery_20261009_v1').replace('inventory_v1.zip','video_v1.zip').replace('inventory_runner.py','video_runner.py').replace('test_inventory.py','test_video.py').replace('inventory_FINAL.tar.gz','video_FINAL.tar.gz');(D/'remote_ops.py').write_text(t,encoding='utf-8')
t=(B/'inventory_binding_20261009/seal_remote.py').read_text().replace('inventory_runner.py','video_runner.py').replace('inventory_FINAL.tar.gz','video_FINAL.tar.gz');(D/'seal_remote.py').write_text(t,encoding='utf-8');print(sha(D/'video_v1.zip'))

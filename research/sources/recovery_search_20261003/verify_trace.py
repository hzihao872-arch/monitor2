"""Recompute source hashes, correspondence, time flags, and exact P0 packets."""
import json,hashlib,subprocess
from pathlib import Path
import numpy as np
from PIL import Image
from trace_sources import ROOT,OUT,save

checks={}
for manifest,base,key in [(ROOT/'fetch_manifest.json',ROOT,'previous_batch'),(OUT/'fetch_manifest.json',OUT,'trace_batch')]:
    rows=json.loads(manifest.read_text('utf-8'));errors=[]
    for r in rows:
        p=base/r['path']
        if not p.exists() or p.stat().st_size!=r['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=r['sha256']:errors.append(r['path'])
    checks[key]={'files':len(rows),'source_bytes':sum(r['bytes'] for r in rows),'errors':errors}
assert checks['trace_batch']['source_bytes']<=25*1024*1024
all_matches=json.loads((OUT/'frame_correspondence.json').read_text('utf-8'))
exact=[]
for row in all_matches:
    ep=row['robopulse_episode'];video=OUT/f"{row['source_task']}_{row['source_episode'].split('_')[-1]}_cam_high.mp4"
    indices=[r['source_video_frame_index'] for r in row['frame_matches']]
    expr='+'.join(f'eq(n\\,{j})' for j in indices)
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(video),'-vf','select='+expr,'-fps_mode','passthrough','-f','rawvideo','-pix_fmt','rgb24','-'])
    arrays=np.frombuffer(raw,dtype=np.uint8).reshape(-1,480,640,3)
    assert len(arrays)==len(indices)
    vals=[]
    for a,r in zip(arrays,row['frame_matches']):
        b=np.array(Image.open(ROOT/f"images/ep{ep}/{r['published_logical_frame']:03d}_view1.png").convert('RGB'))
        vals.append({'logical_frame':r['published_logical_frame'],'source_frame':r['source_video_frame_index'],'pixel_exact':bool(np.array_equal(a,b)),'decoded_rgb_sha256':hashlib.sha256(a.tobytes()).hexdigest()})
    exact.append({'episode':ep,'all_pixels_exact':all(r['pixel_exact'] for r in vals),'frames':vals})
save('exact_pixel_correspondence.json',exact)
checks['all_59_published_frames_pixel_exact']=all(x['all_pixels_exact'] for x in exact)
selected=json.loads((OUT/'selected_lerobot_annotations.json').read_text('utf-8'))
times=[]
for r in selected:
    ep=618 if r['episode_index']==5060 else 621
    a=json.loads((OUT/f'ep{ep}_source_annotation.json').read_text('utf-8'))['annotation']
    d=json.loads((OUT/f"lerobot_{r['episode_index']}_time_flags.json").read_text('utf-8'))
    flags=d['complementary_info.vifailback_flags'];n=r['num_frames']
    times.append({'episode':ep,'lerobot_episode':r['episode_index'],'source_annotation_exact':r['annotation']==a,'num_frames':n,'frame_index_contiguous':d['frame_index']==list(range(n)),'max_timestamp_error_vs_n_over_25':max(abs(t-i/25) for i,t in enumerate(d['timestamp'])),'task_index_values':sorted(set(d['task_index'])),'avoid_indices':[i for i,f in enumerate(flags) if f[1]],'correct_indices':[i for i,f in enumerate(flags) if f[2]],'hardware_clock_verified':False})
save('time_and_annotation_audit.json',times)
checks['time_annotations']=times
checks['no_independent_review']=True
save('verification_summary.json',checks)
assert not checks['previous_batch']['errors'] and not checks['trace_batch']['errors']
assert checks['all_59_published_frames_pixel_exact']
assert all(t['source_annotation_exact'] and t['frame_index_contiguous'] and t['max_timestamp_error_vs_n_over_25']<1e-6 for t in times)
print(json.dumps(checks,indent=2))

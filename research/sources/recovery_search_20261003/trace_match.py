"""Exhaustive local frame correspondence for the two preselected source videos."""
import json, subprocess, hashlib
import numpy as np
from PIL import Image, ImageDraw
from trace_sources import ROOT, OUT, save
matches=[]
for rp,task,ep in [(618,'stack_three_color_cubes_ep1',58),(621,'stack_three_color_cubes_ep2',36)]:
    video=OUT/f'{task}_{ep}_cam_high.mp4'
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]))
    save(f'ep{rp}_ffprobe.json',probe)
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(video),'-vf','scale=160:120','-f','rawvideo','-pix_fmt','rgb24','-'])
    frames=np.frombuffer(raw,dtype=np.uint8).reshape(-1,120,160,3).astype(np.float32)
    result=[]
    for path in sorted((ROOT/f'images/ep{rp}').glob('*_view1.png')):
        a=np.asarray(Image.open(path).convert('RGB').resize((160,120),Image.Resampling.BICUBIC),dtype=np.float32)
        dif=np.abs(frames-a).mean(axis=(1,2,3)); rank=np.argsort(dif)
        j=int(rank[0])
        result.append(dict(published_logical_frame=int(path.name.split('_')[0]),source_video_frame_index=j,source_playback_seconds=j/25,mean_absolute_rgb_error_160x120=float(dif[j]),second_best_index=int(rank[1]),second_best_error=float(dif[rank[1]])))
    annotations=json.loads((ROOT/f'{task}_annotations.json').read_text('utf-8'))
    ai,r=next((i,r) for i,r in enumerate(annotations) if r['video'].endswith(f'/episode_{ep}_cam_high.mp4'))
    save(f'ep{rp}_source_annotation.json',dict(annotation_file=f'{task}_annotations.json',annotation_array_index=ai,source_index_present='source_index' in r,annotation=r))
    matches.append(dict(robopulse_episode=rp,source_task=task,source_episode=f'episode_{ep}',source_video=r['video'],source_num_frames=len(frames),frame_matches=result,method='All published view1 frames compared against every decoded source frame using RGB mean absolute error at 160x120; image verification required',robot_time_verified=False))
    # Original-resolution side-by-side at several times, including final evidence.
    choices=[0,12,18,23,len(result)-2,len(result)-1] if rp==621 else [0,11,16,21,27,29]
    canvas=Image.new('RGB',(640,len(choices)*265),'white');draw=ImageDraw.Draw(canvas)
    for row,k in enumerate(choices):
        j=result[k]['source_video_frame_index']
        target=OUT/f'frames/ep{rp}_source_{j:04d}.png';target.parent.mkdir(exist_ok=True)
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(video),'-vf',f'select=eq(n\\,{j})','-frames:v','1',str(target)],check=True)
        for col,path in enumerate([ROOT/f'images/ep{rp}/{k:03d}_view1.png',target]):
            im=Image.open(path);im.thumbnail((320,240));canvas.paste(im,(col*320,row*265+25))
        draw.text((0,row*265),f'RoboPulse ep{rp} logical {k} | upstream frame {j}, playback {j/25:.2f}s',fill='black')
    canvas.save(OUT/f'ep{rp}_multi_time_match.jpg')
save('frame_correspondence.json',matches)
print(json.dumps([{k:v for k,v in x.items() if k!='frame_matches'}|{'indices':[r['source_video_frame_index'] for r in x['frame_matches']],'mae_range':[min(r['mean_absolute_rgb_error_160x120'] for r in x['frame_matches']),max(r['mean_absolute_rgb_error_160x120'] for r in x['frame_matches'])]} for x in matches],indent=2))

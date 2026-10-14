"""Reference and P0 visual materials from pinned upstream media; no labels in online tracks."""
import json,subprocess,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
from trace_sources import ROOT,OUT,save
def extract(video,j,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():subprocess.run(['ffmpeg','-v','error','-y','-i',str(video),'-vf',f'select=eq(n\\,{j})','-frames:v','1',str(path)],check=True)
def contact(paths,labels,dest,cols=4,size=(320,240)):
    w,h=size;c=Image.new('RGB',(w*cols,(h+24)*((len(paths)+cols-1)//cols)),'white');d=ImageDraw.Draw(c)
    for i,(p,label) in enumerate(zip(paths,labels)):
        im=Image.open(p).convert('RGB').resize(size,Image.Resampling.BICUBIC);x=i%cols*w;y=i//cols*(h+24);c.paste(im,(x,y+24));d.text((x,y),label,fill='black')
    c.save(dest)
for rp,task,ep,last in [(618,'stack_three_color_cubes_ep1',58,375),(621,'stack_three_color_cubes_ep2',36,360)]:
    video=OUT/f'{task}_{ep}_cam_high.mp4'
    rows=[]
    for q in range(last//25+1):
        path=OUT/f'p0/ep{rp}/frame_{q:02d}.png';extract(video,q*25,path)
        # Store the exact 256 square pixels seen by the model.
        with Image.open(path) as im:small=im.convert('RGB').resize((256,256),Image.Resampling.BICUBIC)
        small.save(path)
        rows.append(dict(time=float(q),path=path.relative_to(Path.cwd()).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),source_frame_index=q*25))
    anno=json.loads((OUT/f'ep{rp}_source_annotation.json').read_text())['annotation']
    track=dict(trajectory_id=f'vifailback-{task}-{ep}',instruction_versions=[dict(version='upstream-task-v1',effective_at=0,text=anno['task'])],objects=['green_on_blue'],frames=[{k:v for k,v in r.items() if k!='source_frame_index'} for r in rows])
    save(f'p0/ep{rp}/online_track.json',track)
    save(f'p0/ep{rp}/frame_provenance.json',rows)
    contact([OUT/f'p0/ep{rp}/frame_{q:02d}.png' for q in range(last//25+1)],[f'ep{rp} q={q}s source n={q*25}' for q in range(last//25+1)],OUT/f'ep{rp}_P0_contact.jpg',size=(256,256))
    packets=[]
    for q in range(last//25+1):
        indices=list(dict.fromkeys([q,0,max(0,q-1),max(0,q-5)]))
        packets.append(dict(tick=q,frame_times=indices,frame_sha256=[rows[k]['sha256'] for k in indices]))
    save(f'p0/ep{rp}/packet_manifest.json',packets)
    ns=list(range(275,last+1,5)) if rp==621 else [125,150,200,250,300,350,375]
    ps=[]
    for j in ns:
        p=OUT/f'reference/ep{rp}_high_{j:04d}.png';extract(video,j,p);ps.append(p)
    contact(ps,[f'ep{rp} high n={j} t={j/25:.2f}' for j in ns],OUT/f'ep{rp}_reference_contact.jpg')
wrist=OUT/'lerobot_5197_right.mp4'
save('ep621_right_ffprobe.json',json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(wrist)])))
ns=[0,175,225,275,290,300,310,320,325,330,335,340,345,350,355,360];ps=[]
for j in ns:
    p=OUT/f'reference/ep621_right_{j:04d}.png';extract(wrist,j,p);ps.append(p)
contact(ps,[f'REF ONLY wrist n={j} t={j/25:.2f}' for j in ns],OUT/'ep621_right_reference_contact.jpg')
print('Reference contacts and P0 frames prepared; no model run.')

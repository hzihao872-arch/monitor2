from pathlib import Path
import json,subprocess,hashlib
from PIL import Image,ImageDraw
OUT=Path(__file__).resolve().parent
clips=json.loads((OUT/'clip_registry.json').read_text('utf-8'))
ix=[0,8,16,24,32,40,48,63]
sheet=Image.new('RGB',(8*320,7*270),'white');d=ImageDraw.Draw(sheet);derived=[]
for row,c in enumerate(clips):
 p=OUT/c['file_name'];folder=OUT/p.stem;folder.mkdir(exist_ok=True)
 for col,n in enumerate(ix):
  f=folder/f'frame_{n:03d}.png'
  if not f.exists():subprocess.run(['ffmpeg','-v','error','-i',str(p),'-vf',f'select=eq(n\\,{n})','-frames:v','1',str(f)],check=True)
  sheet.paste(Image.open(f).convert('RGB'),(col*320,row*270+30))
  d.text((col*320+3,row*270+3),f'{p.stem[-6:]} {c["quality_label"]} f{n} {n/30:.3f}s',fill='black')
  derived.append(dict(path=f.relative_to(OUT).as_posix(),source=c['file_name'],frame=n,playback_seconds=n/30,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
sheet.save(OUT/'pencil_case_overview.jpg')
(OUT/'derived_frames.json').write_text(json.dumps(derived,indent=2)+'\n','utf-8')
print('56 selected source frames from all 7 task clips; not independent episodes')

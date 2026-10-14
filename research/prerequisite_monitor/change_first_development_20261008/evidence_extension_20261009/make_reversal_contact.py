import json,pathlib,sys
from PIL import Image,ImageDraw
H=pathlib.Path(__file__).resolve().parent;B=H.parent/'atomic_state_20261009/source_core/model_input/pilot_v5';ids=['q07108c1875aa88b5','qbb0dbd57d63ce6a9'];times=[0,3,5,7,9,11,14]
canvas=Image.new('RGB',(7*300,2*250),'white');draw=ImageDraw.Draw(canvas)
for row,qid in enumerate(ids):
 manifest=json.loads((B/qid/'manifest.json').read_text());frames={f['time_ms']//1000:f for f in manifest['frames']}
 for col,t in enumerate(times):
  im=Image.open(B/qid/frames[t]['path']).convert('RGB');im.thumbnail((300,218));canvas.paste(im,(col*300,row*250+25));draw.text((col*300+3,row*250+3),f'{qid} t={t}s',fill='black')
canvas.save(H/'reversal_contact.png');print(str(H/'reversal_contact.png'))

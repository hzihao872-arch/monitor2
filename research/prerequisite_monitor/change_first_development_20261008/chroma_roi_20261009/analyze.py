import io,json,pathlib,sys,hashlib
from PIL import Image,ImageDraw
H=pathlib.Path(__file__).resolve().parent;B=H.parent;sys.path.insert(0,str(H));from selector import propose
import cv2,numpy as np
root=H/'remote_verified/run'
if not root.exists():root=H/'local_recovered/run'
rows=[json.loads(p.read_text()) for p in (root/'results').glob('*.json')];text=[];summary={'n':len(rows),'strict_valid':sum(r['validation']['valid'] for r in rows),'crop_audits':[],'archive_status':'partial local recovery; full remote archive NOT verified' if 'local_recovered' in root.parts else 'remote verified'};cells=[]
for r in sorted(rows,key=lambda r:r['query_id']):
 req=r['request'];q=req['query_id'];pkg=B/'atomic_state_20261009/source_core/model_input/pilot_v5'/q;manifest=json.loads((pkg/'manifest.json').read_text());full=manifest['frames'];frames=[cv2.cvtColor(cv2.imdecode(np.frombuffer((pkg/f['path']).read_bytes(),np.uint8),cv2.IMREAD_COLOR),cv2.COLOR_BGR2RGB) for f in full];expected=propose(frames,[f['time_ms'] for f in full]);assert expected==req['automatic_roi_proposals'];summary['crop_audits'].append({'query':q,'deterministic_proposals_replayed':True,'crop_count':len(req['automatic_crop_registry']),'proposals':expected})
 text.extend(['## '+q,'valid='+str(r['validation']['valid'])])
 if r['validation']['valid']:
  for c in r['validation']['payload']['changes']:text.append(f"{c['b']}→{c['a']} {c['object']}: {c['before']} → {c['after']}")
 else:text.append(r['raw'])
 for j,e in enumerate(expected):
  for side,key in [('b','before_index'),('a','after_index')]:
   im=Image.fromarray(frames[e[key]]);draw=ImageDraw.Draw(im);draw.rectangle(e['bbox_xyxy'],outline='red',width=3);im.thumbnail((256,192));cell=Image.new('RGB',(256,215),'white');cell.paste(im,(0,20));ImageDraw.Draw(cell).text((2,2),q[-8:]+f' roi{j}{side} f{e[key]}',fill='black');cells.append(cell)
summary['local_opencv']=cv2.__version__;summary['semantic_status']='Automatic chroma change can include shadows/occlusion and cannot certify true object motion or attachment; exposed development, no blind accuracy.'
(H/'ANALYSIS.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');(H/'RAW_COMPARISON_zh.md').write_text('\n\n'.join(text),encoding='utf-8')
if cells:
 canvas=Image.new('RGB',(256*4,215*((len(cells)+3)//4)),'white')
 for i,cell in enumerate(cells):canvas.paste(cell,((i%4)*256,(i//4)*215))
 canvas.save(H/'ROI_CONTACT.png')
print(json.dumps(summary,indent=2));print('\n'.join(text))

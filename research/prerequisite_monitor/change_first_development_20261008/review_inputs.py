"""Private CPU contact sheets and target-blind candidate audit for exposed clips."""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image,ImageDraw

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments.prerequisite_probe.change_first_monitor.sampling import sample


def audit(inventory, output):
    rows=json.loads(Path(inventory).read_text(encoding='utf-8'))['clips']
    root=Path(output)
    if root.exists():raise FileExistsError(root)
    root.mkdir(parents=True)
    result=[]
    for family in sorted(set(x['family'] for x in rows)):
        tiles=[]
        for row in sorted((r for r in rows if r['family']==family),key=lambda r:r['condition']):
            cap=cv2.VideoCapture(row['source']); frames=[]
            for _ in range(15):
                ok,bgr=cap.read()
                if not ok:raise ValueError('missing expected frame')
                frames.append(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB))
            cap.release()
            p=sample(frames,[i*1000 for i in range(15)])
            result.append({'family':family,'condition':row['condition'],'source_sha256':row['source_sha256'],
                           'candidate_intervals_ms':[[e['before_index']*1000,e['after_index']*1000] for e in p['candidates']],
                           'selected_ms':p['times_ms'],'overflow':p['overflow']})
            picks=[0]+[e['after_index'] for e in p['candidates'][:2]]+[14]
            strip=Image.new('RGB',(4*256,212),'white'); draw=ImageDraw.Draw(strip)
            for col,index in enumerate(picks):
                im=Image.fromarray(frames[index]).resize((256,192))
                strip.paste(im,(col*256,20))
                draw.text((col*256+3,3),f'{row["condition"]}  t={index}',fill='black')
            tiles.append(strip)
        sheet=Image.new('RGB',(1024,212*len(tiles)),'white')
        for i,t in enumerate(tiles):sheet.paste(t,(0,i*212))
        sheet.save(root/(family+'_contact.png'))
    (root/'candidate_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inventory',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();print(len(audit(a.inventory,a.output)),'CPU-only audit rows')

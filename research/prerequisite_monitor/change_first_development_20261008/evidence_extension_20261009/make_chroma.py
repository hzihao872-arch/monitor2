import pathlib,json,hashlib,zipfile
H=pathlib.Path(__file__).resolve().parent;B=H.parent;S=B/'dense_discovery_20261009';D=B/'chroma_roi_20261009';D.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cfg=json.loads((S/'config.json').read_text());cfg['parent']={'path':'/root/autodl-tmp/monitor2/fresh_prerequisite_runs/change_first_cross_fact_20261009_v1/run/requests.jsonl','sha256':sha(B/'cross_fact_20261009/remote_verified/run/requests.jsonl')};cfg['protocol']='Goal-blind automatic HSV saturation/chromatic RGB difference ROI proposals, fixed thresholds and temporal diversity; same dense prompt and all15 fullframes plus <=4 model-focus crops from selected legal past pairs. No manually picked region or goal/label. More visual tokens, not equal compute. Saturation can include wood, shadows and occlusion; does not certify physical motion or object identity. Parent cross47, prior602.'
(D/'config.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8');(D/'contracts.py').write_bytes((S/'contracts.py').read_bytes())
selector='''import cv2,numpy as np
def propose(frames,times):
 if len(frames)!=len(times) or any(b<=a for a,b in zip(times,times[1:])):raise ValueError('times')
 if not frames:return []
 if any(f.shape!=frames[0].shape for f in frames):raise ValueError('shapes')
 hsv=[cv2.cvtColor(f,cv2.COLOR_RGB2HSV) for f in frames];edges=[]
 for i in range(1,len(frames)):
  chroma=((hsv[i-1][:,:,1]>=60)&(hsv[i-1][:,:,2]>40))|((hsv[i][:,:,1]>=60)&(hsv[i][:,:,2]>40))
  delta=np.max(np.abs(frames[i].astype(np.int16)-frames[i-1].astype(np.int16)),axis=2)>30
  mask=cv2.morphologyEx((chroma&delta).astype(np.uint8),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
  n,labels,stats,centroids=cv2.connectedComponentsWithStats(mask,8)
  for stat in stats[1:]:
   x,y,w,h,area=map(int,stat)
   if area<30:continue
   pad=max(16,round(max(w,h)*.8));height,width=frames[0].shape[:2];box=[max(0,x-pad),max(0,y-pad),min(width,x+w+pad),min(height,y+h+pad)]
   edges.append({'before_index':i-1,'after_index':i,'score':area,'bbox_xyxy':box})
 chosen=[]
 for e in sorted(edges,key=lambda e:(-e['score'],e['after_index'],e['bbox_xyxy'])):
  if all(abs(e['after_index']-q['after_index'])>1 for q in chosen):chosen.append(e)
  if len(chosen)==2:break
 return sorted(chosen,key=lambda e:e['after_index'])
def crop(frame,box):
 x1,y1,x2,y2=box;roi=frame[y1:y2,x1:x2];h,w=roi.shape[:2];scale=min(1.,224/max(h,w));roi=cv2.resize(roi,(max(1,round(w*scale)),max(1,round(h*scale))),interpolation=cv2.INTER_AREA)
 ok,enc=cv2.imencode('.png',cv2.cvtColor(roi,cv2.COLOR_RGB2BGR))
 if not ok:raise ValueError('encode')
 return enc.tobytes()
'''
(D/'selector.py').write_text(selector,encoding='utf-8')
t=(S/'dense_runner.py').read_text().replace('dense_runner.py','chroma_runner.py').replace("'contracts.py')","'contracts.py','selector.py')").replace("'prefix_sampling_20261009/download/run/requests.jsonl'","'cross_fact_20261009/remote_verified/run/requests.jsonl'").replace("!=24:raise RuntimeError('parent changed')","!=47:raise RuntimeError('parent changed')").replace("'dense_discovery_v1'","'chroma_roi_v1'").replace("'arm':'dense_full15'","'arm':'full15_chroma_rois'").replace("'parent_issued':228","'parent_issued':602").replace("'parent':228,'total':228+ledger.issued_count","'parent':602,'total':602+ledger.issued_count").replace("'limits':[5000,768]","'limits':[6500,768]")
t=t.replace("pixels=[pkg.read(i,'V1') for i in ids];times={i:pkg.handles[i]['time_ms'] for i in ids};prompt=",'''pixels=[pkg.read(i,'V1') for i in ids];times={i:pkg.handles[i]['time_ms'] for i in ids}
   import cv2,numpy as np
   from selector import propose,crop
   rgb=[cv2.cvtColor(cv2.imdecode(np.frombuffer(p,np.uint8),cv2.IMREAD_COLOR),cv2.COLOR_BGR2RGB) for p in pixels];proposals=propose(rgb,[times[i] for i in ids]);crop_records=[]
   for j,e in enumerate(proposals):
    for side,key in [('b','before_index'),('a','after_index')]:
     index=e[key];parent_id=f'f{index:04}';cid=f'auto{j}{side}';data=crop(rgb[index],e['bbox_xyxy']);record={'time_ms':times[parent_id],'parent_id':parent_id,'crop_xyxy':e['bbox_xyxy'],'crop_origin':'automatic goal-blind chroma motion v1','sha256':hashlib.sha256(data).hexdigest()};ids.append(cid);pixels.append(data);times[cid]=record['time_ms'];handles[cid]=record;crop_records.append(dict(record,id=cid));dst_crop=root/'crops'/f'{item["query_id"]}_{cid}.png';dst_crop.parent.mkdir(exist_ok=True);dst_crop.write_bytes(data)
   prompt=''')
t=t.replace("'image_meta':[{'time_ms':times[i]} for i in ids]","'image_meta':[{k:handles[i][k] for k in ('time_ms','parent_id','crop_xyxy','crop_origin') if k in handles[i]} for i in ids]")
t=t.replace("'baseline_source_sha256':item['baseline_sha256']","'baseline_source_sha256':item['baseline_sha256'],'automatic_crop_registry':crop_records,'automatic_roi_proposals':proposals")
# Existing adapter labels registered crop parent and coordinates via image_meta.
(D/'chroma_runner.py').write_text(t,encoding='utf-8');(D/'test_selector.py').write_text("import numpy as np\nfrom selector import propose,crop\na=np.full((80,100,3),128,np.uint8);b=a.copy();b[30:45,40:65]=[255,100,0];p=propose([a,b],[0,1000]);assert len(p)==1 and p[0]['after_index']==1;box=p[0]['bbox_xyxy'];assert 0<=box[0]<40<65<=box[2]<=100;assert crop(b,box).startswith(b'\\x89PNG');assert propose([a,a],[0,1000])==[]\nc=a.copy();c[30:45,40:65]=[255,255,255];assert propose([a,c],[0,1000])==[]\nprint('chromatic-change, static, grayscale exclusion, and parent-box encoding tests passed')\n",encoding='utf-8')
(D/'freeze.json').write_text(json.dumps({'files':{n:sha(D/n) for n in ('config.json','chroma_runner.py','contracts.py','selector.py')}},indent=2),encoding='utf-8')
with zipfile.ZipFile(D/'chroma_v1.zip','w') as z:
 for n in ('config.json','freeze.json','chroma_runner.py','contracts.py','selector.py','test_selector.py'):z.write(D/n,n)
t=(B/'inventory_binding_20261009/remote_ops.py').read_text().replace('change_first_inventory_binding_20261009_v1','change_first_chroma_roi_20261009_v1').replace('inventory_v1.zip','chroma_v1.zip').replace('inventory_runner.py','chroma_runner.py').replace('test_inventory.py','test_selector.py').replace('inventory_FINAL.tar.gz','chroma_FINAL.tar.gz');(D/'remote_ops.py').write_text(t,encoding='utf-8');t=(B/'inventory_binding_20261009/seal_remote.py').read_text().replace('inventory_runner.py','chroma_runner.py').replace('inventory_FINAL.tar.gz','chroma_FINAL.tar.gz');(D/'seal_remote.py').write_text(t,encoding='utf-8');print(sha(D/'chroma_v1.zip'))

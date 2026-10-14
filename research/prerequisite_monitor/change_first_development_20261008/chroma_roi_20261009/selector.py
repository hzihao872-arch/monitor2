import cv2,numpy as np
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

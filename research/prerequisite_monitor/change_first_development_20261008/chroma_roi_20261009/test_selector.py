import numpy as np
from selector import propose,crop
a=np.full((80,100,3),128,np.uint8);b=a.copy();b[30:45,40:65]=[255,100,0];p=propose([a,b],[0,1000]);assert len(p)==1 and p[0]['after_index']==1;box=p[0]['bbox_xyxy'];assert 0<=box[0]<40<65<=box[2]<=100;assert crop(b,box).startswith(b'\x89PNG');assert propose([a,a],[0,1000])==[]
c=a.copy();c[30:45,40:65]=[255,255,255];assert propose([a,c],[0,1000])==[]
print('chromatic-change, static, grayscale exclusion, and parent-box encoding tests passed')

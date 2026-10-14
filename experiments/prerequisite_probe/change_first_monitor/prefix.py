"""Materialized RGB prefixes. The inference side never opens source videos."""
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np


def digest(data):
    return hashlib.sha256(data).hexdigest()


def materialize_frames(frames, as_of_ms, output, fps=1, times_ms=None):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(output)
    output.mkdir(parents=True, exist_ok=True)
    records = []
    kept = []
    if times_ms is not None and (len(times_ms)!=len(frames) or any(b<=a for a,b in zip(times_ms,times_ms[1:]))):
        raise ValueError('timestamps must be strictly increasing and aligned')
    for i, frame in enumerate(frames):
        ms = times_ms[i] if times_ms is not None else round(i * 1000 / fps)
        if ms > as_of_ms:
            break
        if frame is None:
            raise ValueError('missing frame')
        rgb = np.asarray(frame, dtype=np.uint8)
        if rgb.ndim != 3 or rgb.shape[2] != 3:
            raise ValueError('RGB required')
        scale = min(1.0, 512/rgb.shape[1], 384/rgb.shape[0])
        if scale < 1:
            rgb = cv2.resize(rgb, (max(1,round(rgb.shape[1]*scale)),max(1,round(rgb.shape[0]*scale))),
                             interpolation=cv2.INTER_AREA)
        name = f'frames/{i:04d}.png'
        (output / 'frames').mkdir(exist_ok=True)
        ok, encoded = cv2.imencode('.png', cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        if not ok:
            raise ValueError('PNG encode failed')
        data = encoded.tobytes()
        (output / name).write_bytes(data)
        records.append({'evidence_id': f'f{i:04d}', 'time_ms': ms, 'path': name,
                        'sha256': digest(data), 'width': rgb.shape[1], 'height': rgb.shape[0]})
        kept.append(rgb)
    if not records:
        raise ValueError('empty prefix')
    from .sampling import sample
    proposal=sample(kept,[r['time_ms'] for r in records])
    crops=[]
    for j,candidate in enumerate(proposal['candidates'][:2]):
        before_index=candidate['stable_before_index'] if candidate['stable_before_index'] is not None else candidate['before_index']
        after_index=candidate['stable_after_index'] if candidate['stable_after_index'] is not None else candidate['after_index']
        for side,index in (('before',before_index),('after',after_index)):
            x1,y1,x2,y2=candidate['bbox_xyxy']
            h,w=kept[index].shape[:2]
            pad=max(8,int(max(x2-x1,y2-y1)*.4))
            box=[max(0,x1-pad),max(0,y1-pad),min(w,x2+pad),min(h,y2+pad)]
            if box[0]>=box[2] or box[1]>=box[3]:
                continue
            crop=cv2.resize(kept[index][box[1]:box[3],box[0]:box[2]],(256,256),interpolation=cv2.INTER_AREA)
            ok,encoded=cv2.imencode('.png',cv2.cvtColor(crop,cv2.COLOR_RGB2BGR))
            if not ok:raise ValueError('crop encode failed')
            cid=f'c{j}{side[0]}'
            name=f'crops/{cid}.png'
            (output/'crops').mkdir(exist_ok=True)
            data=encoded.tobytes(); (output/name).write_bytes(data)
            crops.append({'evidence_id':cid,'time_ms':records[index]['time_ms'],'path':name,'sha256':digest(data),
                          'width':256,'height':256,'parent_id':records[index]['evidence_id'],'crop_xyxy':box})
    signature = digest(json.dumps([(r['time_ms'], r['sha256']) for r in records+crops], separators=(',', ':')).encode())
    manifest = {'as_of_ms': as_of_ms, 'fps': fps, 'frames': records, 'crops': crops,
                'proposal':proposal,'signature': signature}
    (output / 'manifest.json').write_text(json.dumps(manifest, sort_keys=True, indent=2), encoding='utf-8')
    return manifest


class PrefixPackage:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.manifest = json.loads((self.root / 'manifest.json').read_text(encoding='utf-8'))
        self.handles = {r['evidence_id']: r for r in self.manifest['frames']+self.manifest.get('crops',[])}
        if len(self.handles) != len(self.manifest['frames']+self.manifest.get('crops',[])):
            raise ValueError('duplicate evidence ID')
        self.accesses = []
        for r in self.manifest['frames']+self.manifest.get('crops',[]):
            if r['time_ms'] > self.manifest['as_of_ms']:
                raise ValueError('future evidence')
            self._verified_path(r)

    def _verified_path(self, record):
        p = (self.root / record['path']).resolve()
        if not p.is_relative_to(self.root) or not p.is_file():
            raise ValueError('unregistered or escaping path')
        if digest(p.read_bytes()) != record['sha256']:
            raise ValueError('pixel hash mismatch')
        return p

    def read(self, evidence_id, phase):
        if evidence_id not in self.handles or phase not in ('V1', 'V3'):
            raise ValueError('unknown evidence handle or phase')
        r = self.handles[evidence_id]
        data = self._verified_path(r).read_bytes()
        self.accesses.append({'phase': phase, 'evidence_id': evidence_id, 'time_ms': r['time_ms'],
                              'as_of_ms':self.manifest['as_of_ms'],
                              'sha256': digest(data), 'parent_id':r.get('parent_id'), 'crop_xyxy':r.get('crop_xyxy')})
        return data

    def all_ids(self):
        return [r['evidence_id'] for r in self.manifest['frames']]

    def all_evidence_ids(self):
        return list(self.handles)

    def shared_ids(self, max_full=8):
        ids = self.all_ids()
        proposal=self.manifest['proposal']
        full=[ids[i] for i in proposal['selected_indices'][:max_full]]
        return full+[r['evidence_id'] for r in self.manifest.get('crops',[])[:4]],proposal

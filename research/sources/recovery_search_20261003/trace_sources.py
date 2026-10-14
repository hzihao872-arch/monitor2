"""Bounded, logged source tracing. No model calls; reuse saved inputs."""
import json, pathlib, hashlib, requests, sys
ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / 'upstream_trace'
OUT.mkdir(exist_ok=True)
MANIFEST = OUT / 'fetch_manifest.json'
REV = '21df46c2585c52e5a62df5f4b946bae6cbc6fed7'
LREV = '619791b94f61667333fe179d471051e0bca0e06f'
def save(name, data):
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def fetch(url, name, purpose, expected=None, cap=5_000_000):
    p = OUT / name
    entries = json.loads(MANIFEST.read_text('utf-8')) if MANIFEST.exists() else []
    if p.exists(): return p
    h = requests.head(url, allow_redirects=True, timeout=40)
    h.raise_for_status()
    advertised = h.headers.get('content-length')
    size = expected if expected is not None else int(advertised) if advertised else None
    if size is not None and size > cap: raise ValueError(('size exceeds cap',name,size,cap))
    remaining = 25*1024*1024-sum(e['bytes'] for e in entries)
    if size is not None and size > remaining: raise ValueError('batch budget exceeded')
    r = requests.get(url, stream=True, timeout=60)
    r.raise_for_status()
    data=bytearray()
    for c in r.iter_content(65536):
        data.extend(c)
        if len(data)>min(cap,remaining): raise ValueError('stream cap exceeded')
    if expected is not None and len(data)!=expected: raise ValueError(('size mismatch',name,len(data),expected))
    p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data)
    entries.append(dict(url=url,path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),purpose=purpose,head_status=h.status_code,head_content_length=advertised,expected_bytes=expected,holdout_eligible=False))
    save('fetch_manifest.json',entries)
    print(name,len(data),flush=True)
    return p
def source(path,name,purpose,expected=None):
    return fetch(f'https://huggingface.co/datasets/sii-rhos-ai/ViFailback-Dataset/resolve/{REV}/{path}',name,purpose,expected)
def fetch_range(url,name,start,end,total,purpose):
    p=OUT/name
    if p.exists(): return p
    entries=json.loads(MANIFEST.read_text('utf-8'))
    if sum(e['bytes'] for e in entries)+end-start+1>25*1024*1024: raise ValueError('batch budget exceeded')
    r=requests.get(url,headers={'Range':f'bytes={start}-{end}'},stream=True,timeout=45)
    if r.status_code!=206:
        r.close();raise ValueError(('range not honored; body not consumed',r.status_code))
    if r.headers.get('content-range')!=f'bytes {start}-{end}/{total}':
        r.close();raise ValueError('unexpected range')
    data=r.raw.read(end-start+2)
    if len(data)!=end-start+1: raise ValueError('range size mismatch')
    p.write_bytes(data)
    entries.append(dict(url=url,path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),purpose=purpose,http_status=206,content_range=r.headers['content-range'],whole_file_bytes=total,whole_file_downloaded=False,holdout_eligible=False))
    save('fetch_manifest.json',entries);print(name,len(data),flush=True)
    return p
def tree(path,name,lerobot=False):
    repo='sii-rhos-ai/vifailback-dataset-lerobot' if lerobot else 'sii-rhos-ai/ViFailback-Dataset'
    rev=LREV if lerobot else REV
    return fetch(f'https://huggingface.co/api/datasets/{repo}/tree/{rev}/{path}?limit=1000',name,'Pinned directory metadata',cap=2_000_000)
if __name__=='__main__':
    save('batch_scope.json',dict(date='2026-10-03',max_saved_source_bytes=25*1024*1024,scope='Two stacking-task directory metadata, selective source frames, then matched episode videos and synchronization metadata only; no full dataset',model_run=False))
    for n in ['stack_three_color_cubes_ep1','stack_three_color_cubes_ep2']:
        tree('annotated_data/'+n+'/videos',n+'_videos_tree.json')
    for n,size in [('episodes.jsonl',943651),('tasks.jsonl',12738),('info.json',7427)]:
        fetch(f'https://huggingface.co/datasets/sii-rhos-ai/vifailback-dataset-lerobot/resolve/{LREV}/meta/{n}','lerobot_'+n,'Episode lengths, task and encoded time metadata',size)

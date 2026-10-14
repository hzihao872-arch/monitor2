"""Bounded primary-source audit, no model execution. Run from D:/monitor2."""
from pathlib import Path
import json, hashlib, requests, sys
from datetime import datetime, timezone

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
CAP = 6 * 1024 * 1024
REV = 'abcb94c1e924282c0005e53cff0b22a073de748a'

def save(name, data):
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def fetch(url, name, revision, expected=None, expected_sha=None, limit=2*1024*1024):
    p=OUT/name
    if p.exists(): return p
    mf=OUT/'fetch_manifest.json'
    records=json.loads(mf.read_text('utf-8')) if mf.exists() else []
    remaining=CAP-sum(r.get('bytes',0) for r in records)
    h=requests.head(url,allow_redirects=True,timeout=30)
    h.raise_for_status()
    advertised=h.headers.get('content-length')
    known=expected if expected is not None else int(advertised) if advertised else None
    if known is not None and known>min(limit,remaining): raise ValueError(('size cap',name,known))
    # API responses may omit length: bounded stream, never fetch a large archive.
    r=requests.get(url,stream=True,timeout=30);r.raise_for_status()
    data=bytearray()
    for c in r.iter_content(65536):
        data.extend(c)
        if len(data)>min(limit,remaining): r.close();raise ValueError(('stream cap',name))
    sha=hashlib.sha256(data).hexdigest()
    if expected is not None: assert len(data)==expected,(name,len(data),expected)
    if expected_sha: assert sha==expected_sha,(name,sha,expected_sha)
    p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    records.append(dict(url=url,path=name,revision=revision,bytes=len(data),sha256=sha,
        head_status=h.status_code,head_content_length=advertised,expected_bytes=expected,
        size_check='HEAD plus fixed-tree byte count' if expected else 'HEAD; bounded stream if length absent',
        retrieved_utc=datetime.now(timezone.utc).isoformat(),holdout_eligible=False))
    save('fetch_manifest.json',records)
    print(name,len(data),flush=True)
    return p

if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':
        paths=['research/status.md','research/decision_log.md','experiments/data_manifest.json',
            'experiments/run_ledger.csv','research/08_pilot_report.md','research/07_evaluation_protocol.md','experiments/config_stage7.json']
        if not (OUT/'before_edit.json').exists():
            records=[]
            for rel in paths:
                data=(ROOT/rel).read_bytes();p=OUT/'before'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
                records.append(dict(path=rel,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
            save('before_edit.json',records)
        save('scope.json',dict(date='2026-10-03',max_saved_source_bytes=CAP,
            scope='Reuse papers and snapshots; missing RoboMeter v2 HTML, ep510/513/514 fixed directory metadata and bounded view1 frames; optional exact scoring source. No weights/models/API inference.',
            source_priority='native task and labels before model output',models_run=0,
            inclusion='Keep all three preselected episodes irrespective of event presence. H-D requires earlier achieved persistent final outcome, later distinct subtask success, and observable loss. Keep retention/legal withdrawal/occlusion/repair as controls or missing, never infer from direction alone.',
            native_target='RoboPulse++ Rising/Falling under C.4; no per-condition scoring from scalar',
            output_mapping='absolute progress first difference then five-frame causal average then sign; zero and endpoints unresolved; do not invent a score',
            units='episode is independent material unit; frame labels are not independent tasks',
            holdout_eligible=False))
        fetch('https://arxiv.org/html/2603.02115v2','robometer_v2.html','arXiv:2603.02115v2')
        for ep in [510,513,514]:
            fetch(f'https://huggingface.co/api/datasets/lyy0715/RoboPulsePlusPlus/tree/{REV}/images/ep{ep}?limit=1000',f'ep{ep}_tree.json',REV,limit=100000)
    elif mode=='frames':
        for ep in [510,513,514]:
            rows=json.loads((OUT/f'ep{ep}_tree.json').read_text('utf-8'))
            for r in rows:
                selected = ep==513 or int(Path(r['path']).name.split('_')[0]) in ({0,5,10,16} if ep==510 else {0,6,12,19})
                if r['type']=='file' and r['path'].endswith('_view1.png') and selected:
                    fetch(f'https://huggingface.co/datasets/lyy0715/RoboPulsePlusPlus/resolve/{REV}/'+r['path'],r['path'],REV,r['size'],r.get('lfs',{}).get('oid'))

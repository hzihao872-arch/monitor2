"""Create a SHA-256 file manifest and downloadable tar for one immutable run."""
import argparse
import gzip
import hashlib
import io
import json
import tarfile
from pathlib import Path


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()


def seal(run,output):
    run=Path(run).resolve();output=Path(output).resolve()
    if not run.is_dir() or output.exists() or output.is_relative_to(run):
        raise ValueError('run absent or output already exists/inside run')
    files=sorted(p for p in run.rglob('*') if p.is_file() and p.name!='seal.json')
    rows={p.relative_to(run).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in files}
    manifest={'run_name':run.name,'files':rows,'complete_query_results':len(list((run/'results').glob('*.json')))}
    (run/'seal.json').write_text(json.dumps(manifest,indent=2,sort_keys=True),encoding='utf-8')
    output.parent.mkdir(parents=True,exist_ok=True)
    with tarfile.open(output,'w:gz') as tar:
        for p in files+[run/'seal.json']:
            tar.add(p,arcname=(Path(run.name)/p.relative_to(run)).as_posix(),recursive=False)
    return {'archive':str(output),'sha256':sha(output),'files':len(files)+1}


def verify_seal(archive,expected_sha256=None):
    errors=[]
    data=Path(archive).read_bytes()
    if expected_sha256 and hashlib.sha256(data).hexdigest()!=expected_sha256:
        errors.append('archive_sha256')
    try:
        gzip.decompress(data)  # rejects trailing garbage that tarfile can ignore
        with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as tar:
            names=tar.getnames()
            seals=[n for n in names if n.endswith('/seal.json')]
            if len(seals)!=1 or len(names)!=len(set(names)):
                errors.append('seal_member_set')
            else:
                manifest=json.load(tar.extractfile(seals[0]))
                root=manifest['run_name']+'/'
                expected={root+n for n in manifest['files']}|{root+'seal.json'}
                if set(names)!=expected:errors.append('file_member_set')
                for rel,info in manifest['files'].items():
                    member=tar.extractfile(root+rel)
                    if member is None:errors.append('missing:'+rel);continue
                    bytes_=member.read()
                    if hashlib.sha256(bytes_).hexdigest()!=info['sha256'] or len(bytes_)!=info['bytes']:
                        errors.append('hash:'+rel)
    except Exception as exc:
        errors.append(type(exc).__name__+':'+str(exc)[:200])
    return {'valid':not errors,'errors':errors,'archive_sha256':hashlib.sha256(data).hexdigest()}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run');p.add_argument('--output');p.add_argument('--verify')
    p.add_argument('--expected-sha256');a=p.parse_args()
    if a.verify:
        result=verify_seal(a.verify,a.expected_sha256);print(json.dumps(result));raise SystemExit(0 if result['valid'] else 1)
    if not a.run or not a.output:p.error('--run and --output required when sealing')
    print(json.dumps(seal(a.run,a.output)))

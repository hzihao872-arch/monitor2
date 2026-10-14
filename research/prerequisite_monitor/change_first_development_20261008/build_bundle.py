"""Build a positive-allowlist model-side ZIP with per-member hashes."""
import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

WORKSPACE=Path(__file__).resolve().parents[3]
CODE=Path('experiments/prerequisite_probe/change_first_monitor')
MODULES=('__init__.py','contracts.py','prefix.py','sampling.py','prompts.py','backends.py',
         'qwen_backend.py','pipeline.py','runner.py')
PROTOCOL=('input_contract.json','stage_schemas.json','capabilities.txt','default_budget.json','prompts_v1.json')
DEV=Path('research/prerequisite_monitor/change_first_development_20261008')
SERVER=('verify_bundle.py','server_preflight.py','run_server_pilot.sh','collect_and_seal.py')


def sha(data):return hashlib.sha256(data).hexdigest()


def build_bundle(input_dir,output):
    inp=Path(input_dir).resolve();output=Path(output)
    if output.exists():raise FileExistsError(output)
    queries=json.loads((inp/'queries.json').read_text(encoding='utf-8'))
    if set(queries)!={'scope','queries'} and set(queries)!={'queries'}:
        raise ValueError('unexpected query manifest fields')
    if not queries['queries'] or len(queries['queries'])>8:
        raise ValueError('pilot must contain 1–8 queries')
    files={}
    prefix=Path('model_input')/inp.name
    files[str(prefix/'queries.json').replace('\\','/')]=(inp/'queries.json').read_bytes()
    for q in queries['queries']:
        if set(q)!={'query_id','prefix_dir','goal','as_of_ms','prefix_signature'}:
            raise ValueError('unexpected query fields')
        qid=q['query_id']
        if q['prefix_dir']!=qid or not re.fullmatch(r'q[a-z0-9]+',qid):
            raise ValueError('invalid anonymous ID')
        root=inp/qid
        manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
        if set(manifest)!={'as_of_ms','fps','frames','crops','proposal','signature'}:
            raise ValueError('unexpected prefix manifest fields')
        proposal=manifest['proposal']
        if set(proposal)!={'selected_indices','candidates','overflow','times_ms','stable_indices','camera_uncertain'}:
            raise ValueError('unexpected proposal fields')
        if any(set(c)!={'before_index','after_index','score','bbox_xyxy','stable_before_index','stable_after_index'} for c in proposal['candidates']):
            raise ValueError('unexpected candidate fields')
        if manifest['as_of_ms']!=q['as_of_ms'] or manifest['signature']!=q['prefix_signature']:
            raise ValueError('prefix mismatch')
        rels=['manifest.json']
        for r in manifest['frames']+manifest.get('crops',[]):
            expected={'evidence_id','time_ms','path','sha256','width','height'}
            if r in manifest['crops']:
                expected|={'parent_id','crop_xyxy'}
            if set(r)!=expected:
                raise ValueError('unexpected evidence record fields')
            if r['time_ms']>q['as_of_ms'] or not re.fullmatch(r'(frames/\d{4}|crops/c\d[ab])\.png',r['path']):
                raise ValueError('future or unexpected image')
            image=root/r['path']
            if not image.resolve().is_relative_to(root.resolve()) or not image.is_file() or sha(image.read_bytes())!=r['sha256']:
                raise ValueError('image hash mismatch')
            rels.append(r['path'])
        if sha(json.dumps([(r['time_ms'],r['sha256']) for r in manifest['frames']+manifest['crops']],separators=(',',':')).encode())!=manifest['signature']:
            raise ValueError('invalid prefix signature')
        if set(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file())!=set(rels):
            raise ValueError('unexpected prefix file')
        for rel in rels:
            files[(prefix/qid/rel).as_posix()]=(root/rel).read_bytes()
    for name in MODULES:files[(CODE/name).as_posix()]=(WORKSPACE/CODE/name).read_bytes()
    for name in PROTOCOL:files[(CODE/'protocol'/name).as_posix()]=(WORKSPACE/CODE/'protocol'/name).read_bytes()
    for name in SERVER:files[(DEV/name).as_posix()]=(WORKSPACE/DEV/name).read_bytes()
    manifest={'version':'change-first-bundle-v1','input_name':inp.name,
              'members':{k:{'sha256':sha(v),'bytes':len(v)} for k,v in sorted(files.items())}}
    files['bundle_manifest.json']=(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode()
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo(name,date_time=(2026,10,8,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,data)
    return {'bundle':str(output),'sha256':sha(output.read_bytes()),'members':len(files)}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();print(json.dumps(build_bundle(a.input,a.output)))

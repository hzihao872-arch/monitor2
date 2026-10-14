"""Verify positive allowlist, every member hash, and prefix time/hash boundary."""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import PurePosixPath

CODE='experiments/prerequisite_probe/change_first_monitor/'
MODULES={'__init__.py','contracts.py','prefix.py','sampling.py','prompts.py','backends.py',
         'qwen_backend.py','pipeline.py','runner.py'}
PROTOCOL={'input_contract.json','stage_schemas.json','capabilities.txt','default_budget.json','prompts_v1.json'}
DEV='research/prerequisite_monitor/change_first_development_20261008/'
SERVER={'verify_bundle.py','server_preflight.py','run_server_pilot.sh','collect_and_seal.py'}

def sha(data):return hashlib.sha256(data).hexdigest()


def verify_bundle(bundle):
    errors=[]
    try:
        with zipfile.ZipFile(bundle) as z:
            names=z.namelist()
            if len(names)!=len(set(names)) or 'bundle_manifest.json' not in names:
                return {'valid':False,'errors':['duplicate_or_missing_manifest']}
            manifest=json.loads(z.read('bundle_manifest.json'))
            expected=set(manifest['members'])|{'bundle_manifest.json'}
            if set(names)!=expected:errors.append('member_set')
            if any('..' in PurePosixPath(n).parts or n.startswith('/') or '\\' in n or 'private_eval' in n
                   or 'truth' in n.lower() or 'condition_map' in n.lower() for n in names):
                errors.append('forbidden_path')
            for n,info in manifest['members'].items():
                if n not in names:continue
                data=z.read(n)
                if sha(data)!=info['sha256'] or len(data)!=info['bytes']:
                    errors.append('hash:'+n)
            prefix='model_input/'+manifest['input_name']+'/'
            queries=json.loads(z.read(prefix+'queries.json'))['queries']
            allowed={'bundle_manifest.json',prefix+'queries.json'}
            allowed|={CODE+x for x in MODULES}
            allowed|={CODE+'protocol/'+x for x in PROTOCOL}
            allowed|={DEV+x for x in SERVER}
            if len(queries)>8 or len({x['query_id'] for x in queries})!=len(queries):
                errors.append('query_count_or_duplicates')
            for q in queries:
                root=prefix+q['query_id']+'/'
                m=json.loads(z.read(root+'manifest.json'))
                allowed.add(root+'manifest.json')
                if set(m)!={'as_of_ms','fps','frames','crops','proposal','signature'}:
                    errors.append('prefix_fields')
                if m['signature']!=q['prefix_signature'] or m['as_of_ms']!=q['as_of_ms']:
                    errors.append('query_signature')
                records=m['frames']+m.get('crops',[])
                if any(x['time_ms']>q['as_of_ms'] for x in records):errors.append('future_frame')
                for r in records:
                    allowed.add(root+r['path'])
                    if root+r['path'] not in names or sha(z.read(root+r['path']))!=r['sha256']:
                        errors.append('pixel_hash')
                sig=sha(json.dumps([(r['time_ms'],r['sha256']) for r in records],separators=(',',':')).encode())
                if sig!=m['signature']:errors.append('calculated_signature')
            if set(names)!=allowed:errors.append('positive_allowlist')
    except (OSError,zipfile.BadZipFile,KeyError,ValueError,json.JSONDecodeError) as exc:
        errors.append(type(exc).__name__+':'+str(exc)[:200])
    return {'valid':not errors,'errors':errors}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--bundle',required=True);a=p.parse_args()
    report=verify_bundle(a.bundle);print(json.dumps(report));raise SystemExit(0 if report['valid'] else 1)

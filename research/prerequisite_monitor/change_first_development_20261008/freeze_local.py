"""Write local W9 identity after successful verification; never placed in model ZIP."""
import argparse
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def freeze(workspace,input_dir,bundle,output):
    root=Path(workspace).resolve();input_dir=Path(input_dir).resolve();bundle=Path(bundle).resolve();output=Path(output)
    if output.exists():raise FileExistsError(output)
    code=root/'experiments/prerequisite_probe/change_first_monitor'
    dev=root/'research/prerequisite_monitor/change_first_development_20261008'
    files=list(code.glob('*.py'))+list((code/'protocol').glob('*'))
    files += [dev/x for x in ('inventory.py','prepare_inputs.py','make_pilot.py','review_inputs.py','evaluate.py',
              'build_bundle.py','verify_bundle.py','server_preflight.py','run_server_pilot.sh','collect_and_seal.py')]
    source_docs=[root/x for x in (
      'research/prerequisite_monitor/CHANGE_FIRST_IDEA_FREEZE_20261008_zh.md',
      'research/prerequisite_monitor/RESEARCH_IDEA_FREEZE_20261008_zh.md',
      'docs/plans/2026-10-08-change-first-monitor-architecture-blueprint-zh.md',
      'docs/plans/2026-10-08-change-first-monitor-local-first-implementation-plan-zh.md')]
    obj={'version':'change-first-local-w9-v1','created_utc':datetime.now(timezone.utc).isoformat(),
         'bundle':{'path':str(bundle),'sha256':sha(bundle)},
         'input_queries_sha256':sha(input_dir/'queries.json'),
         'private_source_inventory_sha256':sha(dev/'private_eval/source_inventory.json'),
         'source_documents_sha256':{str(p.relative_to(root)):sha(p) for p in source_docs},
         'implementation_sha256':{str(p.relative_to(root)):sha(p) for p in sorted(files)}}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
    return obj


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--workspace',required=True);p.add_argument('--input',required=True)
    p.add_argument('--bundle',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();print(json.dumps(freeze(a.workspace,a.input,a.bundle,a.output)['bundle']))

"""Read-only remote hardware/model preflight; no model load or network access."""
import argparse
import hashlib
from importlib import metadata
import json
import shutil
import subprocess
import time
from pathlib import Path


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()


def preflight(model,workspace):
    start=time.time();model=Path(model).resolve();workspace=Path(workspace).resolve()
    gpu=subprocess.run(['nvidia-smi','--query-gpu=name,memory.total,memory.free,memory.used',
                        '--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=15)
    processes=subprocess.run(['nvidia-smi','--query-compute-apps=pid,used_gpu_memory',
                              '--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=15)
    usage=shutil.disk_usage(workspace)
    shards=sorted(model.glob('model-*.safetensors'))
    versions={}
    for name in ('torch','transformers','accelerate','pillow'):
        try:versions[name]=metadata.version(name)
        except metadata.PackageNotFoundError:versions[name]=None
    processor_files={x.name:sha(x) for x in model.iterdir() if x.is_file() and
                     x.name in {'processor_config.json','preprocessor_config.json','tokenizer_config.json','chat_template.json'}} if model.is_dir() else {}
    return {'window_start_epoch':start,'model_path':str(model),'config_exists':(model/'config.json').is_file(),
            'config_sha256':sha(model/'config.json') if (model/'config.json').is_file() else None,
            'shards':[{'name':x.name,'bytes':x.stat().st_size,'sha256':sha(x)} for x in shards],
            'processor_files_sha256':processor_files,'package_versions':versions,
            'gpu':gpu.stdout.strip(),'gpu_exit':gpu.returncode,'compute_processes':processes.stdout.strip(),
            'disk_free_bytes':usage.free,'disk_total_bytes':usage.total,'read_only':True}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--workspace',required=True)
    p.add_argument('--output',required=True);a=p.parse_args()
    dest=Path(a.output)
    if dest.exists():raise FileExistsError(dest)
    report=preflight(a.model,a.workspace)
    dest.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'window_start_epoch':report['window_start_epoch'],'gpu':report['gpu'],
                      'compute_processes':report['compute_processes'],'disk_free_bytes':report['disk_free_bytes'],
                      'config_exists':report['config_exists'],'shards':len(report['shards'])}))

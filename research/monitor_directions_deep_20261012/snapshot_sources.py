"""Read-only public source snapshot; never loads models or runs robot code."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'sources'
OUT.mkdir(exist_ok=True)
records = []

def fetch(url, name, parse=False):
    try:
        response = requests.get(url, timeout=35, headers={'User-Agent':'monitor2-literature-audit/1.0'})
        response.raise_for_status()
        path = OUT / name
        path.write_bytes(response.content)
        item = {'url':url, 'file':str(path.relative_to(ROOT)), 'http_status':response.status_code,
                'retrieved_utc':datetime.now(timezone.utc).isoformat(),
                'sha256':hashlib.sha256(response.content).hexdigest(), 'bytes':len(response.content)}
        records.append(item)
        if parse:
            soup = BeautifulSoup(response.content, 'html.parser')
            for el in soup(['script','style']): el.decompose()
            path.with_suffix('.txt').write_text(soup.get_text('\n', strip=True), encoding='utf-8')
        return response
    except Exception as exc:
        records.append({'url':url,'file':name,'error':str(exc)})
        return None

repo = fetch('https://api.github.com/repos/midea-ai/ars','ars_repo.json')
commit = fetch('https://api.github.com/repos/midea-ai/ars/commits/main','ars_commit.json')
if commit is not None:
    sha = commit.json()['sha']
    tree = fetch(f'https://api.github.com/repos/midea-ai/ars/git/trees/{sha}?recursive=1','ars_tree.json')
    if tree is not None:
        files = [x['path'] for x in tree.json()['tree'] if x['type']=='blob' and
                 (x['path'].endswith(('.py','.yaml','.md','.txt')) or x['path']=='.gitmodules') and
                 not x['path'].startswith('assets/')]
        for file in files:
            fetch(f'https://raw.githubusercontent.com/midea-ai/ars/{sha}/{file}', 'ars__'+file.replace('/','__'))
        print(json.dumps({'ars_commit':sha,'code_files':len(files),'tree_paths':[x['path'] for x in tree.json()['tree']]}, ensure_ascii=False))
for label, arxiv_id, version in [('ARS','2609.34484','v1'),('CriticHack','2610.02527','v1'),
                                ('Survey','2607.21655','v1'),('ProgressLM','2601.15224','v1'),
                                ('UniGoal','2503.10630','v1'),('ImagineNav','2512.17435','v1')]:
    fetch(f'https://arxiv.org/abs/{arxiv_id}',f'{label}_abs.html',True)
    fetch(f'https://arxiv.org/html/{arxiv_id}{version}',f'{label}_{version}.html',True)
fetch('https://huggingface.co/api/models/Qwen/Qwen3.6-27B','qwen36_metadata.json')
fetch('https://huggingface.co/Qwen/Qwen3.6-27B/raw/main/README.md','qwen36_README.md')
fetch('https://arxiv.org/html/2512.17435v3','ImagineNav_v3.html',True)
fetch('https://arxiv.org/html/2601.15224v2','ProgressLM_v2.html',True)
fetch('https://arxiv.org/html/2606.06832v1','STRIPS_WM_v1.html',True)
fetch('https://arxiv.org/abs/2307.00329','DoReMi_abs.html',True)
(ROOT/'SOURCE_MANIFEST_root.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'ok':sum('error' not in x for x in records),'errors':[x for x in records if 'error' in x]},ensure_ascii=False))

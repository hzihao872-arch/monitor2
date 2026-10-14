"""Bounded public-source snapshots; no model calls or dataset installation."""
import json, hashlib, pathlib, requests, sys
ROOT = pathlib.Path(__file__).resolve().parent
MANIFEST = ROOT / 'fetch_manifest.json'
entries = json.loads(MANIFEST.read_text('utf-8')) if MANIFEST.exists() else []
def fetch(url, name, cap=5_000_000):
    path = ROOT / name
    if path.exists():
        return path
    r = requests.get(url, timeout=45, stream=True)
    r.raise_for_status()
    data = bytearray()
    for chunk in r.iter_content(65536):
        data.extend(chunk)
        if len(data) > cap:
            raise ValueError('Per-file download cap exceeded: '+name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    entries.append(dict(url=url, path=path.relative_to(ROOT).as_posix(), bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), purpose='public source screening', holdout_eligible=False))
    MANIFEST.write_text(json.dumps(entries, ensure_ascii=False, indent=2)+'\n', 'utf-8')
    return path
if __name__ == '__main__':
    for slug, repo in [('robopulse','lyy0715/RoboPulsePlusPlus'),('imbench','imbench/pb-puzzle-stack-collapse-recovery-v1'),('reboot','REBOOT26/USB-A_recovery_install')]:
        p=fetch('https://huggingface.co/api/datasets/'+repo,slug+'_api.json')
        meta=json.loads(p.read_text('utf-8')); rev=meta['sha']
        tree=json.loads(fetch(f'https://huggingface.co/api/datasets/{repo}/tree/{rev}?recursive=true&limit=1000',slug+'_tree.json').read_text('utf-8'))
        fetch(f'https://huggingface.co/datasets/{repo}/resolve/{rev}/README.md',slug+'_README.md')
        print(json.dumps(dict(slug=slug,repo=repo,revision=rev,card=meta.get('cardData'),files=[dict(path=x['path'],size=x.get('size')) for x in tree if x['type']=='file'][:70]),ensure_ascii=False))

import argparse,hashlib,json,pathlib,tarfile
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('folder');p.add_argument('archive');a=p.parse_args();h=pathlib.Path(a.folder);f=h/a.archive
seal=json.loads((h/'remote_seal.json').read_text(encoding='utf-8'));assert sha(f)==seal['sha256']
dst=h/'remote_verified';dst.mkdir(exist_ok=True)
with tarfile.open(f) as t:t.extractall(dst,filter='data')
members=json.loads((dst/'seal.json').read_text(encoding='utf-8'))['members'];errors=[n for n,s in members.items() if sha(dst/n)!=s]
assert not errors
result={'archive':a.archive,'sha256':sha(f),'verified_members':len(members),'errors':errors}
(h/'REMOTE_VERIFIED.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))

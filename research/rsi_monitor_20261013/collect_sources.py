"""Read-only public literature retrieval; no model, data, or experiment execution."""
from pathlib import Path
from urllib.request import Request, urlopen
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor
import json, hashlib, re, datetime

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'sources'
OUT.mkdir(parents=True, exist_ok=True)
PAPERS = {
 '2609.36054':'v1', '2609.11873':'v3', '2607.07663':'v2',
 '2609.06396':'v2', '2610.13912':'v1', '2310.02304':'v2',
 '2505.22954':'v1', '2603.19461':'v1', '2310.17552':'v1',
 '2410.22689':'v1', '2502.01167':'v1', '2609.34484':'v1',
 '2404.07110':'v1', '2609.30715':'v1', '2608.15680':'v1',
 '2609.39755':'v1', '2109.08273':'v1', '2410.19989':'v2',
 '2609.27068':'v1'}

class Parser(HTMLParser):
 def __init__(self):
  super().__init__(); self.meta = {}; self.parts = []; self.skip = 0
 def handle_starttag(self, tag, attrs):
  a = dict(attrs)
  if tag == 'meta' and a.get('name','').startswith('citation_'):
   self.meta.setdefault(a['name'], []).append(a.get('content',''))
  if tag in ('script','style'): self.skip += 1
  if tag in ('p','div','h1','h2','h3','h4','h5','h6','li','tr','section'): self.parts.append('\n')
 def handle_endtag(self, tag):
  if tag in ('script','style'): self.skip=max(0,self.skip-1)
 def handle_data(self, data):
  if not self.skip: self.parts.append(data)

def fetch(job):
 key, url, binary = job
 rec={'key':key,'url':url,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  req=Request(url,headers={'User-Agent':'Monitor-literature-readonly/1.0'})
  with urlopen(req,timeout=25) as response:
   raw=response.read(); rec['final_url']=response.url
  path=OUT/(key+('.pdf' if binary else '.html')); path.write_bytes(raw)
  rec.update(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),status='ok')
  if not binary:
   p=Parser(); p.feed(raw.decode('utf-8',errors='replace'))
   txt=re.sub(r'[ \t]+',' ',''.join(p.parts)); txt=re.sub(r'\n\s*\n+', '\n\n',txt)
   (OUT/(key+'.txt')).write_text(txt,encoding='utf-8'); rec['metadata']=p.meta
 except Exception as e: rec.update(status='failed',error=str(e))
 return rec

jobs=[]
for paper,version in PAPERS.items():
 jobs.append((paper+'_abs','https://arxiv.org/abs/'+paper,False))
 if paper != '2609.36054': jobs.append((paper+version+'_full','https://arxiv.org/html/'+paper+version,False))
jobs.append(('2609.36054v1','https://arxiv.org/pdf/2609.36054v1',True))
with ThreadPoolExecutor(max_workers=3) as pool: results=list(pool.map(fetch,jobs))
(OUT/'retrieval_manifest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
metadata=[{'arxiv_id':r['key'].replace('_abs',''),**r.get('metadata',{})} for r in results if r['key'].endswith('_abs')]
(OUT/'bibliography_metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
lines=[]
for m in metadata:
 pid=m['arxiv_id']; title=m.get('citation_title',['UNKNOWN'])[0]; authors=' and '.join(m.get('citation_author',[])); date=m.get('citation_date',[''])[0]
 lines.append('@misc{arxiv'+pid.replace('.','')+',\n  title={'+title+'},\n  author={'+authors+'},\n  year={'+date[:4]+'},\n  eprint={'+pid+'},\n  archivePrefix={arXiv},\n  url={https://arxiv.org/abs/'+pid+'}\n}')
(ROOT/'references.bib').write_text('\n\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps([{'key':r['key'],'status':r['status'],'error':r.get('error')} for r in results],ensure_ascii=False))

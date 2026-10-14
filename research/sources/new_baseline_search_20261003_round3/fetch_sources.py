from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen
from html.parser import HTMLParser
from datetime import datetime, timezone
import hashlib
import json
import sys

B = Path(__file__).resolve().parent
class Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.skip=0; self.out=[]
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style','annotation'): self.skip+=1
        if tag in ('p','tr','h1','h2','h3','h4','h5','section'): self.out.append('\n')
        if tag in ('td','th'): self.out.append(' | ')
    def handle_endtag(self, tag):
        if tag in ('script','style','annotation'): self.skip=max(0,self.skip-1)
    def handle_data(self, data):
        if not self.skip: self.out.append(data)
def fetch(pair):
    name,url = pair
    row={'file':name,'url':url,'retrieved_at':datetime.now(timezone.utc).isoformat()}
    try:
        with urlopen(Request(url,headers={'User-Agent':'Research evidence audit'}),timeout=35) as r:
            data=r.read(16_000_001); row['status']=r.status
        if len(data)>16_000_000: raise ValueError('Source exceeded bounded fetch size')
        (B/name).write_bytes(data)
        row.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        if name.endswith('.html'):
            parser=Text(); parser.feed(data.decode('utf-8'))
            (B/(name+'.txt')).write_text('\n'.join(' '.join(x.split()) for x in ''.join(parser.out).splitlines() if x.strip()),encoding='utf-8')
    except Exception as e: row['error']=str(e)
    return row
if __name__=='__main__':
    pairs=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    result=list(ThreadPoolExecutor(max_workers=5).map(fetch,pairs))
    manifest=B/'fetch_manifest.json'
    old=json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else []
    manifest.write_text(json.dumps(old+result,ensure_ascii=False,indent=2),encoding='utf-8')
    for row in result: print(json.dumps(row,ensure_ascii=False))

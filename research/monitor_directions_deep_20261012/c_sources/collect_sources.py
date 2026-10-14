import concurrent.futures, datetime, hashlib, json, pathlib, urllib.request

ROOT = pathlib.Path(__file__).parent
PAPERS = ['2609.30715v1','2602.02454v1','2406.18043v2','2412.04455v1','2510.10975v1','2609.11445v1','2606.23085v1','2608.13438v1','2607.27511v1','2603.06987v1','2607.28251v1','2606.09258v1','2503.08558v2']
URLS = {p: 'https://arxiv.org/html/' + p for p in PAPERS}
URLS.update({'farm_readme': 'https://raw.githubusercontent.com/HaoranPei-casia/FARM/main/README.md', 'world_gymnast_readme': 'https://raw.githubusercontent.com/world-gymnast/world-gymnast/main/README.md','world_gymnast_setup': 'https://raw.githubusercontent.com/world-gymnast/world-gymnast/main/SETUP.md','sirius_project': 'https://ut-austin-rpl.github.io/sirius-runtime-monitor/'})
def fetch(item):
    name,url=item
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'monitor2-research/1.0'})
        with urllib.request.urlopen(req,timeout=40) as r: data=r.read()
        suffix='.html' if '/html/' in url or url.endswith('/') else '.md'
        path=ROOT/(name+suffix);path.write_bytes(data)
        return {'name':name,'url':url,'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'status':'saved'}
    except Exception as e:return {'name':name,'url':url,'status':'error','error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: out=list(pool.map(fetch,URLS.items()))
(ROOT/'manifest.json').write_text(json.dumps({'check_date':'2026-10-12 Asia/Shanghai','sources':out},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))

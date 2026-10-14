import concurrent.futures,urllib.request,re,pathlib,json
p=pathlib.Path(__file__).parent
ids=['2609.30715','2602.02454','2406.18043','2412.04455','2510.10975','2609.11445','2606.23085','2608.13438','2607.27511','2603.06987','2607.28251','2606.09258','2503.08558','2606.06832','2609.18324']
def fetch(i):
    try:
        data=urllib.request.urlopen('https://arxiv.org/abs/'+i,timeout=25).read().decode()
        (p/(i+'_abs.html')).write_text(data,encoding='utf-8')
        date=re.search(r'<div class="dateline">(.*?)</div>',data,re.S)
        return {'id':i,'dateline':re.sub('<[^>]+>','',date.group(1)).strip() if date else 'not found'}
    except Exception as e:return {'id':i,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: a=list(pool.map(fetch,ids))
(p/'version_check.json').write_text(json.dumps(a,indent=2),encoding='utf-8')
print(json.dumps(a,indent=2))

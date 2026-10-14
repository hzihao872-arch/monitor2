import hashlib, json, pathlib, tarfile

ROOT=pathlib.Path(__file__).resolve().parent
DEV=ROOT.parent
mapping={x['query_id']:(x['family'],x['condition']) for x in json.loads((DEV/'private_eval/pilot_v5_selection.json').read_text(encoding='utf-8'))}
names=['s1_v1_results_20261009T121725Z.tar.gz','s1_v2_results_20261009T122427Z.tar.gz','s1_v3_results_20261009T123229Z.tar.gz','v1_length_results_20261009_final.tar.gz']
audit=[]
for name in names:
    path=DEV/'runs/s1_20261009'/name
    with tarfile.open(path) as t:
        ledger=[json.loads(s) for s in t.extractfile(next(n for n in t.getnames() if n.endswith('/requests.jsonl'))).read().decode().splitlines()]
        issued={r['request_id']:r['request'] for r in ledger if r['kind']=='issued'}
        rows=[]
        for r in ledger:
            if r['kind']!='completed': continue
            req=issued[r['request_id']]
            rows.append({'case':mapping.get(req['query_id']), 'stage':req['stage'], 'arm':req['arm'], 'metrics':r['metrics'], 'seconds':r['seconds'], 'raw':r['raw']})
        results=[json.load(t.extractfile(n)) for n in t.getnames() if '/results/' in n and n.endswith('.json')]
        audit.append({'archive':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rows':rows,'results':results})
(ROOT/'old_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
for run in audit:
    print(run['archive'],len(run['rows']),round(sum(x['seconds'] for x in run['rows']),2))
    for x in run['rows']:
        if x['stage']=='V1':
            print(x['case'],x['metrics']['output_tokens'],x['metrics']['hit_output_cap'],x['raw'])

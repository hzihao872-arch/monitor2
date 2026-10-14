import collections,json,pathlib
H=pathlib.Path(__file__).resolve().parent;labels=json.loads((H/'private_eval/labels.json').read_text());rows=[json.loads(p.read_text()) for p in (H/'download/run/results').glob('*.json')];logs=[json.loads(s) for s in (H/'download/run/requests.jsonl').read_text().splitlines()];issued={r['request_id']:r for r in logs if r['kind']=='issued'};done={r['request_id']:r for r in logs if r['kind']=='completed'};counts=collections.defaultdict(lambda:{'n':0,'correct_ai':0,'unknown':0,'input_tokens':0});pairs=collections.defaultdict(dict);errors=[]
for r in rows:
 k='n'+str(r['sample_count'])+'_'+r['order'];s=counts[k];s['n']+=1;s['correct_ai']+=r['payload']['state']==labels[r['probe_id']]['reference'];s['unknown']+=r['payload']['state']=='Unknown';pairs[(r['sample_count'],r['probe_id'])][r['order']]=r
 if any(m['time_ms']>14000 for m in r['request']['image_meta']):errors.append('future')
 if len(r['request']['image_ids'])!=r['sample_count']:errors.append('sample_count')
for rid,d in done.items():counts[issued[rid]['request']['arm']]['input_tokens']+=d['metrics']['input_tokens']
comparison=[]
for (n,pid),p in sorted(pairs.items()):
 a=p['positive_first'];b=p['opposed_first'];comparison.append({'sample_count':n,'probe':pid,'reference_ai':labels[pid]['reference'],'states':[a['payload']['state'],b['payload']['state']],'order_consistent':a['payload']['state']==b['payload']['state'],'both_correct_ai':a['payload']['state']==b['payload']['state']==labels[pid]['reference']})
base=[json.loads(p.read_text()) for p in (H.parent/'native_prefix_20261009/download/run/results').glob('*.json') if json.loads(p.read_text())['representation']=='images']
for r in rows:
 b=next(b for b in base if b['probe_id']==r['probe_id'] and b['order']==r['order']);assert r['request']['prompt']==b['request']['prompt']
m=[r['metrics'] for r in done.values()];summary={'issued':len(issued),'completed':len(done),'failed':sum(r['kind']=='failed' for r in logs),'ambiguous':len(set(issued)-set(done)-{r['request_id'] for r in logs if r['kind']=='failed'}),'prior':204,'cumulative':228,'counts':dict(counts),'pairs':comparison,'audit_errors':errors,'wall_seconds':sum(r['seconds'] for r in done.values()),'adapter_seconds':sum(r['elapsed_seconds'] for r in m),'input_tokens':sum(r['input_tokens'] for r in m),'peak_vram_gib':max([r['peak_vram_bytes'] for r in m] or [0])/2**30,'status':'same query, automatic prefix sampling only; directed development predicates, not event discovery'}
(H/'ANALYSIS.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))

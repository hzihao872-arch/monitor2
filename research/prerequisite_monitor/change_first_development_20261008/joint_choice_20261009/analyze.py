import collections,json,pathlib
H=pathlib.Path(__file__).resolve().parent
labels=json.loads((H/'private_eval/labels.json').read_text(encoding='utf-8'))
rows=[json.loads(p.read_text(encoding='utf-8')) for p in (H/'download/run/results').glob('*.json')]
logs=[json.loads(s) for s in (H/'download/run/requests.jsonl').read_text(encoding='utf-8').splitlines()]
issued={r['request_id']:r for r in logs if r['kind']=='issued'};done={r['request_id']:r for r in logs if r['kind']=='completed'}
counts=collections.defaultdict(lambda:{'n':0,'correct_ai':0,'unknown':0});pairs=collections.defaultdict(dict);errors=[]
for r in rows:
 k=r['kind']+'_'+r['development_split']+'_'+r['order'];s=counts[k];s['n']+=1;s['correct_ai']+=r['payload']['state']==labels[r['probe_id']]['reference'];s['unknown']+=r['payload']['state']=='Unknown'
 pairs[(r['kind'],r['probe_id'])][r['order']]=r
 if any(m['time_ms']>r['request']['as_of_ms'] for m in r['request']['image_meta']):errors.append('future')
comparison=[]
for (kind,pid),p in sorted(pairs.items()):
 a=p['positive_first'];b=p['opposed_first'];comparison.append({'kind':kind,'probe':pid,'split':a['development_split'],'reference_ai':labels[pid]['reference'],'positive_first':a['payload'],'opposed_first':b['payload'],'order_consistent':a['payload']['state']==b['payload']['state'],'both_correct_ai':a['payload']['state']==b['payload']['state']==labels[pid]['reference']})
 if a['request']['image_hashes']!=b['request']['image_hashes']:errors.append('pixel_difference')
metrics=[r['metrics'] for r in done.values()]
summary={'issued':len(issued),'completed':len(done),'failed':sum(r['kind']=='failed' for r in logs),'ambiguous':len(set(issued)-set(done)-{r['request_id'] for r in logs if r['kind']=='failed'}),'prior':128,'cumulative':128+len(issued),'counts':dict(counts),'pairs':comparison,'audit_errors':errors,'wall_seconds':sum(r['seconds'] for r in done.values()),'adapter_seconds':sum(r['elapsed_seconds'] for r in metrics),'input_tokens':sum(r['input_tokens'] for r in metrics),'peak_vram_gib':max([r['peak_vram_bytes'] for r in metrics] or [0])/2**30,'status':'AI development reference only; directed predicates; held-out development examples are not blind'}
(H/'ANALYSIS.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='pairs'},ensure_ascii=False,indent=2));print(json.dumps([{k:v for k,v in r.items() if k not in ('positive_first','opposed_first')}|{'states':[r['positive_first']['state'] if 'state' in r['positive_first'] else None,r['opposed_first']['state'] if 'state' in r['opposed_first'] else None]} for r in comparison],ensure_ascii=False))

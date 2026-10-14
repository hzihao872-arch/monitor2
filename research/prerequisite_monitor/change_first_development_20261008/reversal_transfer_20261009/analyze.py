import collections,json,pathlib
H=pathlib.Path(__file__).resolve().parent;labels=json.loads((H/'private_eval/labels.json').read_text());rows=[json.loads(p.read_text()) for p in (H/'download/run/results').glob('*.json')];logs=[json.loads(s) for s in (H/'download/run/requests.jsonl').read_text().splitlines()];issued={r['request_id']:r for r in logs if r['kind']=='issued'};done={r['request_id']:r for r in logs if r['kind']=='completed'};counts=collections.defaultdict(lambda:{'n':0,'correct_ai':0,'unknown':0,'input_tokens':0});pairs=collections.defaultdict(dict);errors=[]
for r in rows:
 k=r['mode']+'_'+r['order'];s=counts[k];s['n']+=1;s['correct_ai']+=r['payload']['state']==labels[r['probe_id']]['reference'];s['unknown']+=r['payload']['state']=='Unknown';pairs[(r['mode'],r['probe_id'])][r['order']]=r
 if any(m['time_ms']>r['request']['as_of_ms'] for m in r['request']['image_meta']):errors.append('future')
for rid,d in done.items():counts[issued[rid]['request']['arm']]['input_tokens']+=d['metrics']['input_tokens']
comparison=[]
for (mode,pid),p in sorted(pairs.items()):
 a=p['positive_first'];b=p['opposed_first'];comparison.append({'mode':mode,'probe':pid,'reference_ai':labels[pid]['reference'],'states':[a['payload']['state'],b['payload']['state']],'order_consistent':a['payload']['state']==b['payload']['state'],'both_correct_ai':a['payload']['state']==b['payload']['state']==labels[pid]['reference']})
for pid in labels:
 for order in ('positive_first','opposed_first'):
  a=pairs[('current',pid)][order];b=pairs[('prefix8',pid)][order];assert a['request']['prompt']==b['request']['prompt']
m=[r['metrics'] for r in done.values()];summary={'issued':len(issued),'completed':len(done),'failed':sum(r['kind']=='failed' for r in logs),'ambiguous':len(issued)-len(done)-sum(r['kind']=='failed' for r in logs),'prior':283,'cumulative':283+len(issued),'counts':dict(counts),'pairs':comparison,'audit_errors':errors,'wall_seconds':sum(r['seconds'] for r in done.values()),'adapter_seconds':sum(r['elapsed_seconds'] for r in m),'input_tokens':sum(r['input_tokens'] for r in m),'peak_vram_gib':max([r['peak_vram_bytes'] for r in m] or [0])/2**30,'status':'AI development reversal transfer; atomic state trajectory only, not automated event or utility/reversal accuracy'}
(H/'ANALYSIS.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))

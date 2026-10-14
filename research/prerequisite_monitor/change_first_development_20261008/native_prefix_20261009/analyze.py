import collections,json,pathlib
H=pathlib.Path(__file__).resolve().parent;labels=json.loads((H/'private_eval/labels.json').read_text(encoding='utf-8'))
rows=[json.loads(p.read_text(encoding='utf-8')) for p in (H/'download/run/results').glob('*.json')];logs=[json.loads(s) for s in (H/'download/run/requests.jsonl').read_text().splitlines()]
issued={r['request_id']:r for r in logs if r['kind']=='issued'};done={r['request_id']:r for r in logs if r['kind']=='completed'};counts=collections.defaultdict(lambda:{'n':0,'correct_ai':0,'unknown':0,'input_tokens':0});pairs=collections.defaultdict(dict);errors=[]
for r in rows:
 k=r['representation']+'_'+r['order'];s=counts[k];s['n']+=1;s['correct_ai']+=r['payload']['state']==labels[r['probe_id']]['reference'];s['unknown']+=r['payload']['state']=='Unknown';pairs[(r['representation'],r['probe_id'])][r['order']]=r
 req=r['request']
 if any(m['time_ms']>req['as_of_ms'] for m in req['image_meta']):errors.append('future')
 if len(req['image_ids'])!=15 or any(i.startswith('c') for i in req['image_ids']):errors.append('not_15_full_frames')
for rid,d in done.items():counts[issued[rid]['request']['arm']]['input_tokens']+=d['metrics']['input_tokens']
comparison=[]
for (rep,pid),p in sorted(pairs.items()):
 a=p['positive_first'];b=p['opposed_first'];comparison.append({'representation':rep,'probe':pid,'reference_ai':labels[pid]['reference'],'states':[a['payload']['state'],b['payload']['state']],'order_consistent':a['payload']['state']==b['payload']['state'],'both_correct_ai':a['payload']['state']==b['payload']['state']==labels[pid]['reference']})
for pid in labels:
 for order in ('positive_first','opposed_first'):
  a=pairs.get(('images',pid),{}).get(order);b=pairs.get(('video',pid),{}).get(order)
  if a and b and any(a['request'][k]!=b['request'][k] for k in ('prompt','image_ids','image_hashes','image_meta','as_of_ms')):errors.append('representation_pixel_prompt_difference')
m=[r['metrics'] for r in done.values()];summary={'issued':len(issued),'completed':len(done),'failed':sum(r['kind']=='failed' for r in logs),'ambiguous':len(set(issued)-set(done)-{r['request_id'] for r in logs if r['kind']=='failed'}),'prior':164,'cumulative':164+len(issued),'counts':dict(counts),'pairs':comparison,'audit_errors':errors,'wall_seconds':sum(r['seconds'] for r in done.values()),'adapter_seconds':sum(r['elapsed_seconds'] for r in m),'input_tokens':sum(r['input_tokens'] for r in m),'peak_vram_gib':max([r['peak_vram_bytes'] for r in m] or [0])/2**30,'status':'same sparse RGB pixels, unequal representation tokens; AI development only'}
(H/'ANALYSIS.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))

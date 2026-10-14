import collections,json,pathlib
H=pathlib.Path(__file__).resolve().parent;rows=[json.loads(p.read_text()) for p in (H/'download/run/results').glob('*.json')];logs=[json.loads(s) for s in (H/'download/run/requests.jsonl').read_text().splitlines()];done=[r for r in logs if r['kind']=='completed'];issued=[r for r in logs if r['kind']=='issued'];counts=collections.defaultdict(lambda:{'n':0,'valid':0});curves=[];errors=[];pairs=collections.defaultdict(dict)
for r in rows:
 s=counts[r['order']];s['n']+=1;s['valid']+=r['validation']['valid'];pairs[r['query_id']][r['order']]=r
 if any(m['time_ms']>14000 for m in r['request']['image_meta']):errors.append('future')
 if r['validation']['valid']:
  mapped={r['request']['host_only_frame_mapping'][str(o['frame_number'])]:o for o in r['validation']['payload']};curves.append({'query':r['query_id'],'order':r['order'],'percent_by_ref':{k:v['task_completion_percentage'] for k,v in mapped.items()},'descriptions_by_ref':{k:v['frame_description'] for k,v in mapped.items()},'all_zero':all(v['task_completion_percentage']==0 for v in mapped.values())})
comparison=[]
for q,p in pairs.items():
 a=p['chronological'];b=p['shuffled'];assert a['request']['prompt']==b['request']['prompt'];assert sorted(a['request']['image_hashes'])==sorted(b['request']['image_hashes'])
 comparison.append({'query_id':q,'both_valid':a['validation']['valid'] and b['validation']['valid'],'errors_chrono':a['validation']['errors'],'errors_shuffle':b['validation']['errors']})
summary={'issued':len(issued),'completed':len(done),'failed':sum(r['kind']=='failed' for r in logs),'ambiguous':len(issued)-len(done)-sum(r['kind']=='failed' for r in logs),'prior':388,'cumulative':388+len(issued),'counts':dict(counts),'curves_strictly_valid_only':curves,'pair_contracts':comparison,'fence_raw_count':sum(r['raw'].startswith('```') for r in rows),'audit_errors':errors,'wall_seconds':sum(r['seconds'] for r in done),'adapter_seconds':sum(r['metrics']['elapsed_seconds'] for r in done),'input_tokens':sum(r['metrics']['input_tokens'] for r in done),'output_tokens':sum(r['metrics']['output_tokens'] for r in done),'hit_caps':sum(r['metrics']['hit_output_cap'] for r in done),'peak_vram_gib':max([r['metrics']['peak_vram_bytes'] for r in done] or [0])/2**30,'status':'Qwen8B five-frame zero-shot adaptation of GVL; source baseline initial0 mathematically excludes negative net relative to initial; no VOC against chronological index used as utility accuracy'}
(H/'ANALYSIS.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))

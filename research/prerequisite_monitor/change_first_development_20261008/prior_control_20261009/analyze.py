import json,pathlib
H=pathlib.Path(__file__).resolve().parent;S=H.parent/'atomic_contrast_20261009';labels=json.loads((H.parent/'atomic_state_20261009/private_eval/labels.json').read_text())
rows=[json.loads(p.read_text()) for p in (H/'download/run/results').glob('*.json')];rgb=[json.loads(p.read_text()) for p in (S/'download/run/results').glob('*.json')];logs=[json.loads(s) for s in (H/'download/run/requests.jsonl').read_text().splitlines()];done=[r for r in logs if r['kind']=='completed'];pairs=[]
for pid in labels:
 a={r['polarity']:r for r in rows if r['probe_id']==pid};b={r['polarity']:r for r in rgb if r['probe_id']==pid and r['input_kind']=='rgb' and r['template']=='chat'}
 if len(a)!=2:continue
 d0=a['positive']['payload']['alias_logp']['True']-a['opposed']['payload']['alias_logp']['True'];d1=b['positive']['payload']['alias_logp']['True']-b['opposed']['payload']['alias_logp']['True'];adjust=d1-d0
 for polarity in a:assert a[polarity]['request']['prompt']==b[polarity]['request']['prompt'];assert not a[polarity]['request']['image_hashes']
 def state(d):return 'True' if d>0 else ('False' if d<0 else 'Unknown')
 pairs.append({'probe':pid,'reference_ai':labels[pid]['reference'],'prior_values':[a[k]['payload']['alias_argmax'] for k in ('positive','opposed')],'prior_margin':d0,'rgb_margin':d1,'prior_direction':state(d0),'rgb_direction':state(d1),'adjusted_margin':adjust,'adjusted_direction':state(adjust),'adjusted_correct_ai':state(adjust)==labels[pid]['reference'],'same_direction_as_prior':state(d1)==state(d0)})
summary={'issued':sum(r['kind']=='issued' for r in logs),'completed':len(done),'failed':sum(r['kind']=='failed' for r in logs),'unknown':sum(r['payload']['alias_argmax']=='Unknown' for r in rows),'both_true_pairs':sum(p['prior_values']==['True','True'] for p in pairs),'pairs':pairs,'cumulative':204,'wall_seconds':sum(r['seconds'] for r in done),'adapter_seconds':sum(r['metrics']['elapsed_seconds'] for r in done),'input_tokens':sum(r['metrics']['input_tokens'] for r in done),'peak_vram_gib':max([r['metrics']['peak_vram_bytes'] for r in done] or [0])/2**30,'adjustment_status':'posthoc exploratory subtraction; no calibrated threshold or main method validation'}
(H/'ANALYSIS.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))

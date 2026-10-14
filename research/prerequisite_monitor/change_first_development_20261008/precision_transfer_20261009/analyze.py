import json,pathlib,collections
H=pathlib.Path(__file__).resolve().parent
labels=json.loads((H/'private_eval/labels.json').read_text())
rows=[json.loads(p.read_text()) for p in (H/'remote_verified/run/results').glob('*.json')]
old=[json.loads(p.read_text()) for p in (H.parent/'atomic_contrast_20261009/remote_verified/run/results').glob('*.json')]
matrix={}
for r in old:
 if r['input_kind']=='rgb' and r['template']=='chat':matrix[('bf16',r['probe_id'],r['polarity'])]=r
for r in rows:matrix[(r['head_precision'],r['probe_id'],r['polarity'])]=r
pairs=[];comparisons=[]
for precision,pid in sorted({(k[0],k[1]) for k in matrix}):
 a=matrix[precision,pid,'positive'];b=matrix[precision,pid,'opposed'];d=a['payload']['alias_logp']['True']-b['payload']['alias_logp']['True'];v='True' if d>0 else 'False' if d<0 else 'Unknown'
 pairs.append({'precision':precision,'probe':pid,'margin':d,'value':v,'ai_reference_agreement':v==labels[pid]['reference'],'both_true':a['payload']['alias_argmax']==b['payload']['alias_argmax']=='True'})
for pid,pol in sorted({(k[1],k[2]) for k in matrix}):
 a=matrix['bf16',pid,pol];b=matrix['fp32',pid,pol]
 assert all(a['request'][k]==b['request'][k] for k in ('prompt','image_ids','image_hashes','image_meta','as_of_ms'))
 comparisons.append({'probe':pid,'polarity':pol,'alias_answer_changed':a['payload']['alias_argmax']!=b['payload']['alias_argmax'],'delta_true_logp':b['payload']['alias_logp']['True']-a['payload']['alias_logp']['True']})
summary={'issued':len(rows),'pairs':pairs,'precision_comparisons':comparisons,'groups':{}}
for precision in ('bf16','fp32'):
 for group in ('seen','R'):
  selected=[p for p in pairs if p['precision']==precision and (('_R_' in p['probe'])==(group=='R'))];summary['groups'][precision+'_'+group]={'n':len(selected),'contrast_ai_agreement':sum(p['ai_reference_agreement'] for p in selected),'both_true':sum(p['both_true'] for p in selected)}
summary['head_precision_answer_flips']=sum(p['alias_answer_changed'] for p in comparisons)
summary['status']='Exploratory two-forward delta; only output head converted to FP32, no training; AI exposed development references, not calibrated success.'
(H/'ANALYSIS.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in summary.items() if k not in ('pairs','precision_comparisons')},indent=2))

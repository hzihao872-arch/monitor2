import json,pathlib,collections
H=pathlib.Path(__file__).resolve().parent
def load(folder):return {(r['query_id'],r['change'],r['side']):r for p in folder.glob('*.json') if (r:=json.loads(p.read_text()))}
own=load(H.parent/'generated_fact_20261009/remote_verified/run/results');cross=load(H/'remote_verified/run/results');pairs=[];counts=collections.Counter(r['payload']['value'] for r in cross.values())
for q,j in sorted({k[:2] for k in own}):
 deltas={};values={}
 for side in ('before','after'):
  a=own[q,j,side];b=cross[q,j,side];assert a['condition']==b['condition'] and a['object']==b['object'];other=own[q,j,'after' if side=='before' else 'before'];assert b['request']['target_ms']==other['request']['target_ms'];deltas[side]=a['payload']['logp']['True']-b['payload']['logp']['True'];values[side]={'own':a['payload']['value'],'cross':b['payload']['value']}
 pairs.append({'query':q,'change':j,'before':own[q,j,'before']['condition'],'after':own[q,j,'after']['condition'],'values':values,'own_minus_cross_true_logp':deltas,'both_own_greater':all(v>0 for v in deltas.values()),'both_own_true':all(own[q,j,s]['payload']['value']=='True' for s in ('before','after'))})
summary={'result_conditions':len(cross),'actual_issued':47,'cross_values':dict(counts),'transition_pairs':pairs,'both_own_greater':sum(p['both_own_greater'] for p in pairs),'both_own_greater_and_own_true':sum(p['both_own_greater'] and p['both_own_true'] for p in pairs),'interpretation':'Within-statement temporal contrast; target IDs and prefix counts differ naturally. Retrospective generated predicates at14. Posthoc diagnostic, not calibrated probability or confirmed true change; omissions unrecoverable.'}
(H/'ANALYSIS.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in summary.items() if k!='transition_pairs'},indent=2));print(json.dumps(pairs,indent=2))

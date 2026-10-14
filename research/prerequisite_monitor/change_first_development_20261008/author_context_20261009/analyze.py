import json,pathlib
H=pathlib.Path(__file__).resolve().parent;rows=[json.loads(p.read_text()) for p in (H/'download/run/results').glob('*.json')];logs=[json.loads(s) for s in (H/'download/run/requests.jsonl').read_text().splitlines()];done=[r for r in logs if r['kind']=='completed'];issued=[r for r in logs if r['kind']=='issued'];cases=[];errors=[];text=['# 作者目标盲轨迹描述与完成度读出','开发诊断；完成度不代表准备、效用或独立事实真值。']
for q in json.loads((H/'config.json').read_text())['queries']:
 rr={r['arm']:r for r in rows if r['query_id']==q['query_id']}
 if len(rr)!=3:continue
 d=rr['direct'];a=rr['augmented'];desc=rr['description'];assert d['request']['image_hashes']==a['request']['image_hashes']==desc['request']['image_hashes'];assert desc['request']['instruction'] is None
 if q['goal'] in desc['request']['prompt']:errors.append('description_goal_leak')
 for r in rr.values():
  if any(m['time_ms']>14000 for m in r['request']['image_meta']):errors.append('future')
 ref='True' if q['query_id'] in ('qf2bed1caaecc37a0','q675f22bca6b91b54') else 'False'
 cases.append({'query_id':q['query_id'],'visual_completion_proxy_ai':ref,'direct':d['payload'],'augmented':a['payload'],'direct_proxy_match':d['payload']['value']==ref,'augmented_proxy_match':a['payload']['value']==ref,'delta_true_logp':a['payload']['true_logp']-d['payload']['true_logp'],'description':desc['raw']})
 text.extend(['',f'## {q["query_id"]}','','```text',desc['raw'],'```','',f'Direct: {d["payload"]}','',f'Augmented: {a["payload"]}'])
summary={'issued':len(issued),'completed':len(done),'failed':sum(r['kind']=='failed' for r in logs),'ambiguous':len(issued)-len(done)-sum(r['kind']=='failed' for r in logs),'cumulative':331+len(issued),'direct_proxy_match':sum(r['direct_proxy_match'] for r in cases),'augmented_proxy_match':sum(r['augmented_proxy_match'] for r in cases),'cases':cases,'audit_errors':errors,'wall_seconds':sum(r['seconds'] for r in done),'adapter_seconds':sum(r['metrics']['elapsed_seconds'] for r in done),'input_tokens':sum(r['metrics']['input_tokens'] for r in done),'output_tokens':sum(r['metrics']['output_tokens'] for r in done),'hit_caps':sum(r['metrics']['hit_output_cap'] for r in done),'peak_vram_gib':max([r['metrics']['peak_vram_bytes'] for r in done] or [0])/2**30,'label_forms':[r['metrics']['label_token_ids'] for r in done if 'label_token_ids' in r['metrics']][:1],'status':'author prompt/scoring adaptation with exact last-token form and honest native timestamps, no full TOPReward reward reproduction; AI visible-completion proxy does not independently establish floor contact/stability or preparation utility'}
(H/'ANALYSIS.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');(H/'DESCRIPTIONS_zh.md').write_text('\n'.join(text),encoding='utf-8');print(json.dumps(summary,indent=2))

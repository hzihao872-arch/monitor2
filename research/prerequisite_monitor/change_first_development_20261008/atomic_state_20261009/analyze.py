import collections,hashlib,json,pathlib,statistics
H=pathlib.Path(__file__).resolve().parent;R=H/'download/run'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
labels=json.loads((H/'private_eval/labels.json').read_text(encoding='utf-8'))
spec=json.loads((H/'probes.json').read_text(encoding='utf-8'));window=json.loads((H/'window.json').read_text(encoding='utf-8'))
logs=[json.loads(s) for s in (R/'requests.jsonl').read_text().splitlines() if s.strip()]
issued={r['request_id']:r for r in logs if r['kind']=='issued'}; completed={r['request_id']:r for r in logs if r['kind']=='completed'}
fail={r['request_id']:r for r in logs if r['kind']=='failed'}; rows=[json.loads(p.read_text()) for p in (R/'results').glob('*.json')]
matrix={};by_arm=collections.defaultdict(lambda:{'issued':0,'completed':0,'valid':0,'unknown':0,'correct_ai_reference':0,'wall_seconds':0,'adapter_seconds':0,'input_tokens':0,'output_tokens':0,'hit_caps':0,'peak_vram_bytes':0})
errors=[]
for rid,item in issued.items():
    req=item['request'];mode=req['arm'];stat=by_arm[mode];stat['issued']+=1
    if item['wall_time']>=window['model_stop_epoch']:errors.append('issued_after_stop')
    if req['input_type'].startswith('legal_rgb') and 'supplied visible fact description' in req['prompt']:errors.append('oracle_into_rgb')
    if any(m['time_ms']>req['as_of_ms'] for m in req['image_meta']):errors.append('future_frame')
    if rid in completed:
        row=completed[rid];m=row['metrics'];stat['completed']+=1;stat['wall_seconds']+=row['seconds'];stat['adapter_seconds']+=m['elapsed_seconds']
        for k in ('input_tokens','output_tokens'):stat[k]+=m[k]
        stat['hit_caps']+=int(m['hit_output_cap']);stat['peak_vram_bytes']=max(stat['peak_vram_bytes'],m['peak_vram_bytes'])
for row in rows:
    pid=row['probe_id'];mode=row['mode'];check=row['validation'];value=check.get('value') if mode!='rgb_logits' else check['payload']['value']
    stat=by_arm[mode];stat['valid']+=int(check['valid']);stat['unknown']+=int(value=='Unknown');stat['correct_ai_reference']+=int(check['valid'] and value==labels[pid]['reference'])
    matrix.setdefault(pid,{'reference_ai':labels[pid]['reference']})[mode]={'value':value,'valid':check['valid'],'raw':row['raw']}
index={(r['probe_id'],r['mode']):r for r in rows}
controls=[]
for p in spec['probes']:
    pid=p['id'];a=index.get((pid,'rgb_single'));b=index.get((pid,'rgb_logits'))
    if a and b:
        keys=('prompt','image_ids','image_hashes','image_meta','limits','as_of_ms','prefix_signature')
        equal={k:a['request'][k]==b['request'][k] for k in keys}
        controls.append({'probe_id':pid,'same_input':equal,'same_value':matrix[pid]['rgb_single']['value']==matrix[pid]['rgb_logits']['value']})
        if not all(equal.values()):errors.append('logit_generate_inputs_differ')
directions=[]
for group,t0 in [('opening',0),('plate',0),('grasp',7),('inside',7)]:
    first=f'{group}_{t0:02d}';last=f'{group}_14'
    if (first,'rgb_logits') in index and (last,'rgb_logits') in index:
        a=index[(first,'rgb_logits')]['validation']['payload'];b=index[(last,'rgb_logits')]['validation']['payload']
        delta=b['log_probabilities']['True']-a['log_probabilities']['True'];expected=1 if labels[last]['reference']=='True' else -1
        directions.append({'group':group,'before_logp_true':a['log_probabilities']['True'],'after_logp_true':b['log_probabilities']['True'],
            'delta_logp_true':delta,'reference_direction':expected,'direction_matches':delta*expected>0,
            'status':'exploratory pair-direction readout; not preregistered threshold, causal utility or calibration'})
old=H.parent/'runs/diagnostic_20261009_window/delivery/window_v9/requests.jsonl'
old_logs=[json.loads(s) for s in old.read_text().splitlines() if s.strip()];oldissued=sum(r['kind']=='issued' for r in old_logs)
if oldissued!=50 or sha(old)!=window['parent_ledger_sha256']:errors.append('parent_changed')
if oldissued+len(issued)>80:errors.append('budget_exceeded')
durations=sorted(r['seconds'] for r in completed.values())
summary={'issued':len(issued),'completed':len(completed),'backend_failed':len(fail),'ambiguous':len(set(issued)-set(completed)-set(fail)),
    'parent_issued':oldissued,'parent_plus_new':oldissued+len(issued),'older_separate_issued':96,'by_arm':dict(by_arm),'matrix':matrix,
    'pair_input_controls':controls,'exploratory_token_probability_changes':directions,'audit_errors':errors,
    'wall_seconds':sum(durations),'adapter_seconds':sum(r['metrics']['elapsed_seconds'] for r in completed.values()),
    'p50_wall_seconds':statistics.median(durations) if durations else None,
    'p95_wall_seconds':statistics.quantiles(durations,n=100,method='inclusive')[94] if len(durations)>1 else (durations[0] if durations else None),
    'first_issued_epoch':min(r['wall_time'] for r in issued.values()) if issued else None,
    'last_completed_epoch':max(r['wall_time'] for r in completed.values()) if completed else None,
    'planned_primary':24,'planned_context':6,'unexecuted_slots':30-len(issued),
    'reference_status':'AI development visual pre-audit only; 3 reused video trajectories, 8 correlated atoms; no human independent double labels or blind test'}
(H/'ANALYSIS.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k not in ('matrix','pair_input_controls')},ensure_ascii=False,indent=2))
for pid in sorted(matrix):print(pid,json.dumps(matrix[pid],ensure_ascii=False))

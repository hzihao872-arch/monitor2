import collections,json,pathlib,statistics
H=pathlib.Path(__file__).resolve().parent;labels=json.loads((H.parent/'atomic_state_20261009/private_eval/labels.json').read_text());rows=[json.loads(p.read_text()) for p in (H/'download/run/results').glob('*.json')]
logs=[json.loads(s) for s in (H/'download/run/requests.jsonl').read_text().splitlines()];issued={r['request_id']:r for r in logs if r['kind']=='issued'};done={r['request_id']:r for r in logs if r['kind']=='completed'}
counts=collections.defaultdict(lambda:{'n':0,'bare_correct':0,'alias_correct':0,'unknown':0,'wall_seconds':0,'adapter_seconds':0,'input_tokens':0})
matrix=collections.defaultdict(dict);token_forms={};errors=[]
for row in rows:
    key=row['input_kind']+'_'+row['template'];expected=labels[row['probe_id']]['reference'];expected=expected if row['polarity']=='positive' else ('False' if expected=='True' else 'True')
    s=counts[key];s['n']+=1;s['bare_correct']+=int(row['payload']['bare_argmax']==expected);s['alias_correct']+=int(row['payload']['alias_argmax']==expected);s['unknown']+=int(row['payload']['alias_argmax']=='Unknown')
    matrix[(row['input_kind'],row['template'],row['probe_id'])][row['polarity']]=row
for rid,item in done.items():
    req=issued[rid]['request'];key=req['arm'].rsplit('_',1)[0];s=counts[key];s['wall_seconds']+=item['seconds'];s['adapter_seconds']+=item['metrics']['elapsed_seconds'];s['input_tokens']+=item['metrics']['input_tokens'];token_forms=item['metrics']['candidate_ids']
    if any(m['time_ms']>req['as_of_ms'] for m in req['image_meta']):errors.append('future')
pairs=[]
for (kind,template,pid),p in sorted(matrix.items()):
    if len(p)!=2:continue
    a=p['positive'];b=p['opposed'];yesno=[a['payload']['alias_argmax'],b['payload']['alias_argmax']]
    delta=a['payload']['alias_logp']['True']-b['payload']['alias_logp']['True'];prediction='True' if delta>0 else ('False' if delta<0 else 'Unknown')
    pairs.append({'kind':kind,'template':template,'probe':pid,'positive_value':yesno[0],'opposed_value':yesno[1],
        'both_true':yesno==['True','True'],'both_false':yesno==['False','False'],'contrast_margin':delta,'contrast_value':prediction,
        'contrast_correct_ai':prediction==labels[pid]['reference'],'contrastive_status':'exploratory derived scoring; two-forward cost; statement priors are uncontrolled'})
for kind in ('rgb','oracle'):
    for pid in labels:
        for polarity in ('positive','opposed'):
            a=matrix.get((kind,'chat',pid),{}).get(polarity);b=matrix.get((kind,'raw',pid),{}).get(polarity)
            if a and b:
                if any(a['request'][k]!=b['request'][k] for k in ('prompt','image_hashes','image_ids','image_meta','as_of_ms')):errors.append('template_input_difference')
dur=[r['seconds'] for r in done.values()]
summary={'issued':len(issued),'completed':len(done),'failed':sum(r['kind']=='failed' for r in logs),'ambiguous':len(set(issued)-set(done)-{r['request_id'] for r in logs if r['kind']=='failed'}),
    'prior_issued':80,'cumulative':80+len(issued),'counts':dict(counts),'pairs':pairs,'candidate_token_ids':token_forms,'audit_errors':errors,
    'wall_seconds':sum(dur),'adapter_seconds':sum(r['metrics']['elapsed_seconds'] for r in done.values()),'input_tokens':sum(r['metrics']['input_tokens'] for r in done.values()),
    'peak_vram_gib':max([r['metrics']['peak_vram_bytes'] for r in done.values()] or [0])/2**30,
    'references':'AI development pre-audit; directed predicates; no main-method score or blind assessment'}
(H/'ANALYSIS.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))

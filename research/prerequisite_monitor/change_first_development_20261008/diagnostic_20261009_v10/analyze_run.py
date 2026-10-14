"""Read-only archive analysis, including every failure and explicit cost layers."""
import argparse,json,pathlib,statistics,tarfile,collections,math

def analyze(archive,out):
    with tarfile.open(archive) as t:
        rows=[json.loads(s) for s in t.extractfile(next(n for n in t.getnames() if n.endswith('/requests.jsonl'))).read().decode().splitlines()]
        results=[json.load(t.extractfile(n)) for n in t.getnames() if '/results/' in n and n.endswith('.json')]
    issued={x['request_id']:x for x in rows if x['kind']=='issued'}
    completed=[x for x in rows if x['kind']=='completed']; failed=[x for x in rows if x['kind']=='failed']
    ambiguous=set(issued)-{x['request_id'] for x in completed+failed}
    costs={}
    for x in completed:
        q=issued[x['request_id']]['request'];key=q['arm']+':'+q['stage'];g=costs.setdefault(key,{'requests':0,'wall_seconds':0,'adapter_seconds':0,'input_tokens':0,'output_tokens':0,'hit_caps':0,'peak_vram_bytes':0})
        g['requests']+=1;g['wall_seconds']+=x['seconds'];m=x.get('metrics') or {}
        for k in ('input_tokens','output_tokens'):g[k]+=m.get(k,0)
        g['adapter_seconds']+=m.get('elapsed_seconds',0);g['hit_caps']+=bool(m.get('hit_output_cap'));g['peak_vram_bytes']=max(g['peak_vram_bytes'],m.get('peak_vram_bytes',0))
    reference=json.loads((pathlib.Path(__file__).parent/'reference_development_audit.json').read_text())
    pairs=[];summary=[]
    for r in results:
        if 'v1' in r:
            v=r['v1']['validation'];summary.append({'qid':r['query_id'],'mode':r['mode'],'valid':v['valid'],'errors':v['errors'],'payload':v['payload']})
        if 'direct' in r:summary.append({'qid':r['query_id'],'mode':r['mode'],**r['direct']['validation']})
        if 'arms' in r and r.get('mode')!='legacy_oracle':
            for arm,a in r['arms'].items():
                item={'qid':r['query_id'],'input_type':r['input_type'],'arm':arm,'first_failure':a['first_failure']}
                for stage in ('draft','verify','final'):
                    rec=a.get(stage);v=rec['validation'] if rec else {'valid':False,'errors':['unexecuted'],'payload':None}
                    item[stage]=v
                pairs.append(item)
    # Counts are developer pre-audit agreement, not independent evaluation accuracy.
    transitions=collections.defaultdict(lambda:collections.Counter())
    fields=('goal_done','direct_ready','partial_preparation','net_effect','reversal')
    for r in pairs:
        ref=reference[r['qid']];key=r['input_type']+':'+r['arm']
        dp=r['draft']['payload'];fp=r['final']['payload']
        draft=dp['judgment'] if r['draft']['valid'] else None
        fin=fp if r['final']['valid'] else None
        r['agreement']={}
        for k in fields:
            before=(draft['state'][k] if k in draft.get('state',{}) else draft[k]) if draft else 'invalid_or_unexecuted'
            after=(fin['state'][k] if k in fin.get('state',{}) else fin[k]) if fin else 'invalid_or_unexecuted'
            typ=('engineering_unavailable' if draft is None or fin is None else
                 'kept_correct' if before==ref[k] and after==ref[k] else 'corrected' if before!=ref[k] and after==ref[k] else
                 'destroyed' if before==ref[k] and after!=ref[k] else 'still_wrong_or_unanswered')
            if after=='unknown' and before not in ('unknown','invalid_or_unexecuted'):transitions[key]['became_unknown']+=1
            transitions[key][typ]+=1
            r['agreement'][k]={'before':before,'after':after,'reference':ref[k],'transition':typ}
    secs=sorted(x['seconds'] for x in completed)
    output={'scope':'all requests; transitions use AI development pre-audit only','issued':len(issued),'completed':len(completed),'failed':len(failed),'ambiguous':len(ambiguous),
            'wall_seconds':sum(secs),'adapter_seconds':sum((x.get('metrics') or {}).get('elapsed_seconds',0) for x in completed),
            'p50_seconds':statistics.median(secs) if secs else None,'p95_seconds':secs[math.ceil(.95*len(secs))-1] if secs else None,
            'cost_by_arm_stage':costs,'summary':summary,'pairs':pairs,'transition_counts':{k:dict(v) for k,v in transitions.items()},
            'unexecuted_query_records':[r for r in results if 'skipped' in r],
            'legacy_oracle_results':[r for r in results if r.get('mode')=='legacy_oracle']}
    pathlib.Path(out).write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:output[k] for k in ('issued','completed','failed','ambiguous','wall_seconds','adapter_seconds','transition_counts')},ensure_ascii=False))
    for r in summary:
        print(r['mode'],r['qid'],r.get('valid'),r.get('errors'),r.get('payload'))
    for r in pairs:
        print(r['input_type'],r['arm'],r['qid'],r['first_failure'],r['agreement'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--out',required=True);a=p.parse_args();analyze(a.archive,a.out)

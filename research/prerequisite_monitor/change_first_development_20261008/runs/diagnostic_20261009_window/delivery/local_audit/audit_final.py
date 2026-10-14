"""All-cost audit and controls, never used as model input."""
import collections,hashlib,json,pathlib,tarfile
dev=pathlib.Path(__file__).resolve().parent.parent
out=dev/'runs/diagnostic_20261009_window'; archive=out/'window_v9_FINAL_20261009.tar.gz'
with tarfile.open(archive) as t:
    names=t.getnames();rows=[json.loads(s) for s in t.extractfile('window_v9/requests.jsonl').read().decode().splitlines()]
    results=[json.load(t.extractfile(n)) for n in names if '/results/' in n and n.endswith('.json')]
    status=json.load(t.extractfile('window_v9/provenance/FINAL_IDLE_STATUS.json'))
issued={r['request_id']:r for r in rows if r['kind']=='issued'};done=[r for r in rows if r['kind']=='completed']
cost=collections.defaultdict(lambda:{'calls':0,'wall_seconds':0,'adapter_seconds':0,'input_tokens':0,'output_tokens':0,'hit_caps':0})
for r in done:
    req=issued[r['request_id']]['request'];m=r['metrics'];g=cost[req['arm']+':'+req['stage']];g['calls']+=1;g['wall_seconds']+=r['seconds'];g['adapter_seconds']+=m['elapsed_seconds'];g['input_tokens']+=m['input_tokens'];g['output_tokens']+=m['output_tokens'];g['hit_caps']+=m['hit_output_cap']
control=[]
for r in issued.values():
    req=r['request'];assert all(x['time_ms']<=14000 for x in req['image_meta'])
    if req['arm']=='D_RGB_ORDER':
        source=next(x['request'] for x in issued.values() if x['request']['arm']=='D_RGB' and x['request']['query_id']==req['query_id'])
        assert req['prompt']==source['prompt'] and req['limits']==source['limits'] and sorted(req['image_hashes'])==sorted(source['image_hashes'])
        assert [x['time_ms'] for x in req['image_meta']]==sorted(x['time_ms'] for x in req['image_meta'])
        orig=next(x for x in results if x.get('mode')=='directpixel' and x['query_id']==req['query_id'])['direct']['validation']['payload']
        new=next(x for x in results if x.get('mode')=='order_probe' and x['query_id']==req['query_id'])['direct']['validation']['payload']
        control.append({'qid':req['query_id'],'same_prompt_pixels_limits':True,'state_net_reversal_unchanged':all(orig[k]==new[k] for k in ('state','net_effect','reversal')),'original':orig,'sorted':new})
comparisons=[]
for q in {r['request']['query_id'] for r in issued.values()}:
    for stage in ('DRAFT','VERIFY'):
        pairs=[r['request'] for r in issued.values() if r['request']['query_id']==q and r['request']['stage']==stage and r['request']['arm'] in ('C_predicted','D_predicted')]
        if len(pairs)==2:
            assert pairs[0]['image_hashes']==pairs[1]['image_hashes'] and pairs[0]['limits']==pairs[1]['limits']
            comparisons.append({'qid':q,'stage':stage,'same_pixels_and_limits':True})
payloads=[]
for r in results:
    if r.get('mode') in ('oracle_text','legacy_oracle'):
        payloads.append(r)
    elif r.get('mode')=='paired':
        payloads.append(r)
fullschema=json.loads((dev/'diagnostic_20261009_v9/old_full_jsonschema_audit.json').read_text())
oldlength=[r for r in fullschema if r['archive'].startswith('v1_length')]
stats={'ledger_counts':{k:sum(r['kind']==k for r in rows) for k in ('issued','completed','failed')},'first_issued_epoch':min(r['wall_time'] for r in issued.values()),'last_completed_epoch':max(r['wall_time'] for r in done),'total_input_tokens':sum(r['metrics']['input_tokens'] for r in done),'total_output_tokens':sum(r['metrics']['output_tokens'] for r in done),'total_hit_caps':sum(r['metrics']['hit_output_cap'] for r in done),'peak_vram_gib':max(r['metrics']['peak_vram_bytes'] for r in done)/2**30,'cost_by_arm_stage':dict(cost),'order_controls':control,'paired_controls':comparisons,'oracle_rows':payloads,'server_idle':status,'old_1536_fullschema_passes':sum(r['exported_schema_valid'] for r in oldlength),'old_1536_fullschema_count':len(oldlength),'all_pixel_times_legal':True}
(out/'EXTENDED_AUDIT.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in stats.items() if k not in ('oracle_rows','order_controls','paired_controls')},ensure_ascii=False,indent=2))
for r in payloads:
    if r.get('mode')=='oracle_text':
        print('ORACLE',r['query_id'],json.dumps(r['direct_text'],ensure_ascii=False))
        for arm,rec in r['relations'].items():
            if isinstance(rec,dict): print('L2',r['query_id'],arm,json.dumps(rec,ensure_ascii=False))
print('ORDER',[(r['qid'],r['state_net_reversal_unchanged']) for r in control])

"""Audit actual exploratory outputs without reparsing fenced text into valid judgments."""
import json,hashlib,csv,collections
from pathlib import Path
from trace_sources import OUT,save
from experiments.monitor_eval import load_online_track,frame_packet,parse_output

rows=[];problems=[]
for ep in [618,621]:
    track=load_online_track(OUT/f'p0/ep{ep}/online_track.json')
    for method in ['S0','S1']:
        p=Path(f'experiments/artifacts/r1_upstream_diagnostic_v1/ep{ep}_{method}')
        records=[json.loads(x) for x in (p/'records.jsonl').read_text('utf-8').splitlines()]
        summary=json.loads((p/'summary.json').read_text('utf-8'))
        for r in records:
            packet=frame_packet(track,r['tick'])
            assert r['frame_sha256']==[f['sha256'] for f in packet]
            assert r['frame_times']==[f['time'] for f in packet]
            assert r['prompt_sha256']==hashlib.sha256(r['prompt'].encode()).hexdigest()
            assert r['judgments']==parse_output(r['raw'],track['objects'],r['tick'])['judgments']
            assert r['cost']['calls']==1 and r['cost']['frames']<=4
            assert r['cost']['input_tokens_known']<=4096 and r['cost']['output_tokens_known']<=256
            assert r['cost']['memory_tokens']<=512
            assert all(f['time']<=r['tick'] for f in packet)
        rows.append({'episode':ep,'method':method,'records':len(records),'parse_status_counts':dict(collections.Counter(r['parse_status'] for r in records)),'fenced_outputs':sum(r['raw'].startswith('```') for r in records),'output_at_256_token_cap':sum(r['cost']['output_tokens_known']==256 for r in records),'nonempty_memory_inputs':sum(bool(r['memory_in']) for r in records),'nonempty_accepted_memory_outputs':sum(bool(r['memory_out']) for r in records),'cost':summary['cost'],'records_path':str(p/'records.jsonl')})
    a=[json.loads(x) for x in Path(f'experiments/artifacts/r1_upstream_diagnostic_v1/ep{ep}_S0/records.jsonl').read_text('utf-8').splitlines()]
    b=[json.loads(x) for x in Path(f'experiments/artifacts/r1_upstream_diagnostic_v1/ep{ep}_S1/records.jsonl').read_text('utf-8').splitlines()]
    assert all(x['frame_sha256']==y['frame_sha256'] and x['frame_times']==y['frame_times'] for x,y in zip(a,b))
pre=json.loads((OUT/'diagnostic_preregistration.json').read_text('utf-8'))
for r in pre['frozen_files']:assert hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()==r['sha256']
tot={k:sum(r['cost'][k] for r in rows) for k in ['calls','input_tokens','output_tokens','elapsed_ms_known']}
assert tot['calls']==62
save('diagnostic_audit.json',{'prompt_version':pre['prompt_version'],'protocol':'S6-draft-4','runs':rows,'totals':tot,'peak_vram_bytes':max(r['cost']['peak_vram_bytes'] for r in rows),'same_actual_packet_prefix_verified':True,'frozen_prerun_inputs_unchanged':True,'valid_judgments':0,'interpretation':'Output-interface/length failure. S1 rolling summary did not execute successfully; no strong-baseline remaining-reasoning-error conclusion. No posthoc stripping/reparse, retries, new prompt version, C1 or H1 statistics.','h1_comparison':False,'stage8':False})
print(json.dumps({'totals':tot,'runs':[{k:v for k,v in r.items() if k not in ['cost','records_path']} for r in rows]},indent=2))

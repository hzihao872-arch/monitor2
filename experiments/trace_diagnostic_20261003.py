"""One preregistered S0/S1 diagnostic on two MIT upstream development tracks.

No H1 comparison, reference labels, training, downloads, or candidate architecture.
Existing harness and backend are reused; their default engineering behavior is unchanged.
"""
import json,hashlib,time
from pathlib import Path
import experiments.monitor_eval as evaluation
import experiments.qwen_backend as qwen
from experiments.run_online import validate_media

ROOT=Path('research/sources/recovery_search_20261003/upstream_trace')
VERSION='r1-upstream-diagnostic-v1'
COMMON='''Only green_on_blue is the declared monitored condition: the green cube is stacked on and supported by the blue cube after placement, rather than merely held above it. This selects a condition already in the original instruction and adds no new task rule. H asks whether this placement has happened at any time so far; C asks whether that same relation holds now. G asks whether the whole original three-cube task is complete. No separate continuous-process obligation is specified: output P=? and do not infer a no-contact or never-move rule. Use the named colors consistently. Current occlusion can make C unknown without erasing an established H. A prior model statement is fallible, not visual evidence.'''
DIRECT='Assess the supplied observations directly; set memory to an empty string.'
SUMMARY='''Check the original task conditions separately using these frames and the generic rolling summary. First inspect the current visible objects and any contacts or occlusions; then reconcile with earlier observations. H and C need not agree. Do not equate failure of a later step with loss of every earlier condition, or mistake an ongoing attempt for completion. In memory write a concise chronological visual summary, at most 100 words: include what was clearly achieved and when, the latest visible arrangement of the green, blue and red cubes, the most recent attempted action, and unresolved occlusions or contradictions. Preserve relevant earlier observations when they leave the four-frame window; correct earlier unsupported claims when new evidence contradicts them. Do not create a condition ledger, retrieve other records, or use future information.'''

def build_prompt(method,instruction,objects,memory,tick):
    if method not in ('S0','S1'):raise ValueError('Only preregistered baselines allowed')
    base=(f"Current trajectory time: {tick} s on the published 25 FPS video clock, not a verified hardware clock. "
          f"Original instruction version {instruction['version']} (effective {instruction['effective_at']} s): {instruction['text']}\n"
          +COMMON+'\nUse only supplied current/past frames and, for S1, the supplied summary. '
          'Output pure JSON, with each H/C/P/G exactly one of "+", "-", "?"; evidence_time must be no later than current time. '
          'Format: {"judgments":[{"object_id":"green_on_blue","H":"?","C":"?","P":"?","G":"?","evidence_time":0}],"memory":"..."}. '
          'No markdown or text outside JSON. ')
    return base+('\n'+DIRECT if method=='S0' else '\nPrior generic summary: '+(memory or '(none)')+'\n'+SUMMARY)

def main():
    prereg=json.loads((ROOT/'diagnostic_preregistration.json').read_text('utf-8'))
    assert prereg['prompt_version']==VERSION and prereg['max_model_calls']==62
    # Verify every frozen input and implementation before loading the model.
    for row in prereg['frozen_files']:
        assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
    for ep in [618,621]:validate_media(evaluation.load_online_track(ROOT/f'p0/ep{ep}/online_track.json'))
    evaluation.build_prompt=build_prompt
    evaluation.PROMPT_VERSION=VERSION
    qwen.build_prompt=build_prompt
    t=time.perf_counter()
    try:backend=qwen.QwenBackend('.models/qwen3-vl-2b-instruct')
    except Exception as exc:
        row={'status':'initialization_failed','error':repr(exc),'seconds':time.perf_counter()-t}
        (ROOT/'diagnostic_initialization.json').write_text(json.dumps(row,indent=2)+'\n')
        evaluation._append_ledger('experiments/run_ledger.csv',{'run_id':VERSION+'-init','kind':'exploratory_init','status':'failed','error':repr(exc)})
        raise
    (ROOT/'diagnostic_initialization.json').write_text(json.dumps({'status':'loaded','seconds':time.perf_counter()-t},indent=2)+'\n')
    for ep in [618,621]:
        for method in ['S0','S1']:
            out=Path(f'experiments/artifacts/r1_upstream_diagnostic_v1/ep{ep}_{method}')
            print(ep,method,flush=True)
            summary=evaluation.run_track(ROOT/f'p0/ep{ep}/online_track.json',backend,method,out,'experiments/run_ledger.csv')
            print(json.dumps(summary),flush=True)
            if summary['status']!='completed':return

if __name__=='__main__':main()

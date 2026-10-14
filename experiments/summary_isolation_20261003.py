"""Bounded output-task isolation; no changes to frozen evaluation or backend."""
import argparse,hashlib,json,time
from pathlib import Path
from datetime import datetime,timezone
import experiments.monitor_eval as ev
import experiments.qwen_backend as qb
from experiments.run_online import validate_media

ROOT=Path('experiments/artifacts/r1_summary_isolation_20261003')
SOURCE=Path('research/sources/recovery_search_20261003/upstream_trace')
MODE='joint'
SUMMARY='Write a visual history summary in at most 35 English words. Mention observed changes, the current cube arrangement, and uncertainty or occlusion. Preserve earlier clearly observed achievements, but correct unsupported earlier claims. The prior summary is fallible, not ground truth.'
CONTRACT={
 'text': 'Return only the summary as plain text, without a heading or formatting.',
 'json': 'Return exactly one JSON object containing only memory, a string with the summary. Start with { and end with }. No markdown or code fences.',
 'joint': 'Return exactly one JSON object with memory (the summary string) and judgments (an array containing one object). The judgment object has object_id="green_on_blue", H, C, P, G, and evidence_time (a number no later than the current time). Each H/C/P/G value must be exactly "+", "-", or "?". Start with { and end with }. No markdown or code fences.'
}
def prompt(method,instruction,objects,memory,tick):
    base=(f"Current video playback time: {tick} s. Original task: {instruction['text']}\n"
          'Use only the supplied current and past frames. The monitored relation is green_on_blue: the green cube has been released and is supported on the blue cube, not merely held above it. '
          'H means this placement has happened at least once so far; C means the relation holds now; G means the whole original task is complete. '
          'Use + for supported true, - for supported false, and ? for insufficient evidence. P must be ? because no continuous-process obligation is specified. '
          'Inspect each task condition separately. Occlusion can make C unknown without undoing an established H. Do not add task requirements.\n')
    if method=='S0':
        return base+'Make a direct assessment from these frames. Set memory to an empty string.\n'+CONTRACT['joint']
    return base+SUMMARY+'\nPrior generic summary: '+(memory or '(none)')+'\n'+CONTRACT[MODE]

def inspect_output(raw,mode,tick,tokens):
    result={'format_valid':False,'memory':'','summary_usable_syntax':False}
    if mode=='text':
        memory=raw.strip(); valid=bool(memory) and not memory.startswith(('```','{'))
    else:
        try:
            data=json.loads(raw)
            memory=data.get('memory','') if isinstance(data,dict) else ''
            valid=isinstance(memory,str) and bool(memory.strip())
            if mode=='json':valid=valid and set(data)=={'memory'}
            if mode=='joint':valid=valid and ev.parse_output(raw,['green_on_blue'],tick)['parse_status']=='valid'
        except (ValueError,TypeError):memory='';valid=False
    words=memory.split(); lowered=[w.lower().strip('.,;:') for w in words]
    trigrams=[tuple(lowered[i:i+3]) for i in range(max(0,len(words)-2))]
    # A duplicated sentence may be short enough yet remain an unusable summary.
    repetition=(len(trigrams)-len(set(trigrams)))/max(1,len(trigrams))
    result.update(format_valid=valid,memory=memory,word_count=len(words),repeated_trigram_fraction=repetition,
                  summary_usable_syntax=valid and 1<=len(words)<=35 and tokens<256 and repetition<=0.25)
    return result

def save(name,data):
    (ROOT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf-8')

def verified_backend():
    pre=json.loads((ROOT/'preregistration.json').read_text('utf-8'))
    for row in pre['frozen_files']:
        assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
    for ep in (618,621):validate_media(ev.load_online_track(SOURCE/f'p0/ep{ep}/online_track.json'))
    qb.build_prompt=prompt;ev.build_prompt=prompt;ev.PROMPT_VERSION='r1-summary-isolation-joint-v1'
    return qb.QwenBackend('.models/qwen3-vl-2b-instruct')

def isolation(backend):
    global MODE
    path=ROOT/'isolation_records.jsonl'
    if path.exists():raise FileExistsError(path)
    track=ev.load_online_track(SOURCE/'p0/ep618/online_track.json')
    for tick in (0,2,6):
        for MODE in ('text','json','joint'):
            frames=ev.frame_packet(track,tick);instruction=ev.instruction_at(track,tick)
            start=time.perf_counter()
            try:
                result=backend.infer('S1',instruction,track['objects'],frames,'',tick)
                checked=inspect_output(result['raw'],MODE,tick,result['output_tokens'])
                status='returned';error=''
            except Exception as exc:
                result={'raw':None,'input_tokens':0,'output_tokens':0,'memory_tokens':0,'peak_vram_bytes':None}
                checked={};status='runtime_failure';error=repr(exc)
            elapsed=(time.perf_counter()-start)*1000
            p=prompt('S1',instruction,track['objects'],'',tick)
            row={'mode':MODE,'tick':tick,'trajectory_id':track['trajectory_id'],'memory_in':'','prompt':p,'prompt_sha256':hashlib.sha256(p.encode()).hexdigest(),'frame_times':[f['time'] for f in frames],'frame_sha256':[f['sha256'] for f in frames],**result,'inspection':checked,'status':status,'error':error,'total_elapsed_ms':elapsed}
            ev._append_jsonl(path,row)
            ev._append_ledger('experiments/run_ledger.csv',{'run_id':f'r1-isolation-{MODE}-q{tick}','utc':datetime.now(timezone.utc).isoformat(),'kind':'output_task_isolation','track':str(path),'method':MODE,'backend':'QwenBackend','status':status,'ticks_recorded':1,'call_attempts':1,'input_tokens_known':result['input_tokens'],'output_tokens_known':result['output_tokens'],'elapsed_ms_known':elapsed,'peak_vram_bytes':result['peak_vram_bytes'],'error':error})
            print(MODE,tick,checked,flush=True)
            if status=='runtime_failure':return

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['isolation','chain','full'],required=True);args=parser.parse_args()
    if args.phase!='isolation':
        gate=json.loads((ROOT/('isolation_review.json' if args.phase=='chain' else 'chain_review.json')).read_text('utf-8'))
        assert gate['pass'], 'manual content + syntax gate did not pass'
    backend=verified_backend()
    if args.phase=='isolation':isolation(backend)
    elif args.phase=='chain':ev.run_track(ROOT/'chain_track.json',backend,'S1',ROOT/'chain','experiments/run_ledger.csv')
    else:
        for ep in (618,621):
            for method in ('S0','S1'):
                summary=ev.run_track(SOURCE/f'p0/ep{ep}/online_track.json',backend,method,ROOT/f'full_ep{ep}_{method}','experiments/run_ledger.csv')
                if summary['status']!='completed':return
if __name__=='__main__':main()

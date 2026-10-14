"""Frozen atomic state probes; no changes to old core, labels never enter RGB requests."""
import argparse, hashlib, io, json, math, os, pathlib, subprocess, sys, time

HERE=pathlib.Path(__file__).resolve().parent
VALUES=('True','False','Unknown')

def canonical(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def digest(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(p,x):
    p=pathlib.Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix('.tmp'); tmp.write_text(canonical(x),encoding='utf-8'); os.replace(tmp,p)
def check_times(rows,target):
    if any(r['time_ms']>target for r in rows): raise ValueError('future evidence')
def causal_ids(rows,target):
    available=[r for r in rows if r['time_ms']<=target]
    if not available: raise ValueError('no prefix')
    n=min(8,len(available))
    indices=[round(i*(len(available)-1)/max(1,n-1)) for i in range(n)]
    return [available[i]['evidence_id'] for i in indices]
def validate_answer(raw):
    answer=raw.strip()
    return {'valid':answer in VALUES,'value':answer if answer in VALUES else None,'errors':[] if answer in VALUES else ['exact_token_contract']}
def read_logits(log_probs):
    if set(log_probs)!=set(VALUES) or any(not math.isfinite(v) for v in log_probs.values()): raise ValueError('invalid logits')
    high=max(log_probs.values()); weights={k:math.exp(v-high) for k,v in log_probs.items()}; z=sum(weights.values())
    return {'value':max(VALUES,key=lambda k:log_probs[k]),'log_probabilities':log_probs,
            'conditional_three_way':{k:v/z for k,v in weights.items()},
            'three_token_mass':sum(math.exp(v) for v in log_probs.values()),'calibrated':False}
def check_budget(parent,new,pending,now,stop):
    if parent!=50: raise RuntimeError('parent ledger changed')
    if parent+new+pending>80: raise RuntimeError('global request cap')
    if now+pending*18>=stop: raise RuntimeError('complete block cannot fit before model stop')

def main(a):
    sys.path.insert(0,str(pathlib.Path(a.core_root).resolve()))
    from experiments.prerequisite_probe.change_first_monitor.prefix import PrefixPackage
    from experiments.prerequisite_probe.change_first_monitor.runner import RequestLedger,hash_obj
    from experiments.prerequisite_probe.change_first_monitor.qwen_backend import QwenBackend,prepare_content
    spec=json.loads((HERE/'probes.json').read_text(encoding='utf-8')); window=json.loads((HERE/'window.json').read_text(encoding='utf-8'))
    oracle=json.loads((HERE/'oracle_text.json').read_text(encoding='utf-8'))
    root=pathlib.Path(a.output); root.mkdir(parents=True,exist_ok=True)
    lock=root/'.run.lock'; fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY); os.close(fd)
    try:
        parent=pathlib.Path(a.parent_ledger)
        if digest(parent)!=window['parent_ledger_sha256']: raise RuntimeError('parent ledger hash mismatch')
        parent_n=sum(json.loads(s)['kind']=='issued' for s in parent.read_text().splitlines() if s.strip())
        hashes={n:digest(HERE/n) for n in ('atomic_runner.py','probes.json','window.json','oracle_text.json')}
        if hashes!=json.loads((HERE/'freeze.json').read_text(encoding='utf-8'))['files']: raise RuntimeError('source freeze changed')
        class Backend(QwenBackend):
            def generate(self,request):
                if a.mock:
                    self.last_metrics={'input_tokens':0,'output_tokens':0,'elapsed_seconds':0,'peak_vram_bytes':0,'hit_output_cap':False}
                    return canonical(read_logits(dict(zip(VALUES,[-2.,-3.,-1.])))) if request['decoder']=='logits' else 'Unknown'
                if request['decoder']=='generate': return super().generate(request)
                self._load()
                import torch
                started=time.perf_counter()
                encoded=self.processor.apply_chat_template([{'role':'user','content':prepare_content(request)}],tokenize=True,
                    add_generation_prompt=True,return_dict=True,return_tensors='pt')
                n=int(encoded['input_ids'].shape[-1])
                if n>request['limits'][0]: raise RuntimeError('input cap')
                token_ids={s:self.processor.tokenizer.encode(s,add_special_tokens=False) for s in VALUES}
                if any(len(v)!=1 for v in token_ids.values()): raise RuntimeError('candidate is not a single token')
                encoded=encoded.to('cuda'); torch.cuda.reset_peak_memory_stats()
                with torch.inference_mode():
                    output=self.model(**encoded,logits_to_keep=1)
                    logp=torch.log_softmax(output.logits[0,-1,:].float(),dim=-1)
                    probs={s:float(logp[v[0]].item()) for s,v in token_ids.items()}
                torch.cuda.synchronize()
                self.last_metrics={'input_tokens':n,'output_tokens':0,'elapsed_seconds':time.perf_counter()-started,
                    'peak_vram_bytes':int(torch.cuda.max_memory_allocated()),'hit_output_cap':False,'forward_count':1,'candidate_token_ids':token_ids}
                return canonical(read_logits(probs))
        backend=Backend(a.model or 'mock')
        ledger=RequestLedger(root,hash_obj({'series':'atomic_state_v1','hashes':hashes,'backend':backend.identity,'mock':a.mock}),30,window['hard_deadline_epoch'],1200)
        chosen=[p for p in spec['probes'] if not a.ids or p['id'] in a.ids]
        modes=('rgb_single','oracle_current','rgb_logits') if a.block=='primary' else ('rgb_prefix','oracle_timeline')
        if a.block=='context': chosen=[p for p in chosen if p['id'] in spec['context_ids']]
        pending=sum(not (root/'results'/f'{p["id"]}_{m}.json').exists() for p in chosen for m in modes)
        check_budget(parent_n,ledger.issued_count,pending,time.time()+120,window['model_stop_epoch'])
        if not a.mock:
            active=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
            if active: raise RuntimeError('GPU occupied; do not load or terminate another job')
        for p in chosen:
            pkg=PrefixPackage(pathlib.Path(a.input)/p['query_id']); ref=p['ref']; target=pkg.handles[ref]['time_ms']
            for mode in modes:
                dst=root/'results'/f'{p["id"]}_{mode}.json'
                if dst.exists(): continue
                check_budget(parent_n,ledger.issued_count,1,time.time(),window['model_stop_epoch'])
                ids=causal_ids(pkg.manifest['frames'],target) if mode=='rgb_prefix' else ([ref] if mode.startswith('rgb') else [])
                metadata=[{k:pkg.handles[i].get(k) for k in ('time_ms','parent_id','crop_xyxy')} for i in ids]; check_times(metadata,target)
                pixels=[pkg.read(i,'V3') for i in ids]
                prompt='Judge one positive visible state at the exact TARGET. Use only evidence at or before TARGET. '
                prompt+='Answer exactly one token: True, False, or Unknown. Unknown means the evidence cannot decide. Do not explain. '
                prompt+=f'TARGET: {ref} at {target} ms. STATEMENT: '+p['statement']
                if mode.startswith('oracle'):
                    facts=oracle[p['id']]['current'] if mode=='oracle_current' else oracle[p['id']]['timeline']
                    prompt+='\nEXTRA-INPUT DIAGNOSTIC: supplied visible fact description:\n'+facts
                request={'query_id':p['query_id'],'probe_id':p['id'],'stage':'ATOMIC','arm':mode,'prompt':prompt,
                    'decoder':'logits' if mode=='rgb_logits' else 'generate','image_ids':ids,'images':pixels,
                    'image_hashes':[hashlib.sha256(x).hexdigest() for x in pixels],'image_meta':metadata,
                    'limits':[5000,16],'as_of_ms':target,'input_type':'extra_ai_fact_control' if mode.startswith('oracle') else 'legal_rgb_directed_diagnostic',
                    'parent_requests':parent_n,'prefix_signature':pkg.manifest['signature']}
                raw=ledger.invoke(request,backend.generate)
                valid={'valid':True,'payload':json.loads(raw)} if mode=='rgb_logits' else validate_answer(raw)
                save(dst,{'probe_id':p['id'],'mode':mode,'request':{k:v for k,v in request.items() if k!='images'},'raw':raw,'validation':valid})
                save(root/'progress.json',{'issued':ledger.issued_count,'parent_issued':parent_n,'total':parent_n+ledger.issued_count,'last':p['id']+'_'+mode})
                print(canonical({'probe':p['id'],'mode':mode,'issued':ledger.issued_count,'valid':valid['valid']}),flush=True)
        save(root/'accesses.json',{'rule':'Each RGB request contains only time_ms<=its TARGET; uniform causal prefix sampling; no manually selected crop.'})
    finally: lock.unlink(missing_ok=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--core-root',required=True); parser.add_argument('--input',required=True)
    parser.add_argument('--output',required=True);parser.add_argument('--parent-ledger',required=True);parser.add_argument('--model')
    parser.add_argument('--mock',action='store_true');parser.add_argument('--block',choices=['primary','context'],default='primary');parser.add_argument('--ids',nargs='*')
    main(parser.parse_args())

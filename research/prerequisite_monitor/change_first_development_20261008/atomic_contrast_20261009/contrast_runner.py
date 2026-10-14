import argparse,hashlib,io,json,math,os,pathlib,subprocess,sys,time
H=pathlib.Path(__file__).resolve().parent;VALUES=('True','False','Unknown')
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def raw_text(text,eos):return text.split(eos)[0] if eos else text
def opposition(group):
    return {'opening':'The orange panel covers the rectangular top opening of the box.',
        'plate':'Both green-marked rail sections are fully exposed.',
        'grasp':'The blue cube is visibly separated from the robot gripper fingers.',
        'inside':'The blue cube is visibly outside the transparent box.'}[group]
def alias_readout(probs):
    aggregate={k:max(v)+math.log(sum(math.exp(x-max(v)) for x in v)) for k,v in probs.items()}
    return {'alias_logp':aggregate,'bare_logp':{k:v[0] for k,v in probs.items()},
        'bare_argmax':max(VALUES,key=lambda k:probs[k][0]),'alias_argmax':max(VALUES,key=lambda k:aggregate[k]),
        'bare_token_mass':sum(math.exp(v[0]) for v in probs.values()),'alias_token_mass':sum(math.exp(v) for v in aggregate.values()),'calibrated':False}
def save(p,x):
    p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);temp=p.with_suffix('.tmp');temp.write_text(canonical(x),encoding='utf-8');os.replace(temp,p)
def run(a):
    sys.path.insert(0,a.core)
    from experiments.prerequisite_probe.change_first_monitor.qwen_backend import QwenBackend,prepare_content
    from experiments.prerequisite_probe.change_first_monitor.prefix import PrefixPackage
    from experiments.prerequisite_probe.change_first_monitor.runner import RequestLedger,hash_obj
    config=json.loads((H/'config.json').read_text(encoding='utf-8'))
    hashes={n:sha(H/n) for n in ('contrast_runner.py','config.json')}
    if hashes!=json.loads((H/'freeze.json').read_text())['files']:raise RuntimeError('source changed')
    local_parents=[H.parent/'runs/diagnostic_20261009_window/delivery/window_v9/requests.jsonl',H.parent/'atomic_state_20261009/remote_verified/run/requests.jsonl']
    parent_paths=[local_parents[i] if a.mock else pathlib.Path(p['path']) for i,p in enumerate(config['parents'])]
    for p,path in zip(config['parents'],parent_paths):
        if sha(path)!=p['sha256']:raise RuntimeError('parent changed')
    parent_count=sum(sum(json.loads(s)['kind']=='issued' for s in path.read_text().splitlines() if s.strip()) for path in parent_paths)
    if parent_count!=80:raise RuntimeError('parent count changed')
    root=pathlib.Path(a.output);root.mkdir(parents=True,exist_ok=True);lock=root/'.run.lock';os.close(os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY))
    try:
        class Backend(QwenBackend):
            def generate(self,req):
                if a.mock:
                    self.last_metrics={'elapsed_seconds':0,'input_tokens':0,'output_tokens':0,'peak_vram_bytes':0,'hit_output_cap':False}
                    return canonical(alias_readout({'True':[-2.,-5.],'False':[-3.,-6.],'Unknown':[-4.,-7.]}))
                self._load();import torch
                started=time.perf_counter();content=prepare_content(req)
                # Reference layout: visual evidence first, query last. Both template arms use this identical content.
                content=content[1:]+content[:1]
                msg=[{'role':'user','content':content}]
                rendered=self.processor.apply_chat_template(msg,tokenize=False,add_generation_prompt=req['template']=='chat')
                if req['template']=='raw':
                    before=rendered;rendered=raw_text(rendered,self.processor.tokenizer.eos_token)
                    if rendered.count('<|image_pad|>')!=before.count('<|image_pad|>'):raise RuntimeError('raw EOS cut removed evidence')
                images=[x['image'] for x in content if x['type']=='image']
                inputs=self.processor(text=[rendered],images=images or None,return_tensors='pt')
                n=int(inputs['input_ids'].shape[-1]);ids={s:[self.processor.tokenizer.encode(s,add_special_tokens=False),self.processor.tokenizer.encode(' '+s,add_special_tokens=False)] for s in VALUES}
                if any(len(i)!=1 for variants in ids.values() for i in variants):raise RuntimeError('answer variant is not a single token')
                if n>5000:raise RuntimeError('input cap')
                torch.cuda.reset_peak_memory_stats()
                with torch.inference_mode():
                    out=self.model(**inputs.to('cuda'),logits_to_keep=1)
                    logp=torch.log_softmax(out.logits[0,-1,:].float(),dim=-1)
                    values={s:[float(logp[i[0]].item()) for i in variants] for s,variants in ids.items()}
                torch.cuda.synchronize()
                self.last_metrics={'elapsed_seconds':time.perf_counter()-started,'input_tokens':n,'output_tokens':0,'peak_vram_bytes':int(torch.cuda.max_memory_allocated()),
                    'hit_output_cap':False,'forward_count':1,'candidate_ids':ids,'rendered_text_sha256':hashlib.sha256(rendered.encode()).hexdigest(),
                    'rendered_prefix':rendered[:100],'encoded_sha256':hashlib.sha256(inputs['input_ids'].cpu().numpy().tobytes()).hexdigest(),
                    'image_grid_thw':inputs.get('image_grid_thw').tolist() if inputs.get('image_grid_thw') is not None else []}
                return canonical(alias_readout(values))
        backend=Backend(a.model or 'mock');ledger=RequestLedger(root,hash_obj({'series':'atomic_contrast_v1','hashes':hashes,'mock':a.mock,'model':backend.identity}),48)
        planned=config['requests'];planned=[r for r in planned if r['input_kind']==('rgb' if a.block=='rgb' else 'oracle')]
        if ledger.issued_count+len(planned)>48: # Resume uses exact IDs below; completed files are excluded.
            pending=[r for r in planned if not (root/'results'/f'{r["id"]}.json').exists()]
            if ledger.issued_count+len(pending)>48:raise RuntimeError('block cap')
        if not a.mock and subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():raise RuntimeError('GPU occupied')
        for item in planned:
            dst=root/'results'/f'{item["id"]}.json'
            if dst.exists():continue
            pkg=PrefixPackage(pathlib.Path(a.input)/item['query_id']);ref=item['ref'];target=pkg.handles[ref]['time_ms']
            ids=[ref] if item['input_kind']=='rgb' else [];pixels=[pkg.read(ref,'V3')] if ids else []
            prompt=f'At TARGET {ref} ({target} ms), judge this positive visible-state statement using only evidence at or before TARGET: {item["statement"]} '
            if item['input_kind']=='oracle':prompt+='Supplied visible fact at TARGET (extra-input diagnostic): '+item['fact']+' '
            prompt+='Decide whether the statement is True, False, or Unknown. Unknown means the evidence cannot decide. The answer is:'
            req={'query_id':item['query_id'],'probe_id':item['probe_id'],'condition_id':item['id'],'stage':'CONTRAST','arm':item['input_kind']+'_'+item['template']+'_'+item['polarity'],
                'prompt':prompt,'template':item['template'],'image_ids':ids,'images':pixels,'image_meta':[{'time_ms':target}] if ids else [],
                'image_hashes':[hashlib.sha256(x).hexdigest() for x in pixels],'limits':[5000,0],'as_of_ms':target,'parent_issued':parent_count,
                'input_type':'legal_rgb_directed_diagnostic' if ids else 'extra_ai_fact_control'}
            raw=ledger.invoke(req,backend.generate);payload=json.loads(raw)
            save(dst,{'probe_id':item['probe_id'],'polarity':item['polarity'],'template':item['template'],'input_kind':item['input_kind'],'raw':raw,'payload':payload,
                'request':{k:v for k,v in req.items() if k!='images'}})
            save(root/'progress.json',{'issued':ledger.issued_count,'parent':parent_count,'total':parent_count+ledger.issued_count,'last':item['id']})
            print(canonical({'id':item['id'],'issued':ledger.issued_count,'bare':payload['bare_argmax'],'alias':payload['alias_argmax']}),flush=True)
    finally:lock.unlink(missing_ok=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--core',required=True);p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--model');p.add_argument('--mock',action='store_true');p.add_argument('--block',choices=['rgb','oracle'],default='rgb');run(p.parse_args())

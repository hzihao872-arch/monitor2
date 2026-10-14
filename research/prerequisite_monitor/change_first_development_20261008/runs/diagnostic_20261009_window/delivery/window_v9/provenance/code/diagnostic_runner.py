"""Independent bounded diagnostics; never writes the old core or old runs."""
import argparse,hashlib,json,os,pathlib,sys,time
from contracts import validate
import prompts_short as P

HERE=pathlib.Path(__file__).resolve().parent

def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def durable(path,obj):
    path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp');temp.write_text(canonical(obj),encoding='utf-8');os.replace(temp,path)

def freeze_window(root,window):
    root=pathlib.Path(root);root.mkdir(parents=True,exist_ok=True)
    p=root/'window.json'
    if p.exists():
        if json.loads(p.read_text())!=window:raise ValueError('window/budget changed on resume')
    else:durable(p,window)

def run(a):
    sys.path.insert(0,str(pathlib.Path(a.core_root).resolve()))
    from experiments.prerequisite_probe.change_first_monitor.prefix import PrefixPackage
    from experiments.prerequisite_probe.change_first_monitor.runner import RequestLedger,hash_obj
    from experiments.prerequisite_probe.change_first_monitor.qwen_backend import QwenBackend
    from experiments.prerequisite_probe.change_first_monitor.backends import ScriptedBackend
    root=pathlib.Path(a.output);window=json.loads((HERE/'window.json').read_text());freeze_window(root,window)
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob('*.py') if p.name in ('diagnostic_runner.py','contracts.py','prompts_short.py')}
    mock_final={'state':{'goal_done':'unknown','direct_ready':'unknown','partial_preparation':'unknown'},'impacts':[],'net_effect':'unknown','reversal':'unknown','reason':'scripted mock only'}
    backend=QwenBackend(a.model) if a.backend=='qwen' else ScriptedBackend({
        'V1':{'context':'scripted neutral context','changes':[],'coverage':'no_observable_change'},
        'DRAFT':{'judgment':mock_final,'tests':[]},'VERIFY':{'facts':[]},'FINAL':mock_final})
    ledger=RequestLedger(root,hash_obj({'diagnostic':'v9-v10-frozen','hashes':hashes,'backend':backend.identity,'window':window}),window['max_requests'],window['deadline_epoch'],window['seal_buffer_seconds'])
    source=pathlib.Path(a.input);queries=json.loads((source/'queries.json').read_text())['queries']
    by_id={q['query_id']:q for q in queries}
    selected=[by_id[q] for q in a.query_ids]
    per_query={'compact1':1,'compact2':1,'directpixel':1,'paired':6}[a.mode]
    pending=sum(not (root/'results'/f'{a.mode}_{a.input_type}_{q["query_id"]}.json').exists() for q in selected)*per_query
    if ledger.issued_count+pending>window['max_requests']:raise RuntimeError('complete block does not fit request budget')
    estimate=pending*window['estimated_request_upper_seconds']+window['block_load_margin_seconds']
    if time.time()+estimate+window['seal_buffer_seconds']>=window['deadline_epoch']:raise RuntimeError('complete block does not fit time budget')
    oracle=json.loads(pathlib.Path(a.oracle).read_text()) if a.oracle else {}
    for q in selected:
        qid=q['query_id'];dest=root/'results'/f'{a.mode}_{a.input_type}_{qid}.json'
        if dest.exists():continue
        pkg=PrefixPackage(source/q['prefix_dir']);ids,proposal=pkg.shared_ids();handles={x:pkg.handles[x] for x in ids}
        if pkg.manifest['signature']!=q['prefix_signature']:raise ValueError('prefix identity mismatch')
        def call(stage,arm,prompt,visual=False,n=0,tests=None):
            image_ids=ids if visual else [];phase='V1' if stage=='V1' or a.mode=='directpixel' else 'V3'
            images=[pkg.read(x,phase) for x in image_ids]
            lim=(5000,768) if stage=='V1' or a.mode=='directpixel' else ((7500,768) if visual else (4000,512))
            request={'query_id':qid,'stage':stage,'arm':arm,'prompt':prompt,'image_ids':image_ids,'images':images,
                     'image_hashes':[hashlib.sha256(b).hexdigest() for b in images],
                     'image_meta':[{k:handles[x].get(k) for k in ('time_ms','parent_id','crop_xyxy')} for x in image_ids],
                     'limits':lim,'prefix_signature':pkg.manifest['signature'],'diagnostic_input_type':a.input_type}
            raw=ledger.invoke(request,backend.generate)
            check=validate(stage,raw,handles,n,len(tests or []))
            if stage=='VERIFY' and check['valid']:
                for f in check['payload']['facts']:
                    if f['ref']!=tests[f['test']]['ref']:
                        check['valid']=False;check['errors'].append('fact_time_ref_mismatch')
            return {'raw':raw,'validation':check,'request':{k:v for k,v in request.items() if k!='images'}}
        prefix_ids=canonical({x:handles[x]['time_ms'] for x in ids})
        if a.mode.startswith('compact'):
            prompt=P.V1_BASE+(P.V1_SECOND if a.mode=='compact2' else '')+P.V1_SCHEMA+'\nEVIDENCE_TIME_MS: '+prefix_ids
            row={'v1':call('V1',a.mode,prompt,True),'mode':a.mode,'query_id':qid,'accesses':pkg.accesses}
        elif a.mode=='directpixel':
            prompt=P.SEMANTICS+'\nGOAL: '+q['goal']+'\nCAPABILITIES: '+P.CAPABILITIES+'\nDirectly judge these chronological pixels. '
            prompt+='Assign host change indices 0..2 only to visible changes in chronological order; list their effects in impacts. '
            prompt+=P.FINAL_SCHEMA+'\nEVIDENCE_TIME_MS: '+prefix_ids
            row={'direct':call('FINAL','D_RGB',prompt,True,3),'query_id':qid,'mode':a.mode,'accesses':pkg.accesses}
        else:
            if a.input_type=='oracle':observed=oracle[qid];input_provenance='AI pixel-reviewed corrected changes: privileged diagnostic only'
            else:
                src=root/'results'/f'{a.v1_mode}_predicted_{qid}.json'
                parent=json.loads(src.read_text());vc=parent['v1']['validation']
                if not vc['valid']:
                    durable(dest,{'query_id':qid,'mode':a.mode,'input_type':a.input_type,'skipped':'invalid_v1','parent':str(src),'all_planned_slots':6});continue
                observed=vc['payload'];input_provenance='compact V1 model prediction'
            n=len(observed['changes']);arms={}
            base=P.SEMANTICS+'\nGOAL: '+q['goal']+'\nCAPABILITIES: '+P.CAPABILITIES+'\nCHANGES (indices assigned by host): '+canonical(observed)+'\nEVIDENCE_TIME_MS: '+prefix_ids
            for arm in ('D','C'):
                role=('Directly predict goal state and change impacts from supplied observations. Then give a few neutral visual checks of that direct judgment.' if arm=='D' else
                      'Reason only about each supplied actual change and its local relation to the goal. Bind to the correct goal object/region, consider a competing explanation, and give a positive visible predicate that can falsify the relation. Then predict state and impacts. Do not enumerate prerequisites.')
                draft=call('DRAFT',arm+'_'+a.input_type,base+'\n'+role+'\nFINAL_CONTRACT: '+P.FINAL_SCHEMA+'\nDRAFT_CONTRACT: '+P.DRAFT_SCHEMA,n=n)
                if not draft['validation']['valid']:
                    arms[arm]={'draft':draft,'first_failure':'draft','unexecuted_slots':2};continue
                tests=draft['validation']['payload']['tests']
                current=max((x for x in ids if not handles[x].get('parent_id')),key=lambda x:handles[x]['time_ms'])
                tests=tests+[{'change':-1,'ref':current,'predicate':'The final goal is visibly achieved at this time: '+q['goal']}]
                verify_input={'changes':observed,'tests':[{**t,'test':i} for i,t in enumerate(tests)]}
                verify_prompt='Fresh pixel verification in a new context. Provisional descriptions may be wrong. '\
                    +'\nGOAL: '+q['goal']+'\nNEUTRAL_INPUT: '+canonical(verify_input)+'\n'+P.VERIFY_SCHEMA
                verified=call('VERIFY',arm+'_'+a.input_type,verify_prompt,True,n,tests)
                if not verified['validation']['valid']:
                    arms[arm]={'draft':draft,'verify':verified,'first_failure':'verify','unexecuted_slots':1};continue
                # Both arms use exactly the same readout prompt. Provisional judgment is never evidence.
                final_prompt=P.SEMANTICS+'\nGOAL: '+q['goal']+'\nCAPABILITIES: '+P.CAPABILITIES+'\nCHANGES: '+canonical(observed)
                final_prompt+='\nTESTS: '+canonical(tests)+'\nVERIFIED_FACTS: '+canonical(verified['validation']['payload'])
                final_prompt+='\nRead only verified facts at their exact times. A rejected beneficial interpretation alone is not harmful. Use unknown if required evidence is missing. '+P.FINAL_SCHEMA
                conclusion=call('FINAL',arm+'_'+a.input_type,final_prompt,n=n)
                arms[arm]={'draft':draft,'verify':verified,'final':conclusion,'first_failure':None if conclusion['validation']['valid'] else 'final'}
            row={'query_id':qid,'mode':a.mode,'input_type':a.input_type,'input_provenance':input_provenance,'observed':observed,'arms':arms,'accesses':pkg.accesses}
        durable(dest,row)
        durable(root/'progress.json',{'issued_requests':ledger.issued_count,'max_requests':window['max_requests'],'results':len(list((root/'results').glob('*.json'))),'last_query':qid,'mode':a.mode})
        print(canonical({'query_id':qid,'mode':a.mode,'input_type':a.input_type,'issued':ledger.issued_count}),flush=True)
    return {'issued':ledger.issued_count,'max_requests':window['max_requests']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--core-root',required=True);p.add_argument('--input',required=True);p.add_argument('--output',required=True)
    p.add_argument('--backend',choices=['qwen','scripted'],default='qwen');p.add_argument('--model');p.add_argument('--mode',choices=['compact1','compact2','directpixel','paired'],required=True)
    p.add_argument('--input-type',choices=['predicted','oracle'],default='predicted');p.add_argument('--oracle');p.add_argument('--v1-mode',default='compact1');p.add_argument('--query-ids',nargs='+',required=True)
    print(canonical(run(p.parse_args())))

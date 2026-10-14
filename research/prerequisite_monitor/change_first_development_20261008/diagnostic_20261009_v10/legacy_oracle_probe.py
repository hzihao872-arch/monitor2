"""Corrected changes through unchanged v8 downstream contracts; oracle only."""
import argparse,hashlib,json,pathlib,sys,time
from diagnostic_runner import durable,freeze_window

def convert(observed):
    entities={c['object']:f'o{i}' for i,c in enumerate(observed['changes'])}
    context=[{'entity_id':'scene','description':observed['context'],'region_id':'f0000','visible_relation':'initial visible scene'}]
    context += [{'entity_id':eid,'description':name,'region_id':'f0000','visible_relation':'visible in supplied scene'} for name,eid in entities.items()]
    changes=[{'change_id':f'e{i+1}','entity_ids':[entities[c['object']]],'before_refs':[c['b']],'after_refs':[c['a']],
              'before':c['before'],'after':c['after'],'observation':'observed','status':'closed_event'} for i,c in enumerate(observed['changes'])]
    return {'initial_context':context,'changes':changes,'coverage':observed['coverage'],'uncertainty':[]}

def run(a):
    sys.path.insert(0,str(pathlib.Path(a.core_root).resolve()))
    from experiments.prerequisite_probe.change_first_monitor.pipeline import Pipeline
    from experiments.prerequisite_probe.change_first_monitor.prefix import PrefixPackage
    from experiments.prerequisite_probe.change_first_monitor.contracts import validate_payload
    from experiments.prerequisite_probe.change_first_monitor.runner import RequestLedger
    from experiments.prerequisite_probe.change_first_monitor.qwen_backend import QwenBackend
    here=pathlib.Path(__file__).resolve().parent;root=pathlib.Path(a.output);window=json.loads((here/'window.json').read_text());freeze_window(root,window)
    identity=json.loads((here/'budget_parent.json').read_text())['protocol_id'];backend=QwenBackend(a.model)
    ledger=RequestLedger(root,identity,window['max_requests'],window['deadline_epoch'],window['seal_buffer_seconds'])
    source=pathlib.Path(a.input);queries={q['query_id']:q for q in json.loads((source/'queries.json').read_text())['queries']};oracle=json.loads(pathlib.Path(a.oracle).read_text())
    pending=[q for q in a.query_ids if not (root/'results'/f'legacy_oracle_{q}.json').exists()]
    if ledger.issued_count+6*len(pending)>window['max_requests']:raise RuntimeError('global request budget')
    if time.time()+6*len(pending)*36.54+120+1200>=window['deadline_epoch']:raise RuntimeError('global deadline/seal margin')
    probe_hash=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()
    class OraclePipeline(Pipeline):
        def _call(self,package,stage,arm,goal,context,payload,ids):
            if stage=='V1':
                obj=convert(oracle[self.query_id]);evid=set(self.image_ids)
                check=validate_payload('V1',obj,{'evidence_ids':evid,'evidence_times':{i:package.handles[i]['time_ms'] for i in evid}})
                if not check['valid']:raise ValueError('invalid oracle bridge: '+str(check))
                return {'raw':json.dumps(obj),'payload':obj,'validation':check,'oracle_input':True,'model_cost':0,
                        'provenance':'AI supplied-pixel pre-audit; extra input; not a model V1 prediction'}
            return super()._call(package,stage,arm,goal,context,payload,ids)
    for qid in pending:
        q=queries[qid];pkg=PrefixPackage(source/q['prefix_dir'])
        if pkg.manifest['signature']!=q['prefix_signature']:raise ValueError('prefix identity')
        def invoke(req):
            req['diagnostic_input_type']='oracle_legacy';req['probe_sha256']=probe_hash
            return ledger.invoke(req,backend.generate)
        pipe=OraclePipeline(backend,invoke);result=pipe.run(pkg,q['goal'],arms=('D4','C4'),query_id=qid)
        result.update(query_id=qid,mode='legacy_oracle',input_type='oracle_legacy',actual_v1_model_requests=0,
                      note='v8 downstream prompts/schema unchanged; old L2/V3/L4 limits; no compact-chain repair')
        durable(root/'results'/f'legacy_oracle_{qid}.json',result)
        print(json.dumps({'qid':qid,'issued':ledger.issued_count,'first_failure':{k:v['first_failure'] for k,v in result['arms'].items()}}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--core-root',required=True);p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--oracle',required=True);p.add_argument('--model',required=True);p.add_argument('--query-ids',nargs='+',required=True);run(p.parse_args())

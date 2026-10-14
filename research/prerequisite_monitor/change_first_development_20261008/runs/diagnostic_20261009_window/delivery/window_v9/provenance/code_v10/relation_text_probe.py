"""Remaining fixed oracle cases, text only after failed visual interfaces."""
import argparse,hashlib,json,pathlib,sys,time
from diagnostic_runner import durable,freeze_window
from legacy_oracle_probe import convert
from contracts import validate
import prompts_short as P

def run(a):
    sys.path.insert(0,str(pathlib.Path(a.core_root).resolve()))
    from experiments.prerequisite_probe.change_first_monitor.pipeline import Pipeline
    from experiments.prerequisite_probe.change_first_monitor.prefix import PrefixPackage
    from experiments.prerequisite_probe.change_first_monitor.runner import RequestLedger
    from experiments.prerequisite_probe.change_first_monitor.qwen_backend import QwenBackend
    root=pathlib.Path(a.output);here=pathlib.Path(__file__).resolve().parent;window=json.loads((here/'window.json').read_text());freeze_window(root,window)
    backend=QwenBackend(a.model);identity=json.loads((here/'budget_parent.json').read_text())['protocol_id']
    ledger=RequestLedger(root,identity,window['max_requests'],window['deadline_epoch'],1200)
    source=pathlib.Path(a.input);qs={q['query_id']:q for q in json.loads((source/'queries.json').read_text())['queries']};oracle=json.loads(pathlib.Path(a.oracle).read_text())
    pending=[q for q in a.query_ids if not (root/'results'/f'oracle_text_{q}.json').exists()]
    count=sum(1 if (root/'results'/f'legacy_oracle_{q}.json').exists() else 3 for q in pending)
    if ledger.issued_count+count>window['max_requests']:raise RuntimeError('global budget')
    if time.time()+count*36.54+120+1200>=window['deadline_epoch']:raise RuntimeError('global deadline')
    h=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()
    for qid in pending:
        q=qs[qid];pkg=PrefixPackage(source/q['prefix_dir']);ids,proposal=pkg.shared_ids();obs=convert(oracle[qid])
        def invoke(req):
            req['diagnostic_input_type']='oracle_text_only';req['probe_sha256']=h
            return ledger.invoke(req,backend.generate)
        relations={}
        if not (root/'results'/f'legacy_oracle_{qid}.json').exists():
            pipe=Pipeline(backend,invoke);pipe.query_id=qid;pipe.image_ids=ids;pipe.proposal=proposal
            for arm in ('D4','C4'):
                relations[arm]=pipe._call(pkg,'L2',arm,q['goal'],obs['initial_context'],obs,{'evidence_ids':set(ids),'change_ids':{c['change_id'] for c in obs['changes']}})
        else:relations={'reused_first_case':'unchanged L2 already sealed in legacy_oracle result, no repeated requests'}
        prompt=P.SEMANTICS+'\nGOAL: '+q['goal']+'\nCAPABILITIES: '+P.CAPABILITIES
        prompt+='\nCHANGES (host indices): '+json.dumps(oracle[qid],sort_keys=True)+'\nDirectly judge the supplied visible observations. '+P.FINAL_SCHEMA
        request={'query_id':qid,'stage':'FINAL','arm':'D_ORACLE_TEXT','prompt':prompt,'images':[],'image_ids':[],'image_meta':[],'image_hashes':[],
                 'limits':(4000,512),'prefix_signature':pkg.manifest['signature'],'diagnostic_input_type':'oracle_text_only','probe_sha256':h}
        raw=ledger.invoke(request,backend.generate);check=validate('FINAL',raw,pkg.handles,len(oracle[qid]['changes']))
        durable(root/'results'/f'oracle_text_{qid}.json',{'query_id':qid,'mode':'oracle_text','relations':relations,'direct_text':{'raw':raw,'validation':check},
                     'note':'extra-input diagnostic, no new visual verification; main compact method remains frozen'})
        print(json.dumps({'qid':qid,'issued':ledger.issued_count,'direct_valid':check['valid']}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--core-root',required=True);p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--model',required=True);p.add_argument('--oracle',required=True);p.add_argument('--query-ids',nargs='+',required=True);run(p.parse_args())

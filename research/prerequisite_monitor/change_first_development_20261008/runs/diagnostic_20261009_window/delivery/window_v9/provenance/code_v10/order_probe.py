"""One-factor control: reorder the same pixels, with the exact frozen direct prompt."""
import argparse,hashlib,json,pathlib,sys,time
from contracts import validate
from diagnostic_runner import durable,freeze_window

def run(a):
    sys.path.insert(0,str(pathlib.Path(a.core_root).resolve()))
    from experiments.prerequisite_probe.change_first_monitor.prefix import PrefixPackage
    from experiments.prerequisite_probe.change_first_monitor.runner import RequestLedger
    from experiments.prerequisite_probe.change_first_monitor.qwen_backend import QwenBackend
    here=pathlib.Path(__file__).resolve().parent;root=pathlib.Path(a.output);window=json.loads((here/'window.json').read_text())
    freeze_window(root,window);identity=json.loads((here/'budget_parent.json').read_text())['protocol_id']
    backend=QwenBackend(a.model);ledger=RequestLedger(root,identity,window['max_requests'],window['deadline_epoch'],window['seal_buffer_seconds'])
    pending=[q for q in a.query_ids if not (root/'results'/f'order_probe_predicted_{q}.json').exists()]
    if ledger.issued_count+len(pending)>window['max_requests']:raise RuntimeError('global budget exceeded')
    if time.time()+len(pending)*36.54+120+1200>=window['deadline_epoch']:raise RuntimeError('block cannot fit')
    source=pathlib.Path(a.input);queries={q['query_id']:q for q in json.loads((source/'queries.json').read_text())['queries']}
    for qid in pending:
        originals=[r for r in ledger.records if r['kind']=='issued' and r['request']['query_id']==qid and r['request']['arm']=='D_RGB']
        if len(originals)!=1:raise ValueError('unique original direct request required')
        original=originals[0];request=dict(original['request']);pkg=PrefixPackage(source/queries[qid]['prefix_dir'])
        indices=sorted(range(len(request['image_ids'])),key=lambda i:(request['image_meta'][i]['time_ms'],bool(request['image_meta'][i].get('parent_id')),i))
        for key in ('image_ids','image_meta','image_hashes'):request[key]=[request[key][i] for i in indices]
        if request['image_ids']==original['request']['image_ids']:raise ValueError('no ordering treatment')
        request['images']=[pkg.read(i,'V1') for i in request['image_ids']]
        request['arm']='D_RGB_ORDER';request['diagnostic_control']='same pixels and exact prompt, chronological full/crop order'
        request['probe_sha256']=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()
        if sorted(request['image_hashes'])!=sorted(original['request']['image_hashes']):raise ValueError('pixel multiset changed')
        raw=ledger.invoke(request,backend.generate)
        check=validate('FINAL',raw,{i:pkg.handles[i] for i in request['image_ids']},3)
        row={'query_id':qid,'mode':'order_probe','direct':{'raw':raw,'validation':check},'source_request_id':original['request_id'],'accesses':pkg.accesses,
             'control':'same-image order diagnostic only; not a third method revision'}
        durable(root/'results'/f'order_probe_predicted_{qid}.json',row)
        print(json.dumps({'qid':qid,'issued':ledger.issued_count,'valid':check['valid']}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--core-root',required=True);p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--model',required=True);p.add_argument('--query-ids',nargs='+',required=True);run(p.parse_args())

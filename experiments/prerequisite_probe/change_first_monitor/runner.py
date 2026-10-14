"""Append-only, bounded, resumable per-request runner."""
import argparse
import hashlib
import json
import os
import time
from pathlib import Path

from .backends import ScriptedBackend
from .pipeline import Pipeline
from .prefix import PrefixPackage


class BudgetExceeded(RuntimeError): pass
class AmbiguousRequest(RuntimeError): pass


def canonical(data):
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(',', ':'), default=str)


def hash_obj(data):
    return hashlib.sha256(canonical(data).encode()).hexdigest()


class RequestLedger:
    def __init__(self, directory, protocol_id, max_requests=96, deadline=None, seal_buffer_seconds=0):
        self.root=Path(directory)
        if self.root.exists() and not (self.root/'run_identity.json').exists():
            unexpected={p.name for p in self.root.iterdir()}-{'window.json','.run.lock','preflight.json'}
            if unexpected:
                raise FileExistsError('nonempty directory without run identity')
        self.root.mkdir(parents=True,exist_ok=True)
        self.meta=self.root/'run_identity.json'
        if self.meta.exists():
            if json.loads(self.meta.read_text(encoding='utf-8'))['protocol_id'] != protocol_id:
                raise ValueError('run protocol identity changed')
        else:
            self.meta.write_text(canonical({'protocol_id':protocol_id}),encoding='utf-8')
        self.max_requests=max_requests
        self.deadline=deadline
        self.seal_buffer_seconds=seal_buffer_seconds
        self.log=self.root/'requests.jsonl'
        self.records=[]
        if self.log.exists():
            for line in self.log.read_text(encoding='utf-8').splitlines():
                if line.strip():
                    self.records.append(json.loads(line))

    @property
    def issued_count(self):
        return sum(r['kind']=='issued' for r in self.records)

    def _append(self, row):
        with open(self.log,'a',encoding='utf-8') as f:
            f.write(canonical(row)+'\n')
            f.flush()
            os.fsync(f.fileno())
        self.records.append(row)

    def invoke(self, request, backend_call):
        safe={k:v for k,v in request.items() if k!='images'}
        rid=hash_obj(safe)
        matching=[r for r in self.records if r['request_id']==rid]
        complete=[r for r in matching if r['kind']=='completed']
        if complete:
            return complete[-1]['raw']
        if matching:
            raise AmbiguousRequest(f'issued request has no durable response: {rid}')
        if self.issued_count >= self.max_requests:
            raise BudgetExceeded('request cap reached')
        if self.deadline is not None and time.time()+self.seal_buffer_seconds >= self.deadline:
            raise BudgetExceeded('deadline/seal buffer reached')
        self._append({'kind':'issued','request_id':rid,'request':safe,'wall_time':time.time()})
        start=time.monotonic()
        try:
            raw=backend_call(request)
        except Exception as exc:
            self._append({'kind':'failed','request_id':rid,'error':type(exc).__name__+': '+str(exc)[:400],
                          'seconds':time.monotonic()-start,'wall_time':time.time()})
            raise
        metrics=getattr(getattr(backend_call,'__self__',None),'last_metrics',None)
        self._append({'kind':'completed','request_id':rid,'raw':raw,'metrics':metrics,
                      'seconds':time.monotonic()-start,'wall_time':time.time()})
        return raw


def unknown_answers():
    return {'V1':{'initial_context':[],'changes':[],'coverage':'no_observable_change','uncertainty':[]},
            'L2':{'claims':[],'tests':[]},
            'V3':{'facts':[],'change_checks':[],'goal_facts':[],'new_unverified_changes':[],'missing':[]},
            'L4':{'claim_results':[],'events':[],'state':{'goal_done':'unknown','direct_ready':'unknown','partial_preparation':'unknown'},
                  'state_fact_ids':{'goal_done':[],'direct_ready':[],'partial_preparation':[]},
                  'net_effect':'unknown','reversal':'unknown','unresolved':['scripted_no_visual_judgment']}}


def run(input_dir, output_dir, arms, backend, max_requests, deadline=None, seal_buffer_seconds=0,max_queries=None):
    source=Path(input_dir)
    queries=json.loads((source/'queries.json').read_text(encoding='utf-8'))['queries']
    if len({q['query_id'] for q in queries})!=len(queries):
        raise ValueError('duplicate query')
    if max_queries is not None and (max_queries<1 or max_queries>len(queries)):
        raise ValueError('invalid query block limit')
    output=Path(output_dir)
    if output.resolve().is_relative_to(source.resolve()):
        raise ValueError('output must be outside model input')
    code_root=Path(__file__).resolve().parent
    code_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in code_root.glob('*.py')}
    code_hashes.update({'protocol/'+p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in (code_root/'protocol').glob('*') if p.is_file()})
    identity=hash_obj({'query_manifest':(source/'queries.json').read_bytes().hex(),
                       'arms':arms,'backend':backend.identity,'protocol':'change-first-v1',
                       'code_hashes':code_hashes})
    ledger=RequestLedger(output,identity,max_requests,deadline,seal_buffer_seconds)
    results_dir=output/'results'
    results_dir.mkdir(exist_ok=True)
    for query in queries[:max_queries]:
        qid=query['query_id']
        result_file=results_dir/(qid+'.json')
        if result_file.exists():
            continue
        package=PrefixPackage(source/query['prefix_dir'])
        if package.manifest['signature']!=query['prefix_signature'] or package.manifest['as_of_ms']!=query['as_of_ms']:
            raise ValueError('prefix identity mismatch')
        pipe=Pipeline(backend, invoke=lambda request: ledger.invoke(request,backend.generate))
        result=pipe.run(package,query['goal'],arms=arms,query_id=qid)
        result['query_id']=qid
        result['backend_identity']=backend.identity
        temp=result_file.with_suffix('.tmp')
        temp.write_text(canonical(result),encoding='utf-8')
        os.replace(temp,result_file)
        progress={'queries_total':len(queries),'results_complete':len(list(results_dir.glob('*.json'))),
                  'issued_requests':ledger.issued_count,'max_requests':max_requests,'backend_identity':backend.identity}
        progress_tmp=output/'progress.tmp'
        progress_tmp.write_text(canonical(progress),encoding='utf-8')
        os.replace(progress_tmp,output/'progress.json')
    return {'queries_total':len(queries),'queries_considered':max_queries or len(queries),
            'issued_requests':ledger.issued_count,'completed_results':len(list(results_dir.glob('*.json')))}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--backend',choices=['scripted','qwen'],required=True)
    p.add_argument('--input',required=True)
    p.add_argument('--arms',nargs='+',default=['D4','K4','C4'])
    p.add_argument('--max-requests',type=int,default=96)
    p.add_argument('--max-queries',type=int)
    p.add_argument('--output',required=True)
    p.add_argument('--model')
    p.add_argument('--deadline-epoch',type=float)
    p.add_argument('--seal-buffer-minutes',type=float,default=15)
    a=p.parse_args()
    if a.backend=='scripted':
        backend=ScriptedBackend(unknown_answers())
    else:
        if not a.model:
            p.error('--model is required for qwen')
        from .qwen_backend import QwenBackend
        backend=QwenBackend(a.model)
    print(canonical(run(a.input,a.output,a.arms,backend,a.max_requests,a.deadline_epoch,a.seal_buffer_minutes*60,a.max_queries)))


if __name__=='__main__':
    main()

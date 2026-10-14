"""Capped V1-only diagnostic; deliberately outside the frozen model bundle."""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from experiments.prerequisite_probe.change_first_monitor.backends import ScriptedBackend
from experiments.prerequisite_probe.change_first_monitor.pipeline import LIMITS, Pipeline
from experiments.prerequisite_probe.change_first_monitor.prefix import PrefixPackage
from experiments.prerequisite_probe.change_first_monitor.runner import RequestLedger, canonical, hash_obj, unknown_answers


def run(input_dir, output_dir, backend, max_queries, deadline_epoch=None):
    source = Path(input_dir)
    queries = json.loads((source / 'queries.json').read_text(encoding='utf-8'))['queries']
    if not 1 <= max_queries <= len(queries) <= 8:
        raise ValueError('invalid query count')
    LIMITS['V1'] = (5000, 1536)
    output = Path(output_dir)
    identity = hash_obj({
        'diagnostic': 'v1-only-output-1536-v1',
        'queries_sha256': hashlib.sha256((source / 'queries.json').read_bytes()).hexdigest(),
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'backend': backend.identity,
        'model_code_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted((ROOT / 'experiments/prerequisite_probe/change_first_monitor').glob('*.py'))},
    })
    ledger = RequestLedger(output, identity, max_requests=8, deadline=deadline_epoch, seal_buffer_seconds=900)
    results = output / 'results'
    results.mkdir(exist_ok=True)
    for query in queries[:max_queries]:
        qid = query['query_id']
        dest = results / (qid + '.json')
        if dest.exists():
            continue
        package = PrefixPackage(source / query['prefix_dir'])
        if package.manifest['signature'] != query['prefix_signature']:
            raise ValueError('prefix mismatch')
        pipe = Pipeline(backend, invoke=lambda request: ledger.invoke(request, backend.generate))
        pipe.query_id = qid
        pipe.image_ids, pipe.proposal = package.shared_ids()
        v1 = pipe._call(package, 'V1', 'shared', '', None, None, {'evidence_ids': set(pipe.image_ids)})
        row = {'query_id': qid, 'v1': v1, 'accesses': package.accesses,
               'diagnostic': 'V1-only, output cap 1536; not the original S1 budget'}
        tmp = dest.with_suffix('.tmp')
        tmp.write_text(canonical(row), encoding='utf-8')
        os.replace(tmp, dest)
        progress = {'queries_complete': len(list(results.glob('*.json'))),
                    'issued_requests': ledger.issued_count, 'max_requests': 8}
        tmp = output / 'progress.tmp'
        tmp.write_text(canonical(progress), encoding='utf-8')
        os.replace(tmp, output / 'progress.json')
    return {'queries_complete': len(list(results.glob('*.json'))), 'issued_requests': ledger.issued_count}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--backend', choices=['scripted', 'qwen'], required=True)
    parser.add_argument('--model')
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--max-queries', type=int, required=True)
    parser.add_argument('--deadline-epoch', type=float)
    args = parser.parse_args()
    if args.backend == 'scripted':
        model = ScriptedBackend(unknown_answers())
    else:
        if not args.model:
            parser.error('--model is required for qwen')
        from experiments.prerequisite_probe.change_first_monitor.qwen_backend import QwenBackend
        model = QwenBackend(args.model)
    print(canonical(run(args.input, args.output, model, args.max_queries, args.deadline_epoch)))

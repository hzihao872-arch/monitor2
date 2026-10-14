"""Private evaluation. Never ship this module or its labels to the model host."""
import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

CLASSES=('beneficial','harmful','irrelevant','mixed')


def score_events(reference, predicted, tolerance_ms=1000):
    tp=Counter(); fp=Counter(); fn=Counter(); used=set(); answered=0
    # Match by entity/time only, before consulting effect labels.
    for truth in reference:
        possible=[(abs(p['time_ms']-truth['time_ms']),i) for i,p in enumerate(predicted)
                  if i not in used and p.get('entity')==truth.get('entity')
                  and abs(p['time_ms']-truth['time_ms'])<=tolerance_ms]
        if not possible:
            fn[truth['impact']]+=1
            continue
        _,idx=min(possible)
        used.add(idx)
        effect=predicted[idx].get('impact','unknown')
        if effect in CLASSES:
            answered+=1
            if effect==truth['impact']:
                tp[effect]+=1
            else:
                fp[effect]+=1; fn[truth['impact']]+=1
        else:
            fn[truth['impact']]+=1
    for i,p in enumerate(predicted):
        if i not in used and p.get('impact') in CLASSES:
            fp[p['impact']]+=1
    f1={c:(2*tp[c]/(2*tp[c]+fp[c]+fn[c]) if 2*tp[c]+fp[c]+fn[c] else None) for c in CLASSES}
    present=[x for x in f1.values() if x is not None]
    return {'tp':dict(tp),'fp':dict(fp),'fn':dict(fn),'coverage':answered/len(reference) if reference else None,
            'macro_f1':sum(present)/len(present) if present else None,
            'reference_events':len(reference),'predicted_events':len(predicted),
            'no_event_correct':not reference and not predicted}


def score_state(reference,predicted):
    if len(reference)!=len(predicted):
        raise ValueError('unaligned states')
    decidable=[(r,p) for r,p in zip(reference,predicted) if r in ('true','false')]
    n=len(decidable)
    answered=[(r,p) for r,p in decidable if p in ('true','false')]
    correct=sum(r==p for r,p in answered)
    return {'decidable':n,'answered':len(answered),'correct':correct,
            'coverage':len(answered)/n if n else None,
            'selective_accuracy':correct/len(answered) if answered else None,
            'all_decidable_accuracy':correct/n if n else None}


def cluster_bootstrap(rows,method,baseline,iterations=10000,seed=0):
    groups=defaultdict(list)
    for r in rows:
        groups[r['cluster']].append(r)
    keys=sorted(groups)
    if not keys:
        raise ValueError('no clusters')
    def metric(selected):
        return sum(sum(x[method]-x[baseline] for x in groups[k])/len(groups[k]) for k in selected)/len(selected)
    rng=random.Random(seed)
    draws=sorted(metric([rng.choice(keys) for _ in keys]) for _ in range(iterations))
    return {'clusters':len(keys),'difference':metric(keys),'low':draws[int(.025*(iterations-1))],
            'high':draws[int(.975*(iterations-1))],'unit':'cluster','iterations':iterations}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--labels',required=True)
    p.add_argument('--predictions',required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args()
    labels=[json.loads(x) for x in Path(a.labels).read_text(encoding='utf-8').splitlines() if x.strip()]
    predictions={x['query_id']:x for x in (json.loads(y) for y in Path(a.predictions).read_text(encoding='utf-8').splitlines() if y.strip())}
    report=[]
    for row in labels:
        pred=predictions.get(row['query_id'],{})
        report.append({'query_id':row['query_id'],'event_scores':score_events(row['visual_reference']['events'],pred.get('events',[])),
                       'visual_judgability':row['visual_judgability'],'annotation_status':row['annotation_status']})
    Path(a.output).write_text(json.dumps({'scope':'private_development_or_blind_as_labeled','rows':report},indent=2),encoding='utf-8')


if __name__=='__main__':main()

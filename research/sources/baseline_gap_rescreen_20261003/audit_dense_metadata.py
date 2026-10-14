"""Audit released labels and provenance; no inference or empirical error attribution."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import json
import re

b=Path(__file__).resolve().parent
rows=json.loads((b/'dense_3frame_test.json').read_text(encoding='utf-8'))
manifest=json.loads((b/'dense_data_manifest.json').read_text(encoding='utf-8'))
groups=defaultdict(list)
for row in rows:
    path=row['images'][-1]
    match=re.fullmatch(r'data/([^/]+)/(.+)_frame_(\d+)\.jpg',path)
    assert match,path
    source,episode,frame=match.groups()
    response=row['conversation'][-1]['value']
    reason=re.search(r'<think>\s*(.*?)\s*</think>',response,re.S).group(1)
    reward=float(response.split('</think>')[-1].strip())
    assert len(row['images'])==3
    groups[source].append({'episode':episode,'frame':int(frame),'reward':reward,'reason':reason})
summary={s:{'frame_samples':len(xs),'fraction':len(xs)/len(rows),
    'filename_episode_groups':len({x['episode'] for x in xs}),
    'reason_counts':dict(Counter(x['reason'] for x in xs))} for s,xs in groups.items()}
paper_mae={'droid':.259,'isaac':.081,'robosuite':.051,'libero':.044}
pooled=sum(paper_mae[s]*len(xs) for s,xs in groups.items())/len(rows)
result={'model_inference_run':False,'total_test_frame_samples':len(rows),'sources':summary,
    'out_of_range_reward_labels': [{'source':s,**x} for s,xs in groups.items() for x in xs if not 0<=x['reward']<=1],
    'manifest_metadata':manifest['metadata'], 'manifest_assignment_count':len(manifest['assignments']),
    'paper_total_episodes':26579,'paper_source_mae':paper_mae,
    'weighted_average_of_rounded_paper_mae_using_release_frame_counts':pooled,
    'unweighted_source_mae_average':sum(paper_mae.values())/4,
    'interpretation':'Arithmetic compatibility, not proof that release split/checkpoint produced Table 1. Error contributions are estimated from rounded published source MAEs, not recomputed predictions.',
    'estimated_droid_share_of_total_absolute_error':.259*summary['droid']['frame_samples']/(pooled*len(rows)),
    'release_format_issue':'Test labels contain not smooth while model prompt lists smooth. Treat as interface/data consistency issue, not a discovered scientific model failure.'}
checked=[]
for entry in json.loads((b/'fetch_manifest.json').read_text(encoding='utf-8')):
    if 'sha256' not in entry: continue
    data=(b/entry['file']).read_bytes()
    assert len(data)==entry['bytes']
    assert hashlib.sha256(data).hexdigest()==entry['sha256']
    checked.append(entry['file'])
result['verified_download_count']=len(checked)
result['downloaded_bytes']=sum((b/f).stat().st_size for f in checked)
(b/'dense_metadata_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))

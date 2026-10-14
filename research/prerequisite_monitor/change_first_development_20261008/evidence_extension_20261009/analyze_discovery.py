import json,pathlib,sys
H=pathlib.Path(__file__).resolve().parent;B=H.parent;D=B/(sys.argv[1]+'_20261009');root=D/'remote_verified/run';rows=[json.loads(p.read_text()) for p in (root/'results').glob('*.json')];old={p.stem:json.loads(p.read_text()) for p in (B/'dense_discovery_20261009/remote_verified/run/results').glob('*.json')};text=[];changes=0
for r in sorted(rows,key=lambda r:r['query_id']):
 o=old[r['query_id']];assert all(r['request'][k]==o['request'][k] for k in ('prompt','image_ids','image_hashes','image_meta','as_of_ms'));text.extend(['## '+r['query_id'],'valid='+str(r['validation']['valid'])])
 if r['validation']['valid']:
  changes+=len(r['validation']['payload']['changes'])
  for c in r['validation']['payload']['changes']:text.append(f"{c['b']}→{c['a']} {c['object']}: {c['before']} → {c['after']}")
 else:text.append(r['raw'])
summary={'n':len(rows),'strict_valid':sum(r['validation']['valid'] for r in rows),'changes':changes,'matched_dense_prompts_pixels_times':True,'interpretation':'Natural representation/content-order comparison; not blind semantic accuracy.'};(D/'ANALYSIS.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');(D/'RAW_COMPARISON_zh.md').write_text('\n\n'.join(text),encoding='utf-8');print(json.dumps(summary));print('\n'.join(text))

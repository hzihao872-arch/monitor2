import collections,json,pathlib
H=pathlib.Path(__file__).resolve().parent;root=H/'remote_verified/run'
if not root.exists():root=H/'download/run'
rows=[json.loads(p.read_text()) for p in (root/'results').glob('*.json')];groups=collections.defaultdict(list)
for r in rows:groups[r['query_id']].append(r)
text=[];summary={'results':len(rows),'strict_valid':sum(r['validation']['valid'] for r in rows),'queries':{},'interpretation':'Fixed windows cover same 15 distinct RGB frames as dense; more calls and repeated pixels. No manual correct predicates, goals, or ROIs; schema validity is not detection accuracy.'}
for q,rs in sorted(groups.items()):
 rs.sort(key=lambda r:r['request']['as_of_ms']);summary['queries'][q]={'windows':len(rs),'strict_valid':sum(r['validation']['valid'] for r in rs),'changes':sum(len(r['validation']['payload']['changes']) for r in rs if r['validation']['valid'])};text.append('## '+q)
 for r in rs:
  text.append(str(r['request']['image_ids'])+' valid='+str(r['validation']['valid']))
  if r['validation']['valid']:
   for c in r['validation']['payload']['changes']:text.append(f"{c['b']}→{c['a']} {c['object']}: {c['before']} → {c['after']}")
  else:text.append(r['raw'])
(H/'ANALYSIS.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');(H/'RAW_COMPARISON_zh.md').write_text('\n\n'.join(text),encoding='utf-8');print(json.dumps(summary,indent=2));print('\n'.join(text))

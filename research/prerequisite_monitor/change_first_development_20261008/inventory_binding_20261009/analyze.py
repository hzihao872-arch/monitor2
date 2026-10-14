import json,pathlib,collections
H=pathlib.Path(__file__).resolve().parent;rows=[json.loads(p.read_text()) for p in (H/'remote_verified/run/results').glob('*.json')];groups=collections.defaultdict(list)
for r in rows:groups[r['stage']].append(r)
summary={'issued':len(rows),'stages':{s:{'n':len(rs),'strict_valid':sum(r['validation']['valid'] for r in rs)} for s,rs in groups.items()},'queries':{}}
text=[]
for q in sorted({r['query_id'] for r in rows}):
 rs=[r for r in rows if r['query_id']==q];summary['queries'][q]={r['stage']:r['validation'] for r in rs};text.append('## '+q)
 for r in rs:text.extend([r['stage'],'```json',r['raw'],'```'])
summary['skipped']=[json.loads(p.read_text()) for p in (H/'remote_verified/run/skipped').glob('*.json')];summary['status']='Strict format and ID consistency are not semantic correctness; generated initial hypotheses, goal-blind exposed RGB development diagnostic.'
(H/'ANALYSIS.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8');(H/'RAW_zh.md').write_text('\n\n'.join(text),encoding='utf-8');print(json.dumps({'issued':summary['issued'],'stages':summary['stages'],'skipped':summary['skipped']}))

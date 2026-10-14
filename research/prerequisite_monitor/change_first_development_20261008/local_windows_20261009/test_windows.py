import json,pathlib
c=json.loads((pathlib.Path(__file__).parent/'config.json').read_text())
assert len(c['requests'])==56
for q in {r['query_id'] for r in c['requests']}:
 r=[r for r in c['requests'] if r['query_id']==q];assert len(r)==7;assert {i for x in r for i in x['frame_ids']}=={f'f{n:04}' for n in range(15)}
 for x in r:assert len(x['frame_ids'])==3 and max(int(i[1:])*1000 for i in x['frame_ids'])==x['as_of_ms']
print('window coverage and time checks passed')

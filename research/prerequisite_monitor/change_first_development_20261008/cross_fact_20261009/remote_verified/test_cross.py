import json,pathlib
h=pathlib.Path(__file__).parent;c=json.loads((h/'config.json').read_text());old=json.loads((h/'own_endpoint_config.json').read_text())['requests'];a={r['id']:r for r in old}
assert len(c['requests'])==48
for r in c['requests']:
 o=a[r['id'].removesuffix('_cross')];assert r['condition']==o['condition'] and r['object']==o['object'];other=a[o['id'].rsplit('_',1)[0]+'_'+('after' if o['side']=='before' else 'before')];assert r['ref']==other['ref']
print('all 48 predicates unchanged and targets crossed passed')

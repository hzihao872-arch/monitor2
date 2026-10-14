"""Select E/H/R/G from each exposed group; keep all condition names private."""
import argparse
import json
import secrets
from pathlib import Path

from prepare_inputs import prepare_video


def main(inventory, output):
    data=json.loads(Path(inventory).read_text(encoding='utf-8'))
    selected=[x for x in data['clips'] if x['condition'] in ('E','H','R','G')]
    if len(selected)!=8 or any(x['last_sample_ms']<14000 for x in selected):
        raise ValueError('pilot selection or fixed cutoff unavailable')
    root=Path(output)
    if root.exists():
        raise FileExistsError(root)
    root.mkdir(parents=True)
    public=[]
    private=[]
    for x in selected:
        q='q'+secrets.token_hex(8)
        manifest=prepare_video(x['source'],14000,root/q)
        public.append({'query_id':q,'prefix_dir':q,'goal':x['goal'],'as_of_ms':14000,
                       'prefix_signature':manifest['signature']})
        private.append({'query_id':q,'family':x['family'],'condition':x['condition'],
                        'source':x['source'],'source_sha256':x['source_sha256']})
    (root/'queries.json').write_text(json.dumps({'scope':'exposed_development_pilot','queries':public},indent=2),encoding='utf-8')
    mapping=root.parent.parent/'private_eval'/(root.name+'_selection.json')
    if mapping.exists():
        raise FileExistsError(mapping)
    mapping.write_text(json.dumps(private,indent=2),encoding='utf-8')
    print(f'{len(public)} anonymous queries; private map {mapping}')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--inventory',required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args()
    main(a.inventory,a.output)

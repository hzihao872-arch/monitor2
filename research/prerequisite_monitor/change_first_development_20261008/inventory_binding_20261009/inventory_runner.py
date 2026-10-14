import argparse,hashlib,json,os,pathlib,subprocess,sys
H=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(p,x):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True),encoding='utf-8');os.replace(tmp,p)
def validate_inventory(raw):
 obj=None
 try:
  obj=json.loads(raw)
  if set(obj)!={'objects','coverage'} or obj['coverage'] not in ('complete','overflow','occluded','unknown'):raise ValueError('top contract')
  if type(obj['objects'])!=list or not 1<=len(obj['objects'])<=5:raise ValueError('1..5 objects')
  ids=[r['id'] for r in obj['objects']]
  if len(set(ids))!=len(ids) or not all(i in {f'o{j}' for j in range(5)} for i in ids):raise ValueError('object IDs')
  parents={}
  for r in obj['objects']:
   if set(r)!={'id','description','part_of','visible_state'}:raise ValueError('object keys')
   if any(type(r[k])!=str or len(r[k])>120 for k in ('description','visible_state')):raise ValueError('object strings')
   if r['part_of'] not in ids+['unknown',None]:raise ValueError('part parent')
   parents[r['id']]=r['part_of']
  for i in ids:
   seen=set();j=i
   while j in parents:
    if j in seen:raise ValueError('parent cycle')
    seen.add(j);j=parents[j]
  return {'valid':True,'payload':obj,'errors':[]}
 except (ValueError,KeyError,TypeError,AttributeError) as e:return {'valid':False,'payload':obj,'errors':[str(e)]}
def check_object_ids(payload,ids):return ['unknown_object_id'] if any(c['object'] not in ids for c in payload['changes']) else []
def run(a):
 sys.path.insert(0,a.core)
 from experiments.prerequisite_probe.change_first_monitor.qwen_backend import QwenBackend
 from experiments.prerequisite_probe.change_first_monitor.prefix import PrefixPackage
 from experiments.prerequisite_probe.change_first_monitor.runner import RequestLedger,hash_obj
 from contracts import validate
 cfg=json.loads((H/'config.json').read_text());freeze=json.loads((H/'freeze.json').read_text())
 if freeze['files']!={n:sha(H/n) for n in ('config.json','inventory_runner.py','contracts.py')}:raise RuntimeError('freeze changed')
 parent=H.parent/'precision_transfer_20261009/download/run/requests.jsonl' if a.mock else pathlib.Path(cfg['parent']['path'])
 if sha(parent)!=cfg['parent']['sha256'] or sum(json.loads(s)['kind']=='issued' for s in parent.read_text().splitlines())!=40:raise RuntimeError('parent changed')
 root=pathlib.Path(a.output);root.mkdir(parents=True,exist_ok=True);lock=root/'.run.lock';os.close(os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY))
 try:
  class Backend(QwenBackend):
   def generate(self,req):
    if a.mock:
     self.last_metrics={'elapsed_seconds':0,'input_tokens':0,'output_tokens':0,'peak_vram_bytes':0,'hit_output_cap':False};return json.dumps({'objects':[{'id':'o0','description':'mock','visible_state':'mock','part_of':None}],'coverage':'unknown'}) if req['stage']=='INVENTORY' else json.dumps({'context':'mock','changes':[],'coverage':'no_observable_change'})
    return super().generate(req)
  backend=Backend(a.model or 'mock');ledger=RequestLedger(root,hash_obj({'series':'inventory_binding_v1','freeze':freeze,'mock':a.mock,'model':backend.identity}),16)
  if not a.mock and subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():raise RuntimeError('GPU occupied')
  for qid in cfg['queries']:
   pkg=PrefixPackage(pathlib.Path(a.input)/qid);frames=[f for f in pkg.manifest['frames'] if f['time_ms']<=14000];all_ids=[f['evidence_id'] for f in frames];inventory=None
   for stage in ('INVENTORY','TRACK'):
    dst=root/'results'/f'{qid}_{stage}.json'
    if dst.exists():
     v=json.loads(dst.read_text())['validation']
     if stage=='INVENTORY':
      if not v['valid']:break
      inventory=v['payload']
     continue
    if stage=='INVENTORY':
     ids=['f0000'];prompt='From this initial RGB scene, describe up to five non-robot physical objects, assemblies, and visible components. Use shape and color, and distinguish a visibly connected component from a standalone item. Use part_of="unknown" when attachment cannot be seen, null for a clearly standalone item, otherwise a listed parent object ID. These are visual hypotheses, not hidden physical facts. Do not describe goals, task plans, actions or affordances. Return only a JSON object with exact keys objects and coverage. objects is 1..5 items with exact keys id (unique o0..o4), description (string max120), part_of (parent ID, "unknown", or null), visible_state (string max120). Parent links must not cycle. coverage is complete|overflow|occluded|unknown. The first character must be {; use no markdown or fences.';cap=512
    else:
     ids=all_ids;prompt='Track the candidate non-robot objects below through the chronological RGB prefix. Their initial descriptions and part links are model-generated hypotheses: use pixels to verify or correct the binding; do not assume attachment persists. When a component visibly moves together with a larger assembly, describe the observed assembly change. Do not invent motion from the inventory. Record at most three visible persistent environment changes, object-control changes, or reversals. Robot pose alone is not an environment change. Do not infer goals, utility, hidden mechanisms or task plans. Return only a JSON object with exact keys context, changes, coverage. context is a neutral scene sentence max240. changes is at most3 items with exact keys b, a (supplied frame IDs, time(b)<time(a)), object (one inventory object ID), before and after (strings max160). coverage=complete|overflow|occluded|no_observable_change. Use no markdown or fences. MODEL_GENERATED_INITIAL_INVENTORY: '+json.dumps(inventory,sort_keys=True,separators=(',',':'))+' EVIDENCE_TIME_MS: '+json.dumps({i:pkg.handles[i]['time_ms'] for i in ids},sort_keys=True,separators=(',',':'));cap=768
    pixels=[pkg.read(i,'V1') for i in ids];req={'query_id':qid,'stage':stage,'arm':'inventory_binding','prompt':prompt,'images':pixels,'image_ids':ids,'image_hashes':[hashlib.sha256(b).hexdigest() for b in pixels],'image_meta':[{'time_ms':pkg.handles[i]['time_ms']} for i in ids],'as_of_ms':0 if stage=='INVENTORY' else 14000,'limits':[5000,cap],'input_type':'legal_rgb_goal_blind_automatic_inventory_binding','parent_issued':468,'initial_inventory_origin':'model generated from registered initial frame only; no oracle, goal, label or manually correct region'}
    raw=ledger.invoke(req,backend.generate);v=validate_inventory(raw) if stage=='INVENTORY' else validate('V1',raw,{i:pkg.handles[i] for i in ids})
    if stage=='TRACK' and v['valid']:
     e=check_object_ids(v['payload'],{r['id'] for r in inventory['objects']})
     if e:v['valid']=False;v['errors']+=e
    save(dst,{'query_id':qid,'stage':stage,'raw':raw,'validation':v,'request':{k:v for k,v in req.items() if k!='images'}});save(root/'progress.json',{'issued':ledger.issued_count,'parent':468,'total':468+ledger.issued_count,'last':qid+'_'+stage});print(json.dumps({'query':qid,'stage':stage,'valid':v['valid'],'issued':ledger.issued_count}),flush=True)
    if stage=='INVENTORY':
     if not v['valid']:save(root/'skipped'/f'{qid}.json',{'reason':'invalid inventory','dependent_stage':'TRACK'});break
     inventory=v['payload']
 finally:lock.unlink(missing_ok=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--core',required=True);p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--model');p.add_argument('--mock',action='store_true');run(p.parse_args())

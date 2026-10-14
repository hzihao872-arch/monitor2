import datetime,hashlib,json,pathlib,statistics
H=pathlib.Path(__file__).resolve().parent;B=H.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
series=['atomic_state','atomic_contrast','joint_choice','native_prefix','prior_control','prefix_sampling','dense_discovery','generated_fact','reversal_transfer','fullframe_scale','author_context','author_prefix','gvl_order','gvl_order_v2','author_chat','precision_transfer','inventory_binding','local_windows','native_discovery','discovery_layout','cross_fact','chroma_roi'];summaries=[];members={};done_all=[];issued_all=[]
for short in series:
 root=B/(short+'_20261009');data_root=root/'remote_verified';ledger=data_root/'run/requests.jsonl'
 if not ledger.exists() and short=='chroma_roi':data_root=root/'local_recovered';ledger=data_root/'run/requests.jsonl'
 if not ledger.exists():continue
 logs=[json.loads(s) for s in ledger.read_text(encoding='utf-8').splitlines()];issued=[r for r in logs if r['kind']=='issued'];done=[r for r in logs if r['kind']=='completed'];failed=[r for r in logs if r['kind']=='failed'];pending={r['request_id'] for r in issued}-{r['request_id'] for r in done}-{r['request_id'] for r in failed};assert not pending
 errors=[]
 for r in issued:
  req=r['request']
  if any(m['time_ms']>req['as_of_ms'] for m in req.get('image_meta',[])):errors.append('future')
  if any(i.startswith('c') for i in req.get('image_ids',[])):errors.append('crop')
  if req.get('images'):errors.append('serialized_pixels_in_ledger')
  crops=req.get('automatic_crop_registry',[])
  for crop in crops:
   ids=req['image_ids'];metas=dict(zip(ids,req['image_meta']));pixel_hashes=dict(zip(ids,req['image_hashes']));cid=crop['id'];parent=crop['parent_id']
   if crop['crop_origin']!='automatic goal-blind chroma motion v1' or short!='chroma_roi':errors.append('unaudited_crop_origin')
   if parent not in metas or metas[parent]['time_ms']!=crop['time_ms'] or metas[cid]['time_ms']!=crop['time_ms']:errors.append('crop_parent_time')
   if pixel_hashes[cid]!=crop['sha256']:errors.append('crop_pixel_hash')
   if sha(data_root/'run/crops'/f"{req['query_id']}_{cid}.png")!=crop['sha256']:errors.append('crop_file_hash')
 assert not errors
 metrics=[r['metrics'] for r in done];verification_file=root/('REMOTE_VERIFIED.json' if data_root.name=='remote_verified' else 'PARTIAL_RECOVERY.json');summary={'series':short,'issued':len(issued),'completed':len(done),'failed':len(failed),'ambiguous':len(pending),'ledger_sha256':sha(ledger),'input_tokens':sum(m['input_tokens'] for m in metrics),'output_tokens':sum(m['output_tokens'] for m in metrics),'wall_seconds':sum(r['seconds'] for r in done),'adapter_seconds':sum(m['elapsed_seconds'] for m in metrics),'peak_vram_gib':max([m['peak_vram_bytes'] for m in metrics] or [0])/2**30,'hit_caps':sum(m.get('hit_output_cap',False) for m in metrics),'audit_errors':errors,'data_status':data_root.name,'verification':json.loads(verification_file.read_text())}
 summaries.append(summary);done_all+=done;issued_all+=issued
 for d in ('remote_verified','local_recovered','private_eval','sources'):
  for p in (root/d).rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts:members[str(p.relative_to(B))]=sha(p)
 for p in root.glob('*'):
  if p.is_file() and p.suffix in ('.py','.json','.md','.zip','.gz'):members[str(p.relative_to(B))]=sha(p)
audit={'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'authorization_latest':'调用上限提高，只要能连上服务器你就一直做','old80_and_stop_time':'superseded for new series by latest user authorization; old frozen sources retain their historical limits','series':summaries,'new_issued':len(issued_all),'new_completed':len(done_all),'previous50_plus_new':50+len(issued_all),'older96_separate':96,'all_issued_separate_ledgers':146+len(issued_all),'cost':{'input_tokens':sum(s['input_tokens'] for s in summaries),'output_tokens':sum(s['output_tokens'] for s in summaries),'wall_seconds':sum(s['wall_seconds'] for s in summaries),'adapter_seconds':sum(s['adapter_seconds'] for s in summaries),'peak_vram_gib':max(s['peak_vram_gib'] for s in summaries),'currency_cost':'not measured; inference wall time excludes research, preparation, SSH, idle time and billing minimums'},'reference_status':'AI development visual references; no independent human annotation or blind evaluation','members':members}
(H/'AUDIT.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False),encoding='utf-8');print(json.dumps({k:v for k,v in audit.items() if k not in ('series','members')},ensure_ascii=False,indent=2))

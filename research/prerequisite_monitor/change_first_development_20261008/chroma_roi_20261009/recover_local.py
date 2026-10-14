import hashlib,json,pathlib,shutil,sys,zlib,io,tarfile,datetime
import cv2,numpy as np
H=pathlib.Path(__file__).resolve().parent;B=H.parent;sys.path.insert(0,str(H));from selector import propose,crop
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=H/'download/run';logs=[json.loads(s) for s in (source/'requests.jsonl').read_text().splitlines()];issued=[r for r in logs if r['kind']=='issued'];done=[r for r in logs if r['kind']=='completed'];assert len(issued)==len(done)==8;assert {r['request_id'] for r in issued}=={r['request_id'] for r in done}
root=H/'local_recovered/run';root.mkdir(parents=True,exist_ok=True)
for p in source.rglob('*'):
 if p.is_file():dst=root/p.relative_to(source);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
crop_records=[]
for row in issued:
 req=row['request'];qid=req['query_id'];pkg=B/'atomic_state_20261009/source_core/model_input/pilot_v5'/qid;m=json.loads((pkg/'manifest.json').read_text());frames=[cv2.cvtColor(cv2.imdecode(np.frombuffer((pkg/r['path']).read_bytes(),np.uint8),cv2.IMREAD_COLOR),cv2.COLOR_BGR2RGB) for r in m['frames']];expected=propose(frames,[r['time_ms'] for r in m['frames']]);assert expected==req['automatic_roi_proposals']
 for r in req['automatic_crop_registry']:
  idx=int(r['parent_id'][1:]);data=crop(frames[idx],r['crop_xyxy']);assert hashlib.sha256(data).hexdigest()==r['sha256'];dst=root/'crops'/f"{qid}_{r['id']}.png";dst.parent.mkdir(exist_ok=True);dst.write_bytes(data);crop_records.append({'file':str(dst.relative_to(H)),'sha256':r['sha256'],'status':'local deterministic reconstruction exactly matches model input hash in downloaded remote ledger'})
partial=H/'chroma_FINAL.partial.tar.gz';transport=json.loads((H/'transport_seal.json').read_text());seal=json.loads(transport['stdout']);result={'status':'complete downloaded ledger and8 results;32 crops reconstructed locally and hash matched; remote archive download truncated, full archive member seal NOT verified','issued':8,'completed':8,'ambiguous':0,'remote_seal_receipt':seal,'partial_archive_sha256':sha(partial),'partial_archive_size':partial.stat().st_size,'crop_records':crop_records,'opencv':cv2.__version__,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
# Preserve complete members recoverable from the truncated gzip, without labeling them a verified full archive.
raw=zlib.decompressobj(16+zlib.MAX_WBITS).decompress(partial.read_bytes());recovered=[]
try:
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as t:
  for member in t:
   if not member.isfile():continue
   data=t.extractfile(member).read()
   if len(data)==member.size:recovered.append({'name':member.name,'size':member.size,'sha256':hashlib.sha256(data).hexdigest()})
except (tarfile.ReadError,EOFError) as e:result['partial_tar_read_error']=str(e)
result['partial_tar_complete_members']=recovered;(H/'PARTIAL_RECOVERY.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k not in ('crop_records','partial_tar_complete_members')},indent=2));print('crop_hashes_verified',len(crop_records),'partial_complete_members',len(recovered))

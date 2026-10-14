import datetime,hashlib,json,pathlib,shutil,zipfile
H=pathlib.Path(__file__).resolve().parent;B=H.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
audit=json.loads((H/'AUDIT.json').read_text(encoding='utf-8'));names=[s['series']+'_20261009' for s in audit['series']];files=[]
for name in names:
 root=B/name
 for d in ('remote_verified','local_recovered','private_eval','sources'):
  files.extend(p for p in (root/d).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
 files.extend(p for p in root.glob('*') if p.is_file() and p.suffix in ('.py','.json','.md','.png'))
core=B/'atomic_state_20261009/source_core'
for d in ('model_input/pilot_v5','experiments/prerequisite_probe/change_first_monitor'):
 files.extend(p for p in (core/d).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
files.extend(p for p in H.glob('*') if p.is_file() and p.suffix in ('.md','.json','.py','.png') and p.name!='DELIVERY_VERIFIED.json')
files.extend(p for p in (H/'licenses').rglob('*') if p.is_file())
files.extend(p for p in (H/'sources_gvl').glob('*') if p.is_file() and (p.name in ('PINNED.json','gemini.html','gemini_pinned.html') or p.suffix=='.json'))
files.append(B/'verify_series.py');files=list(dict.fromkeys(files))
partial=B/'chroma_roi_20261009/chroma_FINAL.partial.tar.gz'
if partial.exists():files.append(partial)
for p in files:
 if any(s in p.name.lower() for s in ('session_credentials','remote_access','authorized_session','ssh_key','id_rsa')):raise RuntimeError('credential path prohibited')
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');dst=H/f'evidence_checkpoint_{stamp}.zip';members={str(p.relative_to(B)).replace('\\','/'):sha(p) for p in files}
with zipfile.ZipFile(dst,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,str(p.relative_to(B)).replace('\\','/'))
 z.writestr('CHECKPOINT_MEMBERS.json',json.dumps(members,indent=2))
with zipfile.ZipFile(dst) as z:
 errors=[n for n,h in members.items() if hashlib.sha256(z.read(n)).hexdigest()!=h]
 assert not errors
result={'archive':str(dst),'sha256':sha(dst),'verified_members':len(members),'errors':errors,'new_issued':audit['new_issued'],'previous50_plus_new':audit['previous50_plus_new'],'old96_separate':96,'remote_fully_verified_series':sum(s['data_status']=='remote_verified' for s in audit['series']),'partial_remote_recoveries':sum(s['data_status']=='local_recovered' for s in audit['series']),'status':'local checkpoint verified; one partial remote archive recovery explicitly labeled; not calibrated monitor or blind accuracy'}
(H/'DELIVERY_VERIFIED.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))

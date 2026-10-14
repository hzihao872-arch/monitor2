"""Verify files/provenance only; not a scientific or independent-label review."""
from pathlib import Path
from urllib.parse import unquote,urlsplit
import json,hashlib,re
from audit_sources import ROOT,OUT,save,CAP

errors=[]; checks={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
mf=json.loads((OUT/'fetch_manifest.json').read_text('utf-8'))
for r in mf:
 p=OUT/r['path']
 if not p.exists() or sha(p)!=r['sha256'] or p.stat().st_size!=r['bytes']:errors.append(['source',r['path']])
checks['download_files']=len(mf);checks['download_bytes']=sum(r['bytes'] for r in mf)
if checks['download_bytes']>CAP:errors.append('budget')
checks['png_lfs_verified']=0
for ep in [510,513,514]:
 tree=json.loads((OUT/f'ep{ep}_tree.json').read_text('utf-8'))
 for r in tree:
  p=OUT/r['path']
  if p.exists():
   if sha(p)!=r['lfs']['oid'] or p.stat().st_size!=r['size']:errors.append(['LFS',str(p)])
   checks['png_lfs_verified']+=1
checks['git_blobs_verified']=0
for name in ['r2vlm','prm_current']:
 d=json.loads((OUT/(name+'_tree.json')).read_text('utf-8'))
 for r in d['tree']:
  p=OUT/name/r['path']
  if p.is_file():
   b=p.read_bytes();g=hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
   if g!=r['sha']:errors.append(['git blob',str(p)])
   checks['git_blobs_verified']+=1

checks['reused_hashes_verified']=0
for r in json.loads((OUT/'reused_sources.json').read_text('utf-8')):
 if sha(ROOT/r['path'])!=r['sha256']:errors.append(['reused',r['path']])
 checks['reused_hashes_verified']+=1
checks['protected_files_unchanged']=[]
baseline=json.loads((OUT/'before_edit.json').read_text('utf-8'))
for r in baseline:
 if r['path'] in ['experiments/run_ledger.csv','research/08_pilot_report.md','research/07_evaluation_protocol.md','experiments/config_stage7.json']:
  if sha(ROOT/r['path'])!=r['sha256']:errors.append(['protected changed',r['path']])
  else:checks['protected_files_unchanged'].append(r['path'])
old_status=(OUT/'before/research/status.md').read_bytes()
new_status=(ROOT/'research/status.md').read_bytes()
checks['status_old_body_retained']=new_status.endswith(old_status[len('# 研究状态'.encode('utf-8')):])
checks['decision_log_old_bytes_retained']=(ROOT/'research/decision_log.md').read_bytes().startswith((OUT/'before/research/decision_log.md').read_bytes())
if not checks['status_old_body_retained'] or not checks['decision_log_old_bytes_retained']:errors.append('history changed')
old=json.loads((OUT/'before/experiments/data_manifest.json').read_text('utf-8'))
new=json.loads((ROOT/'experiments/data_manifest.json').read_text('utf-8'))
checks['data_version']=new['version']
checks['data_sources_added']=len(new['sources'])-len(old['sources'])
checks['old_data_sources_retained']=new['sources'][:len(old['sources'])]==old['sources']
if checks['data_version']!='S7-screening-4' or not checks['old_data_sources_retained']:errors.append('data history/version')
for r in new['sources'][-1]['files']:
 if sha(ROOT/r['path'])!=r['sha256']:errors.append(['data pointer hash',r['path']])

json_files=[p for p in OUT.rglob('*.json') if 'before' not in p.relative_to(OUT).parts and p.name!='validation.json']+[ROOT/'experiments/data_manifest.json']
for p in json_files:
 try:json.loads(p.read_text('utf-8'))
 except Exception as e:errors.append(['json',str(p),str(e)])
checks['json_parsed']=len(json_files)
doc=ROOT/'research/native_task_gap_audit_20261003.md'
docs=[(doc,doc.read_text('utf-8')),(ROOT/'research/status.md',new_status[:len(new_status)-len(old_status)+len('# 研究状态'.encode('utf-8'))].decode('utf-8'))]
log=ROOT/'research/decision_log.md';before=(OUT/'before/research/decision_log.md').read_bytes();docs.append((log,log.read_bytes()[len(before):].decode('utf-8')))
links=0;urls=set()
for path,txt in docs:
 for target in re.findall(r'\]\(([^)]+)\)',txt):
  target=target.strip('<>');u=urlsplit(target)
  if u.scheme in ['http','https']:
   urls.add(target);continue
  rel=unquote(target.split('#')[0])
  if not rel:continue
  p=(path.parent/rel).resolve()
  if p==OUT/'validation.json':links+=1;continue
  if not p.exists():errors.append(['missing link',str(path),target])
  links+=1
checks['local_links_checked']=links
checks['remote_urls_format_checked']=sorted(urls)
checks['remote_live_status']='Primary paper/official repo URLs opened during audit; ProgressCompass project live open failed (recorded); not all remote links re-fetched.'
checks['models_run']=0
checks['research_conclusion']='No demonstrated B-subclass strong-method prediction error; file verification is not independent annotation.'
save('validation.json',dict(checks=checks,errors=errors,passed=not errors))
print(json.dumps(dict(passed=not errors,errors=errors,checks=checks),ensure_ascii=False,indent=2))
if errors:raise SystemExit(1)

import hashlib,json,pathlib,sys,time,os
H=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'diagnostic_20261009_v9'));from remote_access import connect
R='/root/autodl-tmp/monitor2/fresh_prerequisite_runs/change_first_chroma_roi_20261009_v1'
archive=H/'chroma_FINAL.tar.gz'
if archive.exists() and not (H/'remote_seal.json').exists():
 destination=H/'chroma_FINAL.partial.tar.gz'
 if not destination.exists():os.replace(archive,destination)
c=connect()
try:
 with c.open_sftp() as s:
  s.get(R+'/remote_seal.json',str(H/'remote_seal.json'),prefetch=False)
  seal=json.loads((H/'remote_seal.json').read_text());partial=H/'chroma_FINAL.rescue.part';size=s.stat(R+'/chroma_FINAL.tar.gz').st_size;start=partial.stat().st_size if partial.exists() else 0
  with s.open(R+'/chroma_FINAL.tar.gz','rb') as remote,partial.open('ab') as local:
   remote.seek(start)
   while True:
    block=remote.read(32768)
    if not block:break
    local.write(block);local.flush()
  assert partial.stat().st_size==size
  assert hashlib.sha256(partial.read_bytes()).hexdigest()==seal['sha256'];os.replace(partial,archive)
 print(json.dumps({'downloaded':True,'size':size,'sha256':seal['sha256']}))
finally:c.close()

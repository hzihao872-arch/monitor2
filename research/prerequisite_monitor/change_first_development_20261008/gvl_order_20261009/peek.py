import json,pathlib,sys
H=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'diagnostic_20261009_v9'));from remote_access import connect
c=connect()
try:
 with c.open_sftp() as s:
  for q in ('q613a0d8ddf5acc68','q0d6f6ef3062d4d34'):
   n=q+'_shuffled.json';r=json.loads(s.open('/root/autodl-tmp/monitor2/fresh_prerequisite_runs/change_first_gvl_order_20261009_v1/run/results/'+n).read());print(json.dumps({'query':q,'validation':r['validation'],'raw':r['raw']},ensure_ascii=False))
finally:c.close()

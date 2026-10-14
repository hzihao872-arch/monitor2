import pathlib,json,sys
H=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'diagnostic_20261009_v9'));from remote_access import connect
c=connect()
try:
 command="/root/autodl-tmp/monitor2/.venv-topreward/bin/python - <<'PY'\nimport json,sys,cv2,numpy,torch,transformers,PIL\nprint(json.dumps({'python':sys.version,'opencv':cv2.__version__,'numpy':numpy.__version__,'torch':torch.__version__,'transformers':transformers.__version__,'pillow':PIL.__version__}))\nPY"
 _,out,err=c.exec_command(command,timeout=30);text=out.read().decode();error=err.read().decode();rc=out.channel.recv_exit_status();assert rc==0,(rc,error);data=json.loads(text);(H/'REMOTE_ENVIRONMENT.json').write_text(json.dumps(data,indent=2),encoding='utf-8');print(json.dumps(data))
finally:c.close()

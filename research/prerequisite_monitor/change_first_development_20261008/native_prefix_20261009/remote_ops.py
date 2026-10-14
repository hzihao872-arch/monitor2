import argparse,json,pathlib,sys
H=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'diagnostic_20261009_v9'));from remote_access import connect
R='/root/autodl-tmp/monitor2/fresh_prerequisite_runs/change_first_native_prefix_20261009_v1'
CORE='/root/autodl-tmp/monitor2/fresh_prerequisite_runs/change_first_s1_20261009/bundle_v8_clean';PY='/root/autodl-tmp/monitor2/.venv-topreward/bin/python'
MODEL='/root/autodl-tmp/hf/hub/models--Qwen--Qwen3-VL-8B-Instruct/snapshots/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b'
def cmd(c,text):
    _,o,e=c.exec_command(text,timeout=45);out=o.read().decode();err=e.read().decode();rc=o.channel.recv_exit_status();print(out,end='');print(err,end='',file=sys.stderr)
    return {'command':text,'stdout':out,'stderr':err,'exit_code':rc}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('op',choices=['deploy','processor','run','status','collect','seal','get']);a=p.parse_args();c=connect()
    try:
        if a.op=='deploy':
            cmd(c,f'mkdir -p {R}')
            with c.open_sftp() as s:s.put(str(H/'native_v1.zip'),R+'/native_v1.zip')
            r=cmd(c,f'{PY} -m zipfile -e {R}/native_v1.zip {R}; {PY} {R}/test_native.py; sha256sum {R}/native_v1.zip')
        elif a.op in ('run','processor'):
            command=f'{PY} {R}/native_runner.py --core {CORE} --input {CORE}/model_input/pilot_v5 --output {R}/run --model {MODEL}'
            command+= ' --processor-only' if a.op=='processor' else ''
            r=cmd(c,f'nohup {command} > {R}/{a.op}.log 2>&1 < /dev/null &')
        elif a.op=='status':r=cmd(c,f'date -u; nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv; cat {R}/run/progress.json; tail -n 5 {R}/run.log')
        elif a.op=='collect':
            dst=H/'download/run';(dst/'results').mkdir(parents=True,exist_ok=True)
            with c.open_sftp() as s:
                for n in s.listdir(R+'/run'):
                    if n.endswith(('.json','.jsonl')):s.get(R+'/run/'+n,str(dst/n))
                for n in s.listdir(R+'/run/results'):s.get(R+'/run/results/'+n,str(dst/'results'/n))
            r={'downloaded_results':len(list((dst/'results').glob('*.json')))};print(json.dumps(r))
        elif a.op=='seal':
            with c.open_sftp() as s:s.put(str(H/'seal_remote.py'),R+'/seal_remote.py')
            r=cmd(c,f'{PY} {R}/seal_remote.py')
        else:
            with c.open_sftp() as s:
                for n in ('native_FINAL.tar.gz','remote_seal.json'):s.get(R+'/'+n,str(H/n))
            r={'downloaded':True};print(json.dumps(r))
        (H/f'transport_{a.op}.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
    finally:c.close()

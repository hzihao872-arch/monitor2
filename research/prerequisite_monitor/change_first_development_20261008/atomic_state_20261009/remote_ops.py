"""Local transport only; imports authorized bridge, never reads or copies session text."""
import argparse,datetime,hashlib,json,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'diagnostic_20261009_v9'))
from remote_access import connect
REMOTE='/root/autodl-tmp/monitor2/fresh_prerequisite_runs/change_first_atomic_20261009_v1'
CORE='/root/autodl-tmp/monitor2/fresh_prerequisite_runs/change_first_s1_20261009/bundle_v8_clean'
PY='/root/autodl-tmp/monitor2/.venv-topreward/bin/python'
MODEL='/root/autodl-tmp/hf/hub/models--Qwen--Qwen3-VL-8B-Instruct/snapshots/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b'
PARENT='/root/autodl-tmp/monitor2/fresh_prerequisite_runs/change_first_diag_20261009_v9/runs/window_v9/requests.jsonl'
def command(c,cmd):
    _,o,e=c.exec_command(cmd,timeout=45);out=o.read().decode();err=e.read().decode();status=o.channel.recv_exit_status()
    print(out,end='');print(err,end='',file=sys.stderr)
    return {'command':cmd,'stdout':out,'stderr':err,'exit_code':status,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('op',choices=['preflight','deploy','primary1','primary2','context','status','collect','seal','get']);a=p.parse_args()
    c=connect()
    try:
        if a.op=='preflight':
            code=f"from transformers import AutoTokenizer; import torch,transformers,json; t=AutoTokenizer.from_pretrained('{MODEL}',local_files_only=True);print(json.dumps({{'tokens':{{s:t.encode(s,add_special_tokens=False) for s in ['True','False','Unknown']}},'torch':torch.__version__,'transformers':transformers.__version__}}))"
            r=command(c,f'date -u; nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv; {PY} -c "{code}"; sha256sum {PARENT}')
        elif a.op=='deploy':
            r=command(c,f'mkdir -p {REMOTE}')
            with c.open_sftp() as s:s.put(str(HERE/'atomic_state_v1.zip'),REMOTE+'/atomic_state_v1.zip')
            r=command(c,f'{PY} -m zipfile -e {REMOTE}/atomic_state_v1.zip {REMOTE}; {PY} {REMOTE}/test_atomic.py; sha256sum {REMOTE}/atomic_state_v1.zip')
        elif a.op in ('primary1','primary2','context'):
            subset=' --ids opening_00 opening_14 plate_00 plate_14' if a.op=='primary1' else (' --ids grasp_07 grasp_14 inside_07 inside_14' if a.op=='primary2' else '')
            block='context' if a.op=='context' else 'primary'
            cmd=f'{PY} {REMOTE}/atomic_runner.py --core-root {CORE} --input {CORE}/model_input/pilot_v5 --output {REMOTE}/run --parent-ledger {PARENT} --model {MODEL} --block {block}'+subset
            r=command(c,f"nohup {cmd} > {REMOTE}/{a.op}.log 2>&1 < /dev/null &")
        elif a.op=='status':
            r=command(c,f'date -u; nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv; ps -eo pid,args | grep "{REMOTE}/atomic_runner.py" | grep -v grep; cat {REMOTE}/run/progress.json; tail -n 4 {REMOTE}/primary1.log; tail -n 4 {REMOTE}/primary2.log; tail -n 4 {REMOTE}/context.log')
        elif a.op=='collect':
            dst=HERE/'download/run';(dst/'results').mkdir(parents=True,exist_ok=True)
            with c.open_sftp() as s:
                for name in s.listdir(REMOTE+'/run'):
                    if name.endswith('.json') or name.endswith('.jsonl'):s.get(REMOTE+'/run/'+name,str(dst/name))
                for name in s.listdir(REMOTE+'/run/results'):s.get(REMOTE+'/run/results/'+name,str(dst/'results'/name))
            r={'downloaded_results':len(list((dst/'results').glob('*.json')))};print(json.dumps(r))
        elif a.op=='seal':
            with c.open_sftp() as s:s.put(str(HERE/'seal_remote.py'),REMOTE+'/seal_remote.py')
            r=command(c,f'{PY} {REMOTE}/seal_remote.py; sha256sum {REMOTE}/atomic_state_FINAL.tar.gz')
        else:
            with c.open_sftp() as s:
                for name in ('atomic_state_FINAL.tar.gz','remote_seal.json'):s.get(REMOTE+'/'+name,str(HERE/name))
            r={'downloaded':True,'sha256':hashlib.sha256((HERE/'atomic_state_FINAL.tar.gz').read_bytes()).hexdigest()}
            print(json.dumps(r))
        (HERE/f'transport_{a.op}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    finally:c.close()

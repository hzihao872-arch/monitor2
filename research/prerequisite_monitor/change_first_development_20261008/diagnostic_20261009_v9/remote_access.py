"""Local-only SSH bridge; credentials stay in memory, never in artifacts."""
import argparse,json,pathlib,re,sys
import paramiko

SESSION=pathlib.Path(r'C:\Users\HANWANG\.codex\sessions\2026\10\08\rollout-2026-10-08T22-51-01-01a11bff-0833-73f1-b838-faf66dc78c88.jsonl')

def connect():
    candidates=[]
    for line in SESSION.read_text(encoding='utf-8').splitlines():
        row=json.loads(line); p=row.get('payload',{})
        if row.get('type')=='response_item' and p.get('role')=='user':
            txt='\n'.join(c.get('text','') for c in p.get('content',[]))
            if 'ssh' in txt and '46163' in txt and '密码' in txt: candidates.append(txt)
    if not candidates: raise RuntimeError('No verified session connection record')
    txt=candidates[-1]
    pw=re.search(r'密码\s*[:：]?\s*([\x21-\x7e]+)',txt)
    if not pw: raise RuntimeError('Credential format not recognized')
    client=paramiko.SSHClient(); client.load_host_keys(str(pathlib.Path.home()/'.ssh/known_hosts'))
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    password=pw.group(1).strip('`"\'')
    client.connect('connect.bjb1.seetacloud.com',port=46163,username='root',password=password,look_for_keys=False,allow_agent=False,timeout=15)
    return client

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--command');p.add_argument('--put',nargs=2);p.add_argument('--get',nargs=2);a=p.parse_args()
    c=connect()
    try:
        if a.command:
            _,out,err=c.exec_command(a.command,timeout=45)
            print(out.read().decode(),end='');print(err.read().decode(),end='',file=sys.stderr)
            sys.exit(out.channel.recv_exit_status())
        else:
            with c.open_sftp() as s:
                if a.put:s.put(*a.put)
                elif a.get:s.get(*a.get)
    finally:c.close()

import argparse,pathlib,sys
H=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(H/'diagnostic_20261009_v9'));from remote_access import connect
p=argparse.ArgumentParser();p.add_argument('command');a=p.parse_args();c=connect()
try:
 _,o,e=c.exec_command(a.command,timeout=40);print(o.read().decode(),end='');print(e.read().decode(),end='',file=sys.stderr);sys.exit(o.channel.recv_exit_status())
finally:c.close()

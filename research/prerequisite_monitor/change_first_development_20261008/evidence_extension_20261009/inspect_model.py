import json,pathlib,shlex,sys
H=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'diagnostic_20261009_v9'));from remote_access import connect
model='/root/autodl-tmp/hf/hub/models--Qwen--Qwen3-VL-8B-Instruct/snapshots/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b';code=f"import json;from transformers import AutoProcessor;p=AutoProcessor.from_pretrained({model!r},local_files_only=True);c=json.load(open({(model+'/config.json')!r}));print(json.dumps({{'tie_word_embeddings':c.get('tie_word_embeddings'),'eos_id':p.tokenizer.eos_token_id,'token_151645':p.tokenizer.decode([151645])}}))"
c=connect()
try:
 _,o,e=c.exec_command(shlex.join(['/root/autodl-tmp/monitor2/.venv-topreward/bin/python','-c',code]),timeout=40);out=o.read().decode();err=e.read().decode();rc=o.channel.recv_exit_status();print(out);print(err);assert rc==0;(H/'MODEL_TOKEN_AUDIT.json').write_text(out,encoding='utf-8')
finally:c.close()

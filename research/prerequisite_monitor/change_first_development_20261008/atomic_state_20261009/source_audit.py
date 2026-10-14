import hashlib,json,pathlib,urllib.request,subprocess
H=pathlib.Path(__file__).resolve().parent;W=H.parents[3]
out=H/'sources';out.mkdir(exist_ok=True)
sources=[
 ('topreward_qwen.py','https://raw.githubusercontent.com/TOPReward/TOPReward/4877a0ee5098cbec18485125466631b1dcc4a573/topreward/clients/qwen.py','4877a0ee5098cbec18485125466631b1dcc4a573',W/'research/sources/TOPReward/topreward/clients/qwen.py'),
 ('qwen_processing_4_57_1.py','https://raw.githubusercontent.com/huggingface/transformers/v4.57.1/src/transformers/models/qwen3_vl/processing_qwen3_vl.py','v4.57.1',None),
 ('robometer_collator.py','https://raw.githubusercontent.com/robometer/robometer/352d160389daa964788de1ec933d1925f3a6de4f/robometer/data/collators/rbm_heads.py','352d160389daa964788de1ec933d1925f3a6de4f',W/'research/sources/robometer/robometer/data/collators/rbm_heads.py'),
 ('robometer_trainer.py','https://raw.githubusercontent.com/robometer/robometer/352d160389daa964788de1ec933d1925f3a6de4f/robometer/trainers/rbm_heads_trainer.py','352d160389daa964788de1ec933d1925f3a6de4f',W/'research/sources/robometer/robometer/trainers/rbm_heads_trainer.py')]
records=[]
for name,url,commit,local in sources:
    try:
        data=urllib.request.urlopen(url,timeout=30).read();(out/name).write_bytes(data)
        normalized=lambda b:b.replace(b'\r\n',b'\n')
        records.append({'file':name,'url':url,'commit_or_tag':commit,'sha256':hashlib.sha256(data).hexdigest(),
            'local_normalized_equal':normalized(data)==normalized(local.read_bytes()) if local else None})
    except Exception as e:records.append({'file':name,'url':url,'error':type(e).__name__+': '+str(e)})
# Resolve the release tag to a commit, so the executable dependency code is pinned.
try:
    ref=json.loads(urllib.request.urlopen('https://api.github.com/repos/huggingface/transformers/git/ref/tags/v4.57.1',timeout=30).read())
    (out/'transformers_tag.json').write_text(json.dumps(ref,indent=2),encoding='utf-8')
except Exception as e: records.append({'tag_resolution_error':str(e)})
(H/'SOURCE_AUDIT.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(records,ensure_ascii=False))

import hashlib,json,pathlib,re,urllib.request
H=pathlib.Path(__file__).resolve().parent/'sources_gvl';H.mkdir(exist_ok=True)
urls=['https://generative-value-learning.github.io/','https://api.github.com/repos/generative-value-learning/generative-value-learning.github.io/commits/main']
manifest=[]
for i,url in enumerate(urls):
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'research-source-audit'});data=urllib.request.urlopen(req,timeout=25).read();name='website.html' if i==0 else 'website_commit.json';(H/name).write_bytes(data);manifest.append({'url':url,'file':name,'sha256':hashlib.sha256(data).hexdigest()})
  if i==0:
   scripts=re.findall(r'<script[^>]+src=["\']([^"\']+)',data.decode())
   for src in scripts:
    if src.startswith('./'):src=src[2:]
    if src.startswith(('http','//')):continue
    u='https://generative-value-learning.github.io/'+src.lstrip('/');b=urllib.request.urlopen(u,timeout=25).read();n=pathlib.Path(src).name;(H/n).write_bytes(b);manifest.append({'url':u,'file':n,'sha256':hashlib.sha256(b).hexdigest()})
 except Exception as e:manifest.append({'url':url,'error':str(e)})
(H/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))

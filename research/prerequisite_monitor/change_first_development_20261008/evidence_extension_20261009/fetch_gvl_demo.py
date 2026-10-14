import hashlib,json,pathlib,re,urllib.request
H=pathlib.Path(__file__).resolve().parent/'sources_gvl';url='https://generative-value-learning.github.io/gemini.html';b=urllib.request.urlopen(url,timeout=25).read();(H/'gemini.html').write_bytes(b);items=[{'url':url,'file':'gemini.html','sha256':hashlib.sha256(b).hexdigest()}]
for src in re.findall(r'<script[^>]+src=["\']([^"\']+)',b.decode()):
 if src.startswith(('http','//')):continue
 src=src.removeprefix('./');u='https://generative-value-learning.github.io/'+src.lstrip('/');d=urllib.request.urlopen(u,timeout=25).read();n=pathlib.Path(src).name;(H/n).write_bytes(d);items.append({'url':u,'file':n,'sha256':hashlib.sha256(d).hexdigest()})
(H/'demo_manifest.json').write_text(json.dumps(items,indent=2));print(json.dumps(items))

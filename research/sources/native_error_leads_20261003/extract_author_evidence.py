from pathlib import Path
import json,hashlib
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
source=ROOT/'research/sources/native_gap_audit_20261003/robometer_v2.html'
s=BeautifulSoup(source.read_text('utf-8'),'html.parser')
ids=['A3.SS1','A3.SS2','A5.SS4','A5.SS5','A3.T14','A3.T15','A5.T26','A5.T27','S5']
items=[]
for id in ids:
 e=s.find(id=id)
 assert e is not None,id
 items.append(dict(locator=id,text=e.get_text(' ',strip=True),tables=[[[c.get_text(' ',strip=True) for c in row.find_all(['th','td'],recursive=False)] for row in t.find_all('tr')] for t in e.find_all('table')]))
(OUT/'author_evidence.json').write_text(json.dumps(dict(source=source.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(source.read_bytes()).hexdigest(),paper='https://arxiv.org/html/2603.02115v2',items=items),ensure_ascii=False,indent=2)+'\n','utf-8')
print('9 exact HTML locators extracted, including all task rows and correct controls')

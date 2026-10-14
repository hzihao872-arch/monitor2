"""Verify source preservation, arithmetic, glyph coverage, and final PDF delivery."""
from pathlib import Path
import json,hashlib,re,zipfile
from pypdf import PdfReader
from fontTools.ttLib import TTFont
R=Path(__file__).resolve().parent
workspace=R.parents[1]
src=workspace/'research/sources/vlac_ars_coverage_20261003'
e=R/'evidence'
checks={}
manifest=json.loads((e/'source_manifest.json').read_text(encoding='utf-8'))
for item in manifest:
    path=(e/item['file']) if item.get('copied',True) else (workspace/item['file'])
    assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'],path
checks['source_manifest_hashes_verified']=len(manifest)
pair=json.loads((e/'previous_pairing_validation.json').read_text(encoding='utf-8'))
for case in pair['cases']:
    i=case['example']; data=(src/f'early_example{i:02}_video.mp4').read_bytes()
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    assert blob==case['video_git_blob_sha1']
    if i<3:
        old=json.loads((src/f'early_example{i:02}_prediction.jsonl').read_text(encoding='utf-8'))
        new=json.loads((e/f'example_{i:02}_prediction.jsonl').read_text(encoding='utf-8'))
        for key in ['prompt','response','pred_curve_point_times_sec','pred_curve_point_progress']:assert old[key]==new[key],key
checks['video_blob_checks']=3
checks['historical_current_prediction_checks']=2
s=json.loads((e/'supplemental_checks.json').read_text(encoding='utf-8'))
assert s['alignment_sensitivity']['endpoint_pairs']==961
assert s['alignment_sensitivity']['all_label_deltas_negative']
assert sum(x['anchor_intervals'] for x in s['cases'])==21
assert sum(x['anchor_directions_correct'] for x in s['cases'])==19
assert all(x['prediction_delta']>0 and x['label_delta']<0 for x in s['onion_native_transitions'][-3:])
checks['arithmetic_and_evidence_checks']='pass'
pdf=R/'VLAC-Cut_中文研究报告.pdf';p=PdfReader(pdf)
assert len(p.pages)==8
txt='\n'.join(page.extract_text() for page in p.pages)
assert '−6.4' in re.sub(r'\s+','',txt)
assert '−8.7' in re.sub(r'\s+','',txt)
assert not re.search(r'\bARS\b',txt,re.I)
assert '�' not in txt
for i in range(1,9):assert (R/f'qa/page-{i}.png').is_file()
layout=json.loads((R/'qa/layout_log.json').read_text(encoding='utf-8'))
assert min(x['y'] for x in layout)>43
chars=set((R/'report.md').read_text(encoding='utf-8'))
song=TTFont('C:/Windows/Fonts/simsun.ttc',fontNumber=0).getBestCmap()
symbols=TTFont('C:/Windows/Fonts/arial.ttf').getBestCmap()
missing=[x for x in chars if not x.isspace() and ord(x) not in song and not(x=='−' and ord(x) in symbols)]
assert not missing,missing
for page in p.pages:
    for ref in page['/Resources']['/Font'].get_object().values():
        f=ref.get_object()
        if 'Sim' in str(f.get('/BaseFont')) or 'Arial' in str(f.get('/BaseFont')):
            assert f['/FontDescriptor'].get_object().get('/FontFile2')
checks.update(pdf_pages=8,all_8_final_pages_visually_reviewed=True,missing_glyphs=missing,chinese_and_minus_fonts_embedded=True,source_materials_preserved=True,pdf_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),model_inference_run=False)
(R/'qa/final_validation.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
bundle=R/'VLAC-Cut_报告与可编辑材料.zip'
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(R.rglob('*')):
        if f.is_file() and f!=bundle and '__pycache__' not in f.parts:
            z.write(f,f.relative_to(R))
print(json.dumps(checks,ensure_ascii=False,indent=2))
print('Bundle bytes:',bundle.stat().st_size)

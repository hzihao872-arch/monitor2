"""Rebuild local screening records and verify source snapshots; no inference."""
from pathlib import Path
import json, hashlib
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'fetch_manifest.json').read_text('utf-8'))
for row in manifest:
    data=(ROOT/row['path']).read_bytes()
    assert len(data)==row['bytes']
    assert hashlib.sha256(data).hexdigest()==row['sha256'],row['path']
rows=[json.loads(x) for x in (ROOT/'RoboPulsePlusPlus.jsonl').read_text('utf-8').splitlines()]
records=[]
for eid in [18,19,29,30,617,618,620,621]:
    src=rows[eid-1]; files=sorted((ROOT/src['image_dir']).glob('*_view1.png'))
    ids=[int(f.stem.split('_')[0]) for f in files]
    records.append(dict(episode_id=eid,task_instruction=src['task_instruction'],author_segments=src['segments'],downloaded_view1_frames=ids,complete_published_view1=(ids==list(range(src['total_frames']))),original_full_rate_trajectory_verified=False,independent_review=False,h1_eligible=False,holdout_eligible=False))
records[-3]['single_reviewer_interpretation']='Green-on-blue visible after release at 11-16; retained through subsequent right-arm attempt in observed frames 17-29. Overall author progress is Falling after 18; this is not a negative label for every condition.'
records[-2]['single_reviewer_interpretation']='Potential task/image color mismatch: green on red, blue separate in viewed frames. Do not admit as success control.'
records[-1]['single_reviewer_interpretation']='Green-on-blue visible 14-23; right-arm approach followed by occlusion 24-26 and separated blocks at 27-28. Candidate loss, not an independently verified te/tv label.'
(ROOT/'screening_records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n','utf-8')
summary=dict(source_files=len(manifest),saved_source_bytes=sum(x['bytes'] for x in manifest),verified_sha256=True,published_complete_view1_episodes=[r['episode_id'] for r in records if r['complete_published_view1']],h1_run=False,model_run=False,failures=[{'action':'first metadata inspection','reason':'Windows default GBK decoding; retried explicit UTF-8'},{'action':'unexpanded ViFailback dataset API','reason':'response exceeded 5,000,000-byte per-file cap and was aborted; no partial file saved; retried expand=sha&expand=cardData'}])
(ROOT/'audit_summary.json').write_text(json.dumps(summary,indent=2)+'\n','utf-8')
canvas=Image.new('RGB',(960,550),'white'); draw=ImageDraw.Draw(canvas)
for row,(eid,indices,label) in enumerate([(618,[12,21,29],'ep618: earlier stack retained (single-reviewer candidate)'),(621,[18,23,28],'ep621: earlier stack lost (single-reviewer candidate)')]):
    y=row*275;draw.text((8,y+4),label,fill='black')
    for col,i in enumerate(indices):
        im=Image.open(ROOT/f'images/ep{eid:03d}/{i:03d}_view1.png');im.thumbnail((318,238));canvas.paste(im,(col*320,y+33));draw.text((col*320+8,y+19),f'Published frame {i}',fill='black')
canvas.save(ROOT/'candidate_pair.jpg')
print(json.dumps(summary))

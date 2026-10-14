"""Record single-reviewer packet inspection; no inference or downloads."""
from pathlib import Path
import json, hashlib, re
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
def read(p): return json.loads(p.read_text('utf-8-sig'))
def save(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
m=read(OUT/'input_manifest.json')
reviews=[]
for q in m['queries']:
    ep,b,i=q['episode'],q['branch'],q['query_index']
    if ep==618:
        current='retained_visible'
        note='Green-on-blue remains visible in inspected packet; later red placement fails. Same reviewer, not independent truth.'
    elif b=='published_array' and i==22:
        current='retained_visible';note='At source281 stack remains visible.'
    elif b=='published_array' and i==27:
        current='loss_visible_development_anchor';note='Source343 shows green on table and blue separated; prior source231 in same packet shows stack. Strongest inspected loss anchor, still same reviewer.'
    else:
        current='occlusion_or_transition_requires_review'
        note='Current support relation is partly occluded/transitioning; insufficiently clean for a reasoning-defect attribution. This does not prove inference is impossible.'
    reviews.append(dict(episode=ep,branch=b,query_index=i,source_frames=q['source_frames'],current_evidence=current,note=note,model_prediction=None))
    q['visibility_review']='visibility_review.json; single reviewer; no method prediction'
save(OUT/'input_manifest.json',m)
save(OUT/'visibility_review.json',dict(reviewer='same single reviewer; full-reference aware, not prefix-blinded',independent_annotation=False,author_condition_labels=False,author_native_labels_unchanged=True,all_queries_retained=True,queries=reviews))
save(OUT/'boundary_sensitivity.json',dict(status='conditional arithmetic only; NOT recovered author scoring mask',episode=621,published_interval=[22,28],closed_endpoint_trim_two=list(range(22,29))[2:-2],halfopen_endpoint_trim_two=list(range(22,28))[2:-2],clear_development_loss_anchor=27,anchor_trimmed_under_both=True,paper_actual_input_grid_unknown=True,paper_difference_alignment_unknown=True,raw_1fps_labels_not_transferred=True))
dm_path=ROOT/'experiments/data_manifest.json'
dm=read(dm_path)
dm['robometer_input_coordinate_audit_20261003']=dict(kind='local derived input-coordinate and visibility audit; no new episode',report='research/robometer_input_evidence_audit_20261003.md',manifest=(OUT/'input_manifest.json').relative_to(ROOT).as_posix(),source_hashes=(OUT/'source_hashes.json').relative_to(ROOT).as_posix(),visibility_review=(OUT/'visibility_review.json').relative_to(ROOT).as_posix(),episodes=[621,618],query_packets=28,derived_raw_video_pngs=19,network_bytes=0,models_run=0,author_predictions_available=False,reference_labels_modified=False,independent_review=False,split='development only; same physical episodes and all alternate views/resamplings',license='inherits existing upstream records; no new license determination')
save(dm_path,dm)
checks={}
checks['source_hashes']=all(sha(ROOT/x['path'])==x['sha256'] for x in read(OUT/'source_hashes.json'))
checks['derived_hashes']=all(sha(ROOT/x['path'])==x['sha256'] for x in read(OUT/'derived_frames.json'))
checks['28_packets']=len(m['queries'])==28
checks['19_derived_frames']=len(read(OUT/'derived_frames.json'))==19
checks['all_causal_pixel_indices']=all(max(q['source_frames'])==q['current_source_frame'] and len(q['source_frames'])==4 for q in m['queries'])
checks['no_predictions']=m['model_predictions'] is None and all(q['model_prediction'] is None for q in reviews)
protected=['experiments/run_ledger.csv','research/08_pilot_report.md','research/07_evaluation_protocol.md','experiments/config_stage7.json']
before=read(OUT/'before_edit.json')
checks['protected_files_unchanged']=all(sha(ROOT/x['path'])==x['sha256'] for x in before if x['path'] in protected)
checks['json_parse']=all(read(p) is not None for p in OUT.glob('*.json')) and read(dm_path) is not None
report=ROOT/'research/robometer_input_evidence_audit_20261003.md'
# These two generated files are linked by the report and finalized below.
for name in ['validation.json','artifact_hashes.json']:
    if not (OUT/name).exists(): save(OUT/name,dict(status='pending finalization'))
links=re.findall(r'\]\(([^)]+)\)',report.read_text('utf-8'))
bad=[s for s in links if not s.startswith(('https://','http://','#')) and not (report.parent/s.split('#')[0]).exists()]
checks['report_local_links']=not bad
save(OUT/'validation.json',dict(passed=all(checks.values()),checks=checks,bad_links=bad,models_run=0,downloads=0))
files=[p for p in OUT.rglob('*') if p.is_file() and 'before' not in p.parts and p.name!='artifact_hashes.json']
save(OUT/'artifact_hashes.json',[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in files])
print(json.dumps(checks,ensure_ascii=False))
assert all(checks.values())

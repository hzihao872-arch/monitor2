"""Record source observations and native-task bindings; no model outputs generated."""
from pathlib import Path
import hashlib,json,collections
from bs4 import BeautifulSoup
from audit_sources import OUT,ROOT,REV,save

rows=[json.loads(x) for x in (ROOT/'research/sources/recovery_search_20261003/RoboPulsePlusPlus.jsonl').read_text('utf-8').splitlines()]
manifest=json.loads((OUT/'fetch_manifest.json').read_text('utf-8'))
cases=[]
observations={
510:dict(frames=[0,5,10,16],observation='At 0 the short vial is left of the rack; by 16 it appears in the left rack slot. The long target tube remains in the cup in the inspected terminal frame. Sparse inspection only; no later-subtask success established.',HD='not a verified positive; sparse frames show no later tube placement success'),
513:dict(frames=list(range(19)),observation='All 19 release view1 frames inspected. Short dark-capped vial initially left of rack; moved into left rack slot, visible after gripper withdrawal at 9-11 and still visible at 16-18. Right gripper approaches long orange-filled tube in transparent cup at 12-15, withdraws by 16-18; target tube remains in cup. Existing tall tube already in rack at 0 is not the queried tube. No later placement success, no visible loss of earlier vial placement, no repair observed in released sequence.',HD='excluded as H-D positive; retain as later noncompletion with earlier outcome retained; one reviewer, release frames only'),
514:dict(frames=[0,6,12,19],observation='Short vial initially left of rack; visible in left slot at 12 and 19. Target long tube is lifted from cup by 19 but remains at gripper near/above right slot; release and completed insertion cannot be confirmed from inspected frames.',HD='not a verified positive; do not equate rising annotation with completed second subtask')}
for ep in [510,513,514]:
 row=next(r for r in rows if r['episode_id']==ep)
 files=[r for r in manifest if r['path'].startswith(f'images/ep{ep}/')]
 cases.append(dict(case_id=f'RoboPulse++-ep{ep}',author_record=row,revision=REV,
     method_native_task='RoboMeter / Robo-Dopamine as evaluated by PRM-as-a-Judge C.4: task-conditioned overall progress direction',
     native_output='RoboMeter overall progress sequence; difference and five-point causal average mapped to sign. Dopamine mode-specific progress/hop, then C.4 mapping.',
     author_prediction_available=False,model_runs=0,
     clock='zero-based logical-frame coordinates, exact PNG name binding; source video FPS/extraction phase/physical clock not verified; do not convert index to seconds',
     interval_convention='raw start_frame and end_frame preserved; paper uses closed brackets; data card says boundary, does not settle scorer endpoint/difference alignment',
     author_label_semantics='1 rising; 0 stagnant; -1 falling, not necessarily irreversible; not individual-condition or later-subtask completion labels',
     object_binding='short dark-capped vial originally left of rack; target long tube originally in transparent cup to right; tall pre-existing rack tube is a separate object',
     task_revision='fixed dataset revision; execution-time instruction revision history unavailable',
     inspection=observations[ep],files=[dict(path=x['path'],bytes=x['bytes'],sha256=x['sha256']) for x in files],
     license='RoboPulse++ card: other; aggregation terms unresolved. Original physical episode and upstream license not bound for these three. Local provenance inspection only; not cleared as model inference/evaluation input.',
     split='author test; project development-only',independent_review=False,
     duplicates='exclude all future upstream matches, alternate views, crops and resamplings of these physical episodes from holdout; cross-episode physical duplication not independently established',
     reusable=['instruction','episode/revision','release frame coordinates','original overall direction annotations','PNG bytes/hash'],
     missing=['author per-episode predictions','Table 8 membership','C.4 exact scorer and valid-point mask','upstream episode/video and clock','upstream license binding','independent condition/visibility review']))
save('case_registry.json',dict(version='native-gap-binding-1',frozen_scope='scope.json before media/model outputs',native_predictions_seen=False,cases=cases))

stats=dict(episodes=len(rows),distinct_exact_task_strings=len({r['task_instruction'] for r in rows}),logical_frames=sum(r['total_frames'] for r in rows),segments_by_label=dict(collections.Counter(str(s['reward_label']) for r in rows for s in r['segments'])),paper_task_entries=275,paper_intervals=2244)
stats['not_a_scored_denominator']='C.4 binary scoring excludes boundary points; zero-labelled segments and zero predicted changes need exact scorer. Counts below are conditional arithmetic only, not author scored samples.'
stats['ep513_falling_boundary_arithmetic']={'raw':[14,18],'closed_frame_set_after_removing_first_last_two':[16],'half_open_frame_set_after_removing_first_last_two':[],'actual_scored_points':None}
save('native_denominator_audit.json',stats)

# Reuse and hash exact existing primary sources, preserving original files.
paths=['research/sources/recovery_search_20261003/robopulse_paper.html','research/sources/recovery_search_20261003/RoboPulsePlusPlus.jsonl','research/sources/recovery_search_20261003/robopulse_README.md','research/sources/recovery_search_20261003/robopulse_discussion2.json','research/sources/system_refresh_20261003/progresscompass_v1.html','research/sources/system_refresh_20261003/r2vlm_v1.html','research/sources/system_refresh_20261003/robomonitor_v1.html','research/sources/direction_selection_20261003/robodopamine2_v1.html','research/sources/direction_selection_20261003/eval_server.py','research/sources/prm_scope_review_20261003/official/eval/prm_judge/prm/robometer.py','research/sources/prm_scope_review_20261003/official/eval/prm_judge/prm/dopamine_inference.py','research/sources/baseline_diagnostic_20261003/case_registry.json','research/sources/recovery_search_20261003/upstream_trace/source_mapping.json','research/sources/recovery_search_20261003/upstream_trace/native_label_mapping.json','research/sources/system_refresh_20261003/selection.json','research/sources/system_refresh_20261003/fetch_manifest.json','research/sources/evonav_main.pdf','research/sources/evonav_supp.pdf']
save('reused_sources.json',[dict(path=p,bytes=(ROOT/p).stat().st_size,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in paths])

save('inference_readiness.json',dict(models_run=0,paid_api_calls=0,new_weights=0,hardware_reassessment_for_inference=False,
   robometer=dict(code_revision='352d160389daa964788de1ec933d1925f3a6de4f',weight_revision='beef63bc914c5c189329d49c6d712d96d632aa34',status='prior checked cache lacks exact checkpoint; no new weights; C.4 scorer and Table 8 subset unknown',input='task plus causal prefix sampled at four linspace indices in fixed server; exact paper configurations remain distinct'),
   r2vlm=dict(code_revision='3b5c09ff1baea40301a790a0c15048df3fc81a5b',weight_revision='6c84c9bffe680e310ad7fcaaf7016134e0a0608f',status='official single-sample runner now audited; exact weights and ALFRED source images not available locally in prior audit',runner='code/script/Alfred/infer_vllm_single.py',fields=['question','turns[].images','optional task/item_id'],output=['raw_output','history_cot','model_answer'],server='local OpenAI-compatible endpoint; not executed',paper_exactness='sample runner does not establish complete Table 1 scoring configuration'),
   progresscompass=dict(status='same-day project snapshot code coming soon; benchmark explicitly no baseline predictions; live web open failed this turn; eight-frame paper runner not available'),
   dopamine=dict(code_revision='2c714abca66329f8e2113587226bc9556726f6c2',preview_revision='980f3d1819c870f62c36169a9486e971049bb09a',status='no exact local paper weights established; preview not silently equated with August 2.0 or PRM paper checkpoint'),
   robomonitor=dict(status='no verified released task-trained weights/runner; task-supervised setup incompatible with no-training recreation')))

data_path=ROOT/'experiments/data_manifest.json';d=json.loads(data_path.read_text('utf-8'))
name='RoboPulse++ ep510/513/514 bounded native-task material audit'
if not any(s['name']==name for s in d['sources']):
 files=[]
 for name_ in ['fetch_manifest.json','case_registry.json','native_denominator_audit.json']:
  p=OUT/name_;files.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 d['sources'].append(dict(name=name,source_url='https://huggingface.co/datasets/lyy0715/RoboPulsePlusPlus',revision=REV,license='other; upstream identity/license not yet bound; source inspection only',role='native_material_development_only',holdout_eligible=False,h1_development_eligible=False,files=files,available='27 release PNGs: all 19 ep513 view1 frames plus 4 each for ep510/514, exact original task/interval binding. ep513 excluded as H-D positive; earlier vial retained and later tube placement not completed, single reviewer.',h1_missing='author predictions, upstream raw identity/time/license, independent labels and C.4 valid-point mask',provenance_manifest='research/sources/native_gap_audit_20261003/fetch_manifest.json',report='research/native_task_gap_audit_20261003.md'))
 d['holdout_exclusions']['native_gap_audit_ep510_513_514']='All three inspected episodes and any upstream physical matches, views or resamplings remain development-only. 27 images are not 27 independent cases.'
 d['updated_local_date']='2026-10-03'
 data_path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps(stats,ensure_ascii=False));print('source files',len(manifest),'download bytes',sum(r['bytes'] for r in manifest))

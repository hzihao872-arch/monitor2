"""Verify archived author evidence, without inference or dataset-wide claims."""
from pathlib import Path
import hashlib
import json
import subprocess
import numpy as np

b = Path(__file__).resolve().parent
def read(name):
    return json.loads((b / name).read_text(encoding='utf-8'))
tree = json.loads((b.parent / 'new_baseline_search_20261003/vlaccut_tree.json').read_text(encoding='utf-8'))
entries = {x['path']: x for x in tree['tree']}
result = {'model_inference_run': False, 'github_revision': tree['sha'], 'cases': []}
inputs = []
for i in (1, 2, 3):
    m = read(f'early_example{i:02}_metadata.json')
    p = read(f'current_example{i:02}_prediction.jsonl')
    video = b / f'early_example{i:02}_video.mp4'
    data = video.read_bytes()
    blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    expected = entries[f'examples/example_{i:02}/episode.mp4']['sha']
    assert blob == expected
    stats = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,r_frame_rate,nb_frames', '-of', 'json', str(video)], text=True))['streams'][0]
    assert int(stats['nb_frames']) == m['num_frames']
    item = {'example': i, 'global_episode_id': m['global_episode_id'], 'bucket': m['bucket'],
            'video_git_blob_sha1': blob, 'matches_current_github_video': True, 'video_stats': stats}
    if i < 3:
        old = read(f'early_example{i:02}_prediction.jsonl')
        fields = ['prompt', 'response', 'pred_curve_point_times_sec', 'pred_curve_point_progress']
        item['old_current_equal'] = {k: old[k] == p[k] for k in fields}
        assert all(item['old_current_equal'].values())
        assert old['input_frame_indices_2hz'] == p['input_frame_indices']
        assert old['benchmark_semantic_anchors'] == m['benchmark_semantic_anchors']
        assert old['gt_dense_progress'] == m['benchmark_dense_progress']
        recomputed = np.interp(old['gt_dense_timestamps_sec'], p['pred_curve_point_times_sec'], p['pred_curve_point_progress'])
        item['dense_interpolation_max_abs_difference_from_author'] = float(np.max(np.abs(recomputed - old['pred_dense_progress_aligned_to_gt'])))
        assert item['dense_interpolation_max_abs_difference_from_author'] < 1e-9
        item['recomputed_dense_mae'] = float(np.mean(np.abs(recomputed - old['gt_dense_progress'])))
        item['author_curve_metrics'] = old['curve_compare_metrics']
    result['cases'].append(item)
    # Model input deliberately excludes trajectory labels, predictions and outcome-bearing source IDs.
    inputs.append({'case_id': f'case_{i:02}', 'video_path': str(video),
                   'task_instruction': m['task_instruction'], 'task_description_with_rubric': m['task_description'],
                   'fps': m['fps'], 'num_frames': m['num_frames']})

manifest = read('fetch_manifest.json')
checked = 0
for f in manifest:
    if 'sha256' not in f:
        continue
    data = (b / f['name']).read_bytes()
    assert len(data) == f['bytes']
    assert hashlib.sha256(data).hexdigest() == f['sha256']
    checked += 1
result['downloaded_sources_hash_verified'] = checked
result['public_prediction_paths'] = [p for p in entries if p.endswith('.jsonl')]

# Parse only complete records from three explicitly partial HTTP Range downloads.
prefix_summary = []
for path in sorted(b.glob('*prefix.json.part')):
    raw = path.read_bytes().decode('utf-8', errors='ignore').lstrip()
    assert raw.startswith('[')
    rest = raw[1:].lstrip()
    rows = []
    while rest and not rest.startswith(']'):
        try:
            row, end = json.JSONDecoder().raw_decode(rest)
        except json.JSONDecodeError:
            break
        md = row['metadata']
        desc = md.get('task_description', '')
        rows.append({'global_episode_id': row['global_episode_id'],
                     'task_instruction': md.get('task_instruction'), 'task_description': desc,
                     'contains_percent_symbol': '%' in desc})
        rest = rest[end:].lstrip().lstrip(',').lstrip()
    prefix_summary.append({'file': path.name, 'partial_file': True, 'complete_records_read': len(rows), 'records': rows})
result['prefix_task_description_check'] = prefix_summary

m = read('early_example02_metadata.json')
p = read('current_example02_prediction.jsonl')
points = []
for t, val in zip(p['pred_curve_point_times_sec'], p['pred_curve_point_progress']):
    frame = round(t * m['fps'])
    points.append({'native_output_time_sec': t, 'frame': frame, 'native_pred_progress': val,
                   'author_dense_gt_at_frame': m['benchmark_dense_progress'][frame]})
result['onion_native_prediction_points'] = points
selected = [x for x in points if x['frame'] in (183, 249)]
assert len(selected) == 2
assert selected[1]['native_pred_progress'] > selected[0]['native_pred_progress']
assert selected[1]['author_dense_gt_at_frame'] < selected[0]['author_dense_gt_at_frame']
result['onion_error_present_without_interpolating_predictions'] = True

(b / 'pairing_validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
(b / 'comparison_inputs.json').write_text(json.dumps({'status': 'prepared_not_executed',
    'use': 'Development-only cases; pass only selected task field and video pixels to evaluator. Do not expose source metadata or filename-derived outcomes.',
    'cases': inputs}, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'cases': result['cases'], 'source_hashes_checked': checked,
    'prefix_record_counts': [x['complete_records_read'] for x in prefix_summary], 'native_onion_pair': selected}, ensure_ascii=False, indent=2))

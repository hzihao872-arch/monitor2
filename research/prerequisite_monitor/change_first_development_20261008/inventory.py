"""Private read-only inventory of the eighteen exposed A/B development clips."""
import argparse
import hashlib
import json
from pathlib import Path

import cv2

FAMILIES = ('access_gate', 'support_surface')


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def inventory(workspace):
    root = Path(workspace)
    rows = []
    for family in FAMILIES:
        base = root / 'research/prerequisite_monitor/fresh_scenes_20261006' / family / 'dev_v2'
        manifest = [json.loads(x) for x in (base/'model_input/manifest.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
        mapping = json.loads((base/'truth/condition_map.json').read_text(encoding='utf-8'))
        if len(manifest) != 9 or set(mapping) != {m['video'] for m in manifest}:
            raise ValueError(f'incomplete source group: {family}')
        for m in manifest:
            video = base / 'model_input' / m['video']
            actual = sha(video)
            if actual != m['sha256']:
                raise ValueError(f'source hash mismatch: {video}')
            cap = cv2.VideoCapture(str(video))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            cap.release()
            if fps < .5 or frames < 15:
                raise ValueError(f'invalid media: {video}')
            rows.append({'family': family, 'condition': mapping[m['video']], 'source': str(video.resolve()),
                         'source_sha256': actual, 'goal': m['instruction'], 'fps': fps,
                         'frame_count': int(frames), 'last_sample_ms': 14000,
                         'source_manifest_sha256': sha(base/'model_input/manifest.jsonl')})
    if len(rows) != 18 or len({r['source_sha256'] for r in rows}) != 18:
        raise ValueError('expected 18 unique development videos')
    return rows


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--workspace', required=True)
    ap.add_argument('--output', required=True)
    a = ap.parse_args()
    dest = Path(a.output)
    if dest.exists():
        raise FileExistsError(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps({'scope':'private_development_exposed', 'clips':inventory(a.workspace)}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(dest, '18 unique clips')

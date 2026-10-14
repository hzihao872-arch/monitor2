"""Read public author outputs; no model inference. Run with workspace .venv Python."""
from pathlib import Path
import json
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

b = Path(__file__).resolve().parent
out = []
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 18)
for i in (1, 2, 3):
    m = json.loads((b / f'early_example{i:02}_metadata.json').read_text(encoding='utf-8'))
    pred_file = f'early_example{i:02}_prediction.jsonl' if i < 3 else 'current_example03_prediction.jsonl'
    p = json.loads((b / pred_file).read_text(encoding='utf-8'))
    anchors = m['benchmark_semantic_anchors']
    times, vals = p['pred_curve_point_times_sec'], p['pred_curve_point_progress']
    rows = []
    for a, z in zip(anchors, anchors[1:]):
        pa = float(np.interp(a['frame'] / m['fps'], times, vals))
        pz = float(np.interp(z['frame'] / m['fps'], times, vals))
        delta, pd = z['progress'] - a['progress'], pz - pa
        rows.append(dict(start_frame=a['frame'], end_frame=z['frame'],
                         gt_start=a['progress'], gt_end=z['progress'], gt_delta=delta,
                         pred_start=round(pa, 6), pred_end=round(pz, 6), pred_delta=round(pd, 6),
                         direction_agrees=bool(np.sign(delta) == np.sign(pd)),
                         endpoint_clamping=bool(a['frame']/m['fps'] < times[0] or z['frame']/m['fps'] > times[-1])))
    out.append(dict(example=i, global_episode_id=m['global_episode_id'], fps=m['fps'],
                    frames=m['num_frames'], transitions=rows))
    print('EXAMPLE', i, json.dumps(rows))
    ids = sorted(set(p.get('input_frame_indices_2hz', p.get('input_frame_indices',
                 list(range(0, m['num_frames'], 15)))) + [a['frame'] for a in anchors]))
    vf = 'select=' + '+'.join(f'eq(n\\,{f})' for f in ids) + ',scale=360:-1'
    folder = b / f'frames_{i:02}'
    folder.mkdir(exist_ok=True)
    cp = subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i',
                         str(b/f'early_example{i:02}_video.mp4'), '-vf', vf, '-vsync', '0',
                         str(folder/'%03d.png')], capture_output=True, text=True)
    if cp.returncode:
        raise RuntimeError(cp.stderr)
    imgs = sorted(folder.glob('*.png'))
    assert len(imgs) == len(ids), (len(imgs), len(ids))
    w, h, pad, cols = 360, 270, 26, 4
    sheet = Image.new('RGB', (w*cols, (h+pad)*((len(ids)+cols-1)//cols)), (245,245,245))
    draw = ImageDraw.Draw(sheet)
    for n, (fp, fr) in enumerate(zip(imgs, ids)):
        im = Image.open(fp)
        im.thumbnail((w,h))
        x, y = n % cols * w, n // cols * (h+pad)
        sheet.paste(im, (x,y))
        draw.text((x+5,y+h), f'frame {fr} / {fr/m["fps"]:.2f}s', font=font, fill='black')
    sheet.save(b/f'contact_{i:02}.jpg', quality=85)
    (folder/'frame_map.json').write_text(json.dumps([dict(file=f.name, original_frame=fr)
         for f,fr in zip(imgs,ids)], indent=2), encoding='utf-8')
(b/'anchor_diagnostic.json').write_text(json.dumps(out,indent=2),encoding='utf-8')

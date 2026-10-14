"""Private CPU-only probe of persistent first-to-last visual differences."""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw


def probe(inventory, output):
    rows = json.loads(Path(inventory).read_text(encoding='utf-8'))['clips']
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    summary = []
    for row in rows:
        if row['condition'] not in {'E', 'R'}:
            continue
        cap = cv2.VideoCapture(row['source'])
        frames = []
        for _ in range(15):
            ok, bgr = cap.read()
            if not ok:
                raise ValueError('missing frame')
            frames.append(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        cap.release()
        gray = [cv2.resize(cv2.cvtColor(f, cv2.COLOR_RGB2GRAY), (64, 48)).astype(np.int16)
                for f in frames]
        diff = gray[-1] - gray[0]
        mask = (np.abs(diff - np.median(diff)) > 18).astype(np.uint8)
        count, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
        ranked = sorted((stats[k] for k in range(1, count) if stats[k, cv2.CC_STAT_AREA] >= 3),
                        key=lambda s: -s[cv2.CC_STAT_AREA])
        h, w = frames[0].shape[:2]
        boxes = []
        for component in ranked[:3]:
            x, y, bw, bh, area = map(int, component)
            boxes.append({'bbox_xyxy': [int(x*w/64), int(y*h/48),
                                        int((x+bw)*w/64), int((y+bh)*h/48)], 'area': area})
        sheet = Image.new('RGB', (w*2, h), 'white')
        for side, frame in enumerate((frames[0], frames[-1])):
            sheet.paste(Image.fromarray(frame), (side*w, 0))
        draw = ImageDraw.Draw(sheet)
        for index, box in enumerate(boxes):
            color = ('red', 'cyan', 'yellow')[index]
            for side in (0, 1):
                x1, y1, x2, y2 = box['bbox_xyxy']
                draw.rectangle((x1+side*w, y1, x2+side*w, y2), outline=color, width=2)
        name = f"{row['family']}_{row['condition']}.png"
        sheet.save(output / name)
        summary.append({'family': row['family'], 'condition': row['condition'], 'boxes': boxes,
                        'sheet': name})
    (output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    return summary


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--inventory', required=True)
    p.add_argument('--output', required=True)
    a = p.parse_args()
    print(len(probe(a.inventory, a.output)), 'endpoint probes')

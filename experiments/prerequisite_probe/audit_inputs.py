"""Inspect the exact decoded frames presented to both model interfaces."""

import argparse
import hashlib
import json
from pathlib import Path

import cv2
from PIL import Image, ImageDraw

from .probe import SIZE, sample_indices


def decode(path):
    cap = cv2.VideoCapture(str(path))
    frames = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    cap.release()
    return frames


def audit(root):
    input_dir = root / "model_input"
    truth = root / "truth"
    truth.mkdir(exist_ok=True)
    columns = (0, 3, 6, 9, 14)
    sheet = Image.new("RGB", (320 * len(columns), 256 * 6), "white")
    draw = ImageDraw.Draw(sheet)
    records = []
    for row, video in enumerate(sorted(input_dir.glob("*.mp4"))):
        frames = decode(video)
        if len(frames) != 15 or any(frame.shape != (SIZE[1], SIZE[0], 3) for frame in frames):
            raise RuntimeError(f"Unexpected model input shape: {video}, {[x.shape for x in frames]}")
        records.append({
            "video": video.name, "decoded_frame_count": len(frames), "width": SIZE[0], "height": SIZE[1],
            "source_indices_30fps": sample_indices(),
            "decoded_rgb_sha256": [hashlib.sha256(frame.tobytes()).hexdigest() for frame in frames],
        })
        for col, index in enumerate(columns):
            picture = Image.fromarray(frames[index]).resize((320, 240))
            sheet.paste(picture, (col * 320, row * 256 + 16))
            draw.text((col * 320 + 5, row * 256 + 2), f"{video.stem} t={index}s", fill="black")
    if len(records) != 6:
        raise RuntimeError(f"Expected six videos, found {len(records)}")
    (truth / "actual_frames.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    sheet.save(truth / "contact_sheet.png")
    return records


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("experiments/prerequisite_probe/artifacts"))
    args = parser.parse_args()
    print(json.dumps([x["video"] for x in audit(args.root)]))

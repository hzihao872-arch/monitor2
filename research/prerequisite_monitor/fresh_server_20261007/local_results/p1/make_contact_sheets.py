"""Local-only visual audit of frozen model-input frames after blind review."""

from __future__ import annotations

import json
from pathlib import Path

import cv2
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[3] / "fresh_scenes_20261006"
OUT = Path(__file__).resolve().parent
SECONDS = (0, 7, 8, 14)
CONDITIONS = ("E", "N_o", "N_b", "R")
TILE = (480, 360)
HEADER = 28


def main() -> None:
    for arm in ("access_gate", "support_surface"):
        base = ROOT / arm / "dev_v2"
        mapping = json.loads((base / "truth" / "condition_map.json").read_text(encoding="utf-8"))
        reverse = {condition: video for video, condition in mapping.items()}
        canvas = Image.new("RGB", (TILE[0] * len(SECONDS), (TILE[1] + HEADER) * len(CONDITIONS)), "white")
        draw = ImageDraw.Draw(canvas)
        for row, condition in enumerate(CONDITIONS):
            video = reverse[condition]
            capture = cv2.VideoCapture(str(base / "model_input" / video))
            if not capture.isOpened():
                raise RuntimeError(f"Cannot open {arm}/{video}")
            for col, second in enumerate(SECONDS):
                capture.set(cv2.CAP_PROP_POS_FRAMES, second)
                ok, frame = capture.read()
                if not ok:
                    raise RuntimeError(f"Cannot read {arm}/{video} frame {second}")
                image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                image = image.resize(TILE)
                x, y = col * TILE[0], row * (TILE[1] + HEADER)
                draw.text((x + 6, y + 6), f"{arm} {condition} ({video}) t={second}", fill="black")
                canvas.paste(image, (x, y + HEADER))
            capture.release()
        canvas.save(OUT / f"{arm}_state_audit.png")


if __name__ == "__main__":
    main()

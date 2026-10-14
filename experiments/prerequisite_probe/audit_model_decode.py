"""Record bytes actually decoded from the six frozen model input videos."""

import argparse
import hashlib
import json
from pathlib import Path

import cv2


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def opencv_frames(path: Path):
    cap = cv2.VideoCapture(str(path))
    frames = []
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    finally:
        cap.release()
    return frames


def robometer_frames(path: Path):
    from robometer.evals.eval_viz_utils import extract_frames

    return extract_frames(str(path), fps=1.0, max_frames=512)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=["opencv", "robometer"], required=True)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    decode = opencv_frames if args.backend == "opencv" else robometer_frames
    entries = []
    for number in range(1, 7):
        path = args.input_dir / f"{number:04d}.mp4"
        frames = decode(path)
        if len(frames) != 15 or any(frame.shape != (480, 640, 3) for frame in frames):
            raise RuntimeError(f"Unexpected frame shape or count for {path.name}")
        video_sha = sha256_file(path)
        entries.append({
            "video": path.name,
            "video_sha256": video_sha,
            "decoded_frame_count": len(frames),
            "frame_shape_rgb": [480, 640, 3],
            "decoded_rgb_sha256": [hashlib.sha256(frame.tobytes()).hexdigest() for frame in frames],
        })
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"backend": args.backend, "videos": entries}, indent=2) + "\n", encoding="utf-8")
    print(f"AUDITED {args.backend} {len(entries)} videos -> {args.out}")


if __name__ == "__main__":
    main()

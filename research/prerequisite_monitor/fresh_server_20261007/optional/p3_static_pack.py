"""Locally build eight anonymous exact-pixel static-end-state diagnostic videos."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import subprocess
import zipfile
from pathlib import Path

CONDITIONS = ("N_b", "S", "N_o", "G")
PATTERN = (12,) * 5 + (13,) * 5 + (14,) * 5


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_frames(path: Path, expected: list[str]):
    import cv2

    capture = cv2.VideoCapture(str(path))
    frames = []
    try:
        while True:
            okay, frame = capture.read()
            if not okay:
                break
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(rgb)
    finally:
        capture.release()
    hashes = [hashlib.sha256(frame.tobytes()).hexdigest() for frame in frames]
    if len(frames) != 15 or hashes != expected:
        raise ValueError("source or generated pixels differ from expected 15 frames")
    return frames


def encode_exact(frames, path: Path) -> None:
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "rawvideo",
               "-pixel_format", "rgb24", "-video_size", "640x480", "-framerate", "1", "-i", "-",
               "-c:v", "libx264rgb", "-crf", "0", "-preset", "ultrafast", "-pix_fmt", "rgb24", str(path)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        assert process.stdin is not None
        for frame in frames:
            process.stdin.write(frame.tobytes())
        process.stdin.close()
        assert process.stderr is not None
        error = process.stderr.read().decode("utf-8", errors="replace")
        process.stderr.close()
        status = process.wait()
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
    if status != 0:
        raise RuntimeError("ffmpeg lossless RGB encode failed: " + error[-1000:])


def generate(frozen: Path, output: Path) -> dict:
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    report = {"scope": "P3_out_of_distribution_static_end_state", "repeat_source_seconds": PATTERN,
              "encoding": "libx264rgb crf=0 rgb24 1fps", "clip_count": 0, "arms": {}}
    for arm, seed in (("access_gate", 20261007), ("support_surface", 20261008)):
        source = frozen / arm / "dev_v2"
        source_input = source / "model_input"
        source_rows = {row["video"]: row for row in (json.loads(line) for line in
                       (source_input / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip())}
        source_media = json.loads((source_input / "media_hashes.json").read_text(encoding="utf-8"))
        media_map = {entry["video"]: entry for entry in source_media["clips"]}
        truth_map = json.loads((source / "truth/condition_map.json").read_text(encoding="utf-8"))
        by_condition = {condition: video for video, condition in truth_map.items()}
        if set(CONDITIONS) - set(by_condition):
            raise ValueError("missing required local conditions")
        order = list(CONDITIONS)
        random.Random(seed).shuffle(order)
        target = output / arm / "model_input"
        target.mkdir(parents=True)
        instruction = next(iter(source_rows.values()))["instruction"]
        (target / "instruction.txt").write_text(instruction + "\n", encoding="utf-8")
        manifest_rows, media_rows, local_map = [], [], {}
        for index, condition in enumerate(order, 1):
            src_video = by_condition[condition]
            src_hashes = media_map[src_video]["decoded_rgb_sha256"]
            source_frames = read_frames(source_input / src_video, src_hashes)
            chosen = [source_frames[t] for t in PATTERN]
            name = f"{index:04}.mp4"
            path = target / name
            encode_exact(chosen, path)
            target_hashes = [src_hashes[t] for t in PATTERN]
            read_frames(path, target_hashes)
            video_sha = sha256(path)
            manifest_rows.append({"video": name, "instruction": instruction, "sha256": video_sha,
                                  "fps": 1, "frame_indices_from_30fps": list(range(0, 450, 30))})
            media_rows.append({"video": name, "video_sha256": video_sha, "decoded_rgb_sha256": target_hashes})
            local_map[name] = {"condition": condition, "source_video": src_video,
                               "source_video_sha256": source_rows[src_video]["sha256"],
                               "source_seconds": PATTERN, "source_pixel_sha256": target_hashes,
                               "static_video_sha256": video_sha}
            report["clip_count"] += 1
        (target / "manifest.jsonl").write_text("".join(json.dumps(x) + "\n" for x in manifest_rows), encoding="utf-8")
        (target / "media_hashes.json").write_text(json.dumps({"clips": media_rows}, indent=2) + "\n", encoding="utf-8")
        arm_dir = output / arm
        (arm_dir / "mapping_local_only.json").write_text(json.dumps(local_map, indent=2) + "\n", encoding="utf-8")
        zip_path = arm_dir / "model_input.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in sorted(target.iterdir()):
                archive.write(path, path.name)
        report["arms"][arm] = {"zip_sha256": sha256(zip_path), "video_count": 4,
                               "mapping_sha256_local_only": sha256(arm_dir / "mapping_local_only.json")}
    (output / "build_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frozen", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(generate(args.frozen, args.output), indent=2))


if __name__ == "__main__":
    main()

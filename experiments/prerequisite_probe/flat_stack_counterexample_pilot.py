"""Blind visual challenge for the blue-on-red versus direct-table ambiguity."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

import numpy as np

from .distractor_scenes import make_flat_with_distractor
from .flat_square_dev import FlatSquareSpec, INSTRUCTION, evaluate_terminal
from .flat_square_operational_check import RetryIK
from .flat_square_route_challenge import direct_place_spec, position
from .probe import FPS, PandaIK, SIZE
from .produce import action_at, build_keyframes, ffmpeg_writer, sha256
from .scene_observability_pilot import decoded_frame_hashes


CASES = (("blocked", "clip_2407.mp4"), ("open", "clip_8193.mp4"))
SECONDS = 15


def record_one(red_start, video):
    env = make_flat_with_distractor(red_start)
    try:
        env.reset(seed=20261005)
        scene = env.unwrapped
        keyframes, ik_errors = build_keyframes(env, direct_place_spec(), RetryIK(PandaIK()))
        indices, raw_hashes = [], []
        writer = ffmpeg_writer(video, 1)
        try:
            for index in range(SECONDS * FPS):
                if index:
                    env.step(action_at(index / FPS, keyframes))
                if index % FPS == 0:
                    frame = np.ascontiguousarray(env.render().cpu().numpy()[0])
                    if frame.shape != (SIZE[1], SIZE[0], 3):
                        raise RuntimeError(frame.shape)
                    writer.stdin.write(frame.tobytes())
                    indices.append(index)
                    raw_hashes.append(hashlib.sha256(frame.tobytes()).hexdigest())
        finally:
            writer.stdin.close()
            stderr = writer.stderr.read().decode(errors="replace")
            if writer.wait():
                raise RuntimeError(stderr)
        decoded = decoded_frame_hashes(video)
        if len(decoded) != SECONDS:
            raise RuntimeError(f"expected {SECONDS} decoded frames")
        return {
            "condition": red_start, "video": video.name,
            "blue_end_xyz": position(scene.blue),
            "red_end_xyz": position(scene.red),
            "terminal": evaluate_terminal(list(scene._terminal_window), FlatSquareSpec()),
            "terminal_sample": scene._terminal_sample(),
            "ik_errors": ik_errors, "sample_indices_30fps": indices,
            "raw_rgb_sha256": raw_hashes, "decoded_rgb_sha256": decoded,
            "video_sha256": sha256(video),
        }
    finally:
        env.close()


def run(output):
    observer = output / "observer_only"
    truth = output / "truth"
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(output)
    observer.mkdir(parents=True)
    truth.mkdir(parents=True)
    records = [record_one(start, observer / name) for start, name in CASES]
    manifest = {
        "protocol": "flat_stack_counterexample_pilot_v1",
        "instruction": INSTRUCTION,
        "video_format": {"duration_s": SECONDS, "fps": 1,
                         "width": SIZE[0], "height": SIZE[1]},
        "clips": [{"video": row["video"], "video_sha256": row["video_sha256"],
                   "sample_indices_30fps": row["sample_indices_30fps"],
                   "decoded_rgb_sha256": row["decoded_rgb_sha256"]}
                  for row in sorted(records, key=lambda r: r["video"])],
    }
    (observer / "media_hashes.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (observer / "instruction.txt").write_text(INSTRUCTION + "\n", encoding="utf-8")
    (observer / "reviewer_packet.md").write_text(
        "# 平面方框主视角终态审读\n\n"
        "只看本目录两段匿名视频与目标句。可重复播放、裁剪；不要看研究目录的真值。\n\n"
        f"> {INSTRUCTION}\n\n"
        "逐段判断第 14 秒是否已经满足整个最终目标；重点写蓝块底面是否能看出直接贴着桌面，"
        "或是否由别的物体承托。如看不清，请写『无法判断』及需要的画面，勿猜。\n\n"
        "| 视频 | 已完成/未完成/无法判断 | 依据的画面关系与时点 | 看不清处 |\n"
        "| --- | --- | --- | --- |\n"
        + "".join(f"| {row['video']} |  |  |  |\n" for row in manifest["clips"])
        + "\n请写完成时间，以及此前是否见过这两段的真值或预期答案。\n",
        encoding="utf-8",
    )
    (truth / "mapping.json").write_text(json.dumps({"records": records}, indent=2), encoding="utf-8")
    archive = output / "flat_stack_reader_only.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path in sorted(observer.iterdir()):
            z.write(path, path.name)
    with zipfile.ZipFile(archive) as z:
        if any(z.read(path.name) != path.read_bytes() for path in observer.iterdir()):
            raise RuntimeError("observer archive bytes mismatch")
    return {"videos": len(records), "decoded_frames_each": SECONDS,
            "archive_sha256": sha256(archive),
            "terminal_success_by_condition": {r["condition"]: r["terminal"]["success"]
                                              for r in records}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output)))

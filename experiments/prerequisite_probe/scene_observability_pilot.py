"""Anonymous main-camera 1 FPS development pilots for an independent reader.

The observer_only directory contains the goal, four anonymous clips and media
hashes. Scene, condition, simulation state and outcomes stay in truth/.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np

from .flat_square_dev import FlatSquareSpec, INSTRUCTION
from .flat_square_operational_check import RetryIK, red_prep_spec
from .flat_square_route_challenge import (
    build_waypoint_keyframes,
    position,
    source_lid_two_stage_waypoints,
)
from .flat_square_scene import make_flat_env
from .probe import FPS, PandaIK, SIZE, snapshot_signature
from .produce import action_at, build_keyframes, ffmpeg_writer, sha256
from .source_lid_scene import make_source_lid_env
from .distractor_scenes import (
    make_flat_with_distractor, make_source_with_distractor, make_source_with_handle,
)


SPEC = FlatSquareSpec()
SECONDS = 15
CASES = (
    ("flat_square", "B+", "clip_0274.mp4"),
    ("source_lid", "N0", "clip_0459.mp4"),
    ("source_lid", "B+", "clip_0632.mp4"),
    ("flat_square", "N0", "clip_0816.mp4"),
)


def make_scene(kind, *, with_distractor=False, source_handle=False):
    if kind == "flat_square":
        return (make_flat_with_distractor if with_distractor else make_flat_env)("blocked")
    if kind == "source_lid":
        factory = (make_source_with_handle if source_handle else
                   (make_source_with_distractor if with_distractor else make_source_lid_env))
        return factory("blocked")
    raise ValueError(kind)


def keyframes_for(env, kind, condition, ik):
    q_home = env.unwrapped.agent.robot.get_qpos()[0, :7].cpu().numpy().astype(float)
    if condition == "N0":
        return [(0.0, q_home, 1.0), (SECONDS, q_home, 1.0)], []
    if kind == "flat_square":
        retry_ik = RetryIK(ik)
        keyframes, errors = build_keyframes(env, red_prep_spec(), retry_ik)
        return keyframes, errors
    return build_waypoint_keyframes(env, ik, source_lid_two_stage_waypoints())


def decoded_frame_hashes(video: Path):
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(video),
        "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1",
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    frame_bytes = SIZE[0] * SIZE[1] * 3
    if len(result.stdout) % frame_bytes:
        raise RuntimeError(f"incomplete decoded frame for {video}")
    return [hashlib.sha256(result.stdout[i:i + frame_bytes]).hexdigest()
            for i in range(0, len(result.stdout), frame_bytes)]


def record_one(env, initial, kind, condition, video: Path, ik):
    env.reset(seed=20261005)
    scene = env.unwrapped
    scene.set_state_dict(copy.deepcopy(initial))
    keyframes, errors = keyframes_for(env, kind, condition, ik)
    red_start_xyz = position(scene.red)
    blue_start_xyz = position(scene.blue)
    yellow_start_xyz = position(scene.yellow) if hasattr(scene, "yellow") else None
    writer = ffmpeg_writer(video, 1)
    sample_indices = []
    raw_frame_hashes = []
    try:
        for index in range(SECONDS * FPS):
            if index:
                env.step(action_at(index / FPS, keyframes))
            if index % FPS == 0:
                frame = np.ascontiguousarray(env.render().cpu().numpy()[0])
                if frame.shape != (SIZE[1], SIZE[0], 3):
                    raise RuntimeError(f"wrong frame shape: {frame.shape}")
                writer.stdin.write(frame.tobytes())
                sample_indices.append(index)
                raw_frame_hashes.append(hashlib.sha256(frame.tobytes()).hexdigest())
    finally:
        writer.stdin.close()
        stderr = writer.stderr.read().decode(errors="replace")
        rc = writer.wait()
        if rc:
            raise RuntimeError(f"ffmpeg exited {rc}: {stderr}")
    decoded = decoded_frame_hashes(video)
    if len(sample_indices) != SECONDS or len(decoded) != SECONDS:
        raise RuntimeError(f"expected 15 frames, got {len(sample_indices)}/{len(decoded)}")
    return {
        "scene_kind": kind,
        "condition": condition,
        "video": video.name,
        "initial_state_sha256": snapshot_signature(initial),
        "blue_start_xyz": blue_start_xyz,
        "red_start_xyz": red_start_xyz,
        "yellow_start_xyz": yellow_start_xyz,
        "blue_end_xyz": position(scene.blue),
        "red_end_xyz": position(scene.red),
        "yellow_end_xyz": position(scene.yellow) if hasattr(scene, "yellow") else None,
        "ik_errors": errors,
        "video_sha256": sha256(video),
        "sample_indices_30fps": sample_indices,
        "raw_rgb_sha256": raw_frame_hashes,
        "decoded_rgb_sha256": decoded,
    }


def run(output: Path, *, with_distractor=False, source_handle=False):
    if source_handle and not with_distractor:
        raise ValueError("source_handle requires with_distractor")
    observer = output / "observer_only"
    truth = output / "truth"
    observer.mkdir(parents=True, exist_ok=True)
    truth.mkdir(parents=True, exist_ok=True)
    ik = PandaIK()
    initial_states = {}
    for kind in ("flat_square", "source_lid"):
        env = make_scene(kind, with_distractor=with_distractor, source_handle=source_handle)
        try:
            env.reset(seed=20261005)
            initial_states[kind] = copy.deepcopy(env.unwrapped.get_state_dict())
        finally:
            env.close()
    records = []
    for kind, condition, name in CASES:
        env = make_scene(kind, with_distractor=with_distractor, source_handle=source_handle)
        try:
            records.append(record_one(env, initial_states[kind], kind, condition,
                                      observer / name, ik))
        finally:
            env.close()
    observer_manifest = {
        "instruction": INSTRUCTION,
        "protocol": ("scene_observability_pilot_v3_yellow_handle" if source_handle else
                     ("scene_observability_pilot_v2_yellow" if with_distractor else
                      "scene_observability_pilot_v1")),
        "video_format": {"duration_s": SECONDS, "fps": 1, "width": SIZE[0], "height": SIZE[1]},
        "clips": [{"video": item["video"], "video_sha256": item["video_sha256"],
                   "sample_indices_30fps": item["sample_indices_30fps"],
                   "decoded_rgb_sha256": item["decoded_rgb_sha256"]}
                  for item in sorted(records, key=lambda entry: entry["video"])],
    }
    (observer / "media_hashes.json").write_text(json.dumps(observer_manifest, indent=2), encoding="utf-8")
    (observer / "instruction.txt").write_text(INSTRUCTION + "\n", encoding="utf-8")
    packet = (
        "# 主视角准备视频独立审读\n\n"
        "只看同目录四段匿名视频和以下最终目标句。不要打开研究目录中的其他文件。"
        "每段均为 15 秒、1 FPS；可重复播放或裁剪同一视频。\n\n"
        f"> {INSTRUCTION}\n\n"
        "请分别对每个视频写：① 起始与结束时蓝块、红物、黄块、绿框在哪里；"
        "② 红物与蓝块到达绿框的关系是否清楚可见、途中是否变化；"
        "③ 哪些时刻或关系看不清，需要什么额外画面；④ 判断理由。"
        "不要猜条件代号、成功率或机器人后续动作。\n\n"
        "| 视频 | 起始/结束身份与位置 | 关系变化与理由 | 看不清处 |\n"
        "| --- | --- | --- | --- |\n"
        + "".join(f"| {entry['video']} |  |  |  |\n" for entry in observer_manifest["clips"])
        + "\n请写填写时间，以及此前是否见过这些视频的仿真真值、条件映射或预期答案。\n"
    )
    (observer / "reviewer_packet.md").write_text(packet, encoding="utf-8")
    (truth / "pilot_mapping.json").write_text(json.dumps({
        "protocol": observer_manifest["protocol"],
        "scene_spec": SPEC.protocol,
        "records": records,
    }, indent=2), encoding="utf-8")
    return {"videos": [entry["video"] for entry in observer_manifest["clips"]],
            "decoded_frames_each": SECONDS}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--with-distractor", action="store_true")
    parser.add_argument("--source-handle", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.output, with_distractor=args.with_distractor,
                         source_handle=args.source_handle)))

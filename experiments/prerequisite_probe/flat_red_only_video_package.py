"""No-yellow flat-square development routes and physical admission checks."""

from __future__ import annotations

import math
import argparse
import copy
import hashlib
import json
from pathlib import Path
import random

import numpy as np

from .flat_square_dev import FlatSquareSpec, INSTRUCTION, evaluate_terminal
from .flat_square_operational_check import RetryIK, red_prep_spec
from .flat_square_route_challenge import (
    build_waypoint_keyframes, direct_place_spec, position,
)
from .flat_square_scene import make_flat_env
from .probe import FPS, PandaIK, SIZE, snapshot_signature
from .produce import action_at, build_keyframes, ffmpeg_writer, sha256
from .scene_observability_pilot import decoded_frame_hashes
from .six_case_route_prototypes import flat_b0_return_waypoints


SPEC = FlatSquareSpec()
CONDITIONS = ("B+", "B0", "U0", "H-", "G+", "N0")
U0_RED_DEST_XY = (-0.14, 0.10)
PROTOCOL = "flat_red_only_development_v1"
SECONDS = 15


def branch_state(condition: str) -> str:
    if condition not in CONDITIONS:
        raise ValueError(condition)
    return "blocked" if condition in ("B+", "B0") else "open"


def _distance_xy(a, b) -> float:
    return math.dist(a[:2], b[:2])


def _red_blocks_target(pose) -> bool:
    return (_distance_xy(pose, (SPEC.target_x, SPEC.target_y)) <= 0.005
            and abs(pose[2] - SPEC.red_half) <= 0.003)


def _red_overlaps_target_projection(pose) -> bool:
    return (abs(pose[0] - SPEC.target_x) < SPEC.square_inner_half + SPEC.red_half
            and abs(pose[1] - SPEC.target_y) < SPEC.square_inner_half + SPEC.red_half)


def audit_condition(condition: str, start: dict, end: dict, terminal_success: bool,
                    red_path_positions: list) -> list[str]:
    """Check physical relations without using an anonymous video's filename."""
    if condition not in CONDITIONS:
        raise ValueError(condition)
    issues = []
    blocked_start = condition in ("B+", "B0")
    if _red_blocks_target(start["red"]) != blocked_start:
        issues.append("wrong_initial_red_relation")
    blocked_end = condition in ("B0", "H-")
    if _red_blocks_target(end["red"]) != blocked_end:
        issues.append("red_not_blocking_at_end" if blocked_end else "red_still_blocking_at_end")
    if bool(terminal_success) != (condition == "G+"):
        issues.append("goal_not_completed" if condition == "G+" else "unexpected_goal_completion")
    if condition != "G+" and math.dist(start["blue"], end["blue"]) > 0.005:
        issues.append("blue_moved_in_non_goal_condition")
    if condition == "U0":
        if _distance_xy(start["red"], end["red"]) < 0.08:
            issues.append("u0_red_not_moved")
        if any(_red_overlaps_target_projection(pose) for pose in red_path_positions):
            issues.append("u0_red_overlapped_target_during_route")
    if condition == "B0" and max((_distance_xy(start["red"], pose)
                                  for pose in red_path_positions), default=0) < 0.08:
        issues.append("insufficient_red_excursion")
    if condition in ("B+", "H-") and _distance_xy(start["red"], end["red"]) < 0.08:
        issues.append("red_not_moved_enough")
    if condition in ("G+", "N0") and _distance_xy(start["red"], end["red"]) > 0.005:
        issues.append("red_moved_unexpectedly")
    if condition == "N0" and math.dist(start["blue"], end["blue"]) > 0.005:
        issues.append("noop_moved_blue")
    return issues


def _route(env, condition: str, ik: PandaIK):
    if condition == "B+":
        return build_keyframes(env, red_prep_spec(), RetryIK(ik))
    if condition == "B0":
        return build_waypoint_keyframes(env, RetryIK(ik), flat_b0_return_waypoints())
    if condition == "U0":
        return build_keyframes(env, {
            "object": "red", "destination_xy": U0_RED_DEST_XY,
            "destination_z": SPEC.red_half, "end_time": 15,
        }, RetryIK(ik))
    if condition == "H-":
        return build_keyframes(env, {
            "object": "red", "destination_xy": (SPEC.target_x, SPEC.target_y),
            "destination_z": SPEC.red_half, "end_time": 15,
        }, RetryIK(ik))
    if condition == "G+":
        return build_keyframes(env, direct_place_spec(), RetryIK(ik))
    if condition == "N0":
        home = env.unwrapped.agent.robot.get_qpos()[0, :7].cpu().numpy().astype(float)
        return [(0.0, home, 1.0), (15.0, home, 1.0)], []
    raise ValueError(condition)


def probe_condition(condition: str) -> dict:
    """Run an unscored physical route check without making a Monitor video."""
    env = make_flat_env(branch_state(condition))
    try:
        env.reset(seed=20261005)
        scene = env.unwrapped
        start = {name: position(getattr(scene, name)) for name in ("blue", "red")}
        keyframes, ik_errors = _route(env, condition, PandaIK())
        trajectory = []
        for index in range(15 * FPS):
            if index:
                env.step(action_at(index / FPS, keyframes))
            trajectory.append({
                "step": index, "time_s": index / FPS,
                "blue_xyz": position(scene.blue), "red_xyz": position(scene.red),
                "tcp_xyz": position(scene.agent.tcp),
            })
        end = {name: position(getattr(scene, name)) for name in ("blue", "red")}
        terminal = evaluate_terminal(list(scene._terminal_window), SPEC)
        path = [row["red_xyz"] for row in trajectory]
        return {
            "condition": condition, "start": start, "end": end,
            "red_displacement_xy_m": _distance_xy(start["red"], end["red"]),
            "admission_issues": audit_condition(condition, start, end,
                                                terminal["success"], path),
            "terminal": terminal, "ik_errors": ik_errors,
            "trajectory": trajectory,
        }
    finally:
        env.close()


def _positions(scene):
    return {name: position(getattr(scene, name)) for name in ("blue", "red")}


def _record_one(condition: str, initial: dict, video: Path, ik: PandaIK) -> dict:
    env = make_flat_env(branch_state(condition))
    try:
        env.reset(seed=20261005)
        scene = env.unwrapped
        scene.set_state_dict(copy.deepcopy(initial))
        start = _positions(scene)
        keyframes, ik_errors = _route(env, condition, ik)
        trajectory = []
        sample_indices = []
        raw_hashes = []
        writer = ffmpeg_writer(video, 1)
        try:
            for index in range(SECONDS * FPS):
                if index:
                    env.step(action_at(index / FPS, keyframes))
                poses = _positions(scene)
                trajectory.append({
                    "step": index, "time_s": index / FPS,
                    "blue_xyz": poses["blue"], "red_xyz": poses["red"],
                    "tcp_xyz": position(scene.agent.tcp),
                })
                if index % FPS == 0:
                    frame = np.ascontiguousarray(env.render().cpu().numpy()[0])
                    if frame.shape != (SIZE[1], SIZE[0], 3):
                        raise RuntimeError(f"wrong frame shape: {frame.shape}")
                    writer.stdin.write(frame.tobytes())
                    sample_indices.append(index)
                    raw_hashes.append(hashlib.sha256(frame.tobytes()).hexdigest())
        finally:
            writer.stdin.close()
            stderr = writer.stderr.read().decode(errors="replace")
            rc = writer.wait()
            writer.stderr.close()
            if rc:
                raise RuntimeError(f"ffmpeg exited {rc}: {stderr}")
        decoded = decoded_frame_hashes(video)
        if len(sample_indices) != SECONDS or len(decoded) != SECONDS:
            raise RuntimeError(f"expected {SECONDS} decoded frames: {video}")
        end = _positions(scene)
        terminal = evaluate_terminal(list(scene._terminal_window), SPEC)
        red_path = [row["red_xyz"] for row in trajectory]
        return {
            "condition": condition, "video": video.name,
            "initial_state_sha256": snapshot_signature(initial),
            "start": start, "end": end, "terminal": terminal,
            "red_displacement_xy_m": _distance_xy(start["red"], end["red"]),
            "red_max_xy_excursion_m": max(_distance_xy(start["red"], pose)
                                          for pose in red_path),
            "admission_issues": audit_condition(condition, start, end,
                                                terminal["success"], red_path),
            "ik_errors": ik_errors, "sample_indices_30fps": sample_indices,
            "raw_rgb_sha256": raw_hashes, "decoded_rgb_sha256": decoded,
            "video_sha256": sha256(video), "trajectory": trajectory,
        }
    finally:
        env.close()


def run_candidate(output: Path) -> dict:
    """Generate a never-before-scored six-clip candidate; never overwrite one."""
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(output)
    candidate = output / "candidate_input"
    truth = output / "truth"
    candidate.mkdir(parents=True)
    truth.mkdir(parents=True)
    starts = {}
    for state in ("blocked", "open"):
        env = make_flat_env(state)
        try:
            env.reset(seed=20261005)
            starts[state] = copy.deepcopy(env.unwrapped.get_state_dict())
        finally:
            env.close()
    rng = random.Random(202610051)
    names = rng.sample(range(1000, 10000), len(CONDITIONS))
    rng.shuffle(names)
    records, failures = [], []
    ik = PandaIK()
    for condition, number in zip(CONDITIONS, names):
        video = candidate / f"clip_{number}.mp4"
        try:
            record = _record_one(condition, starts[branch_state(condition)], video, ik)
            records.append(record)
            if record["admission_issues"]:
                failures.append({"video": video.name, "condition": condition,
                                 "issues": record["admission_issues"]})
        except Exception as exc:
            failures.append({"video": video.name, "condition": condition,
                             "error": f"{type(exc).__name__}: {exc}"})
    (truth / "mapping_and_trajectories.json").write_text(json.dumps({
        "protocol": PROTOCOL, "goal_predicate": SPEC.protocol,
        "blocked_snapshot_sha256": snapshot_signature(starts["blocked"]),
        "open_snapshot_sha256": snapshot_signature(starts["open"]),
        "records": records, "failures": failures,
    }, indent=2), encoding="utf-8")
    if failures or len(records) != len(CONDITIONS):
        raise RuntimeError(f"{len(failures)} failed/admission-rejected clips; retained at {output}")
    manifest = {
        "protocol": PROTOCOL, "instruction": INSTRUCTION,
        "video_format": {"duration_s": SECONDS, "fps": 1,
                         "width": SIZE[0], "height": SIZE[1]},
        "clips": [{"video": row["video"], "video_sha256": row["video_sha256"],
                   "sample_indices_30fps": row["sample_indices_30fps"],
                   "decoded_rgb_sha256": row["decoded_rgb_sha256"]}
                  for row in sorted(records, key=lambda r: r["video"])],
    }
    (candidate / "media_hashes.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (candidate / "instruction.txt").write_text(manifest["instruction"] + "\n", encoding="utf-8")
    expected = {r["video"] for r in records} | {"instruction.txt", "media_hashes.json"}
    actual = {p.name for p in candidate.iterdir() if p.is_file()}
    if actual != expected:
        raise RuntimeError(f"candidate_input contains unexpected files: {actual ^ expected}")
    if any(key in (candidate / "media_hashes.json").read_text(encoding="utf-8")
           for key in ("condition", "terminal", "truth", "continuation", "old_score")):
        raise RuntimeError("candidate_input manifest leaked truth")
    return {"status": "candidate_pending_independent_review",
            "clips": len(records), "candidate_input": str(candidate), "truth": str(truth)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run_candidate(args.output)))

"""Audited 12-clip development package; only callable after final S2 review.

Simulator state, condition mapping, routes and continuation outcomes remain in
truth/. model_input/ contains only the shared goal, anonymous MP4s and media
hashes. This is development material, never a post-freeze blind test.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import random

import numpy as np

from .distractor_scenes import make_flat_with_distractor, make_source_with_handle
from .flat_square_dev import FlatSquareSpec, INSTRUCTION, evaluate_terminal
from .flat_square_route_challenge import position
from .probe import FPS, PandaIK, SIZE, snapshot_signature
from .produce import action_at, ffmpeg_writer, sha256
from .scene_observability_pilot import decoded_frame_hashes
from .six_case_route_prototypes import CONDITIONS, route


SPEC = FlatSquareSpec()
SECONDS = 15
S2_PROTOCOL = "scene_observability_pilot_v3_yellow_handle"
PROTOCOL = "prerequisite_six_development_v1"


def _distance_xy(a, b):
    return math.dist(a[:2], b[:2])


def _blocked(kind, pose, quat=None):
    if kind == "flat_square":
        return (_distance_xy(pose, (SPEC.target_x, SPEC.target_y)) <= 0.005
                and abs(pose[2] - SPEC.red_half) <= 0.003)
    upright = quat is None or math.dist(quat, (1.0, 0.0, 0.0, 0.0)) <= 0.05
    return (_distance_xy(pose, (-0.08, -0.07)) <= 0.003
            and abs(pose[2] - 0.062) <= 0.003 and upright)


def assess_condition(kind, condition, start, end, terminal_success,
                     red_excursion_m, red_quat=None):
    """Return physical/protocol violations, independent of file numbering."""
    if kind not in ("flat_square", "source_lid") or condition not in CONDITIONS:
        raise ValueError((kind, condition))
    issues = []
    starts_blocked = condition in ("B+", "B0")
    if _blocked(kind, start["red"]) != starts_blocked:
        issues.append("wrong_initial_red_relation")
    ends_blocked = condition in ("B0", "H-")
    if _blocked(kind, end["red"], red_quat) != ends_blocked:
        issues.append("red_not_blocking_at_end" if ends_blocked else "red_still_blocking_at_end")
    if (condition == "G+") != bool(terminal_success):
        issues.append("goal_not_completed" if condition == "G+" else "unexpected_goal_completion")
    if condition != "G+" and math.dist(start["blue"], end["blue"]) > 0.005:
        issues.append("blue_moved_in_non_goal_condition")
    yellow_move = _distance_xy(start["yellow"], end["yellow"])
    if condition == "U0":
        if yellow_move < 0.08:
            issues.append("yellow_not_moved")
    elif yellow_move > 0.005:
        issues.append("yellow_moved_unexpectedly")
    if condition == "B0" and red_excursion_m < 0.08:
        issues.append("insufficient_red_excursion")
    if condition == "B+" and _distance_xy(start["red"], end["red"]) < 0.08:
        issues.append("red_not_removed")
    if condition == "H-" and _distance_xy(start["red"], end["red"]) < 0.08:
        issues.append("red_not_added")
    if condition == "N0" and any(math.dist(start[name], end[name]) > 0.005
                                 for name in ("blue", "red", "yellow")):
        issues.append("noop_moved_object")
    return issues


def _factory(kind):
    return make_flat_with_distractor if kind == "flat_square" else make_source_with_handle


def _positions(scene):
    return {name: position(getattr(scene, name)) for name in ("blue", "red", "yellow")}


def _read_review_receipt(path: Path):
    receipt = json.loads(path.read_text(encoding="utf-8"))
    if receipt.get("status") != "passed" or receipt.get("protocol") != S2_PROTOCOL:
        raise RuntimeError("final main-camera S2 review has not passed")
    raw = Path(receipt["reader_raw_path"])
    if not raw.is_file() or sha256(raw) != receipt.get("reader_raw_sha256"):
        raise RuntimeError("sealed reader review missing or hash mismatch")
    return receipt


def _record_one(kind, condition, initial, video, ik):
    env = _factory(kind)("blocked" if condition in ("B+", "B0") else "open")
    try:
        env.reset(seed=20261005)
        scene = env.unwrapped
        scene.set_state_dict(copy.deepcopy(initial))
        start = _positions(scene)
        keyframes, ik_errors = route(env, kind, condition, ik, source_handle=(kind == "source_lid"))
        trajectory = []
        sample_indices = []
        raw_hashes = []
        writer = ffmpeg_writer(video, 1)
        try:
            for index in range(SECONDS * FPS):
                if index:
                    env.step(action_at(index / FPS, keyframes))
                positions = _positions(scene)
                trajectory.append({
                    "step": index, "time_s": index / FPS,
                    **{f"{name}_xyz": xyz for name, xyz in positions.items()},
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
            if rc:
                raise RuntimeError(f"ffmpeg exited {rc}: {stderr}")
        decoded = decoded_frame_hashes(video)
        if len(sample_indices) != SECONDS or len(decoded) != SECONDS:
            raise RuntimeError(f"expected {SECONDS} decoded frames: {video}")
        end = _positions(scene)
        red_quat = scene.red.pose.q[0].cpu().numpy().tolist()
        terminal = evaluate_terminal(list(scene._terminal_window), SPEC)
        excursion = max(_distance_xy(start["red"], row["red_xyz"]) for row in trajectory)
        issues = assess_condition(kind, condition, start, end, terminal["success"],
                                  excursion, red_quat)
        return {
            "scene_kind": kind, "condition": condition, "video": video.name,
            "initial_state_sha256": snapshot_signature(initial),
            "start": start, "end": end, "red_end_quaternion_wxyz": red_quat,
            "red_max_xy_excursion_m": excursion, "terminal": terminal,
            "admission_issues": issues, "ik_errors": ik_errors,
            "sample_indices_30fps": sample_indices,
            "raw_rgb_sha256": raw_hashes, "decoded_rgb_sha256": decoded,
            "video_sha256": sha256(video), "trajectory": trajectory,
        }
    finally:
        env.close()


def run(output: Path, review_receipt: Path):
    receipt = _read_review_receipt(review_receipt)
    model_input = output / "model_input"
    truth = output / "truth"
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refuse to overwrite a previous generation attempt: {output}")
    model_input.mkdir(parents=True)
    truth.mkdir(parents=True)
    starts = {}
    for kind in ("flat_square", "source_lid"):
        for state in ("blocked", "open"):
            env = _factory(kind)(state)
            try:
                env.reset(seed=20261005)
                starts[(kind, state)] = copy.deepcopy(env.unwrapped.get_state_dict())
            finally:
                env.close()
    pairs = [(kind, condition) for kind in ("flat_square", "source_lid")
             for condition in CONDITIONS]
    rng = random.Random(20261005)
    numbers = rng.sample(range(1000, 10000), len(pairs))
    rng.shuffle(numbers)
    records = []
    failures = []
    ik = PandaIK()
    for (kind, condition), number in zip(pairs, numbers):
        video = model_input / f"clip_{number}.mp4"
        state = "blocked" if condition in ("B+", "B0") else "open"
        try:
            record = _record_one(kind, condition, starts[(kind, state)], video, ik)
            records.append(record)
            if record["admission_issues"]:
                failures.append({"video": video.name, "condition": condition,
                                 "scene_kind": kind, "issues": record["admission_issues"]})
        except Exception as exc:
            failures.append({"video": video.name, "condition": condition,
                             "scene_kind": kind, "error": f"{type(exc).__name__}: {exc}"})
    (truth / "mapping_and_trajectories.json").write_text(json.dumps({
        "protocol": PROTOCOL, "goal_predicate": SPEC.protocol,
        "s2_review_receipt": str(review_receipt),
        "s2_review_raw_sha256": receipt["reader_raw_sha256"],
        "records": records, "failures": failures,
    }, indent=2), encoding="utf-8")
    (truth / "generation_failures.json").write_text(json.dumps(failures, indent=2), encoding="utf-8")
    if failures or len(records) != 12:
        raise RuntimeError(f"{len(failures)} failed/admission-rejected clips; attempt retained at {output}")
    manifest = {
        "protocol": PROTOCOL, "instruction": INSTRUCTION,
        "video_format": {"duration_s": SECONDS, "fps": 1,
                         "width": SIZE[0], "height": SIZE[1]},
        "clips": [{"video": row["video"], "video_sha256": row["video_sha256"],
                   "sample_indices_30fps": row["sample_indices_30fps"],
                   "decoded_rgb_sha256": row["decoded_rgb_sha256"]}
                  for row in sorted(records, key=lambda r: r["video"])],
    }
    (model_input / "media_hashes.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (model_input / "instruction.txt").write_text(INSTRUCTION + "\n", encoding="utf-8")
    actual = {p.name for p in model_input.iterdir() if p.is_file()}
    expected = {r["video"] for r in records} | {"instruction.txt", "media_hashes.json"}
    if actual != expected:
        raise RuntimeError("model_input contains unexpected files")
    if any(key in (model_input / "media_hashes.json").read_text(encoding="utf-8")
           for key in ("scene_kind", "condition", "terminal", "truth", "continuation")):
        raise RuntimeError("model_input leaked truth fields")
    return {"status": "generated_development_package", "clips": len(records),
            "model_input": str(model_input), "truth": str(truth)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--s2-review-receipt", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.s2_review_receipt)))

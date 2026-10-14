"""Record fixed-camera ManiSkill videos and isolated physical truth."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import time
from pathlib import Path

import numpy as np

from .probe import FPS, INSTRUCTION, PandaIK, SCENE_LAYOUTS, SECONDS, SIZE, make_env, sample_indices, snapshot_signature, _jsonable


CASES = {"B+": "0001", "B0": "0002", "U0": "0003", "H-": "0004", "G+": "0005", "N0": "0006"}
OPEN, CLOSED = 1.0, -1.0


def script_for(condition, scene="cell"):
    if condition not in CASES:
        raise ValueError(condition)
    if scene in ("tray_crossbar", "source_bridge"):
        tx, ty = SCENE_LAYOUTS[scene]["tray"]
        bx, by = SCENE_LAYOUTS[scene]["blue"]
        if scene == "tray_crossbar":
            blocked_xy, blocked_z = (tx, ty), .066
        else:
            blocked_xy, blocked_z = (bx, by), .105
        destinations = {"B+": (.015, .17), "B0": (blocked_xy[0] + .005, blocked_xy[1]),
                        "U0": (.015, -.17), "H-": blocked_xy,
                        "G+": (tx, ty), "N0": None}
        return {"object": "blue" if condition == "G+" else (None if condition == "N0" else "red"),
                "red_start": "blocked" if condition in ("B+", "B0") else "open",
                "destination_xy": destinations[condition],
                "destination_z": blocked_z if condition in ("B0", "H-") else (.038 if condition == "G+" else .015),
                "end_time": 12}
    if scene == "source_stack":
        bx, by = SCENE_LAYOUTS[scene]["blue"]
        destinations = {"B+": (.015, .17), "B0": (bx + .005, by),
                        "U0": (.16, -.15), "H-": (bx, by),
                        "G+": SCENE_LAYOUTS[scene]["tray"], "N0": None}
        return {"object": "blue" if condition == "G+" else (None if condition == "N0" else "red"),
                "red_start": "blocked" if condition in ("B+", "B0") else "open",
                "destination_xy": destinations[condition],
                "destination_z": .064 if condition in ("B0", "H-") else (.038 if condition == "G+" else .018),
                "end_time": 12}
    if scene == "offset_cell":
        tx, ty = SCENE_LAYOUTS[scene]["tray"]
        destinations = {"B+": (.015, .17), "B0": (tx + .005, ty + .003),
                        "U0": (.015, -.17), "H-": (tx, ty), "G+": (tx, ty),
                        "N0": None}
        return {"object": "blue" if condition == "G+" else (None if condition == "N0" else "red"),
                "red_start": "blocked" if condition in ("B+", "B0") else "open",
                "destination_xy": destinations[condition], "end_time": 12}
    if scene == "pickup_gate":
        destinations = {"B+": (.12, .16), "B0": (-.09, .040),
                        "U0": (.20, .18), "H-": (-.09, .040),
                        "G+": SCENE_LAYOUTS[scene]["tray"], "N0": None}
        return {"object": "blue" if condition == "G+" else (None if condition == "N0" else "red"),
                "red_start": "blocked" if condition in ("B+", "B0") else "open",
                "destination_xy": destinations[condition], "end_time": 12}
    if scene == "pickup_gate_opposite":
        destinations = {"B+": (.12, .16), "B0": (-.09, .185),
                        "U0": (.20, .18), "H-": (-.09, .185),
                        "G+": SCENE_LAYOUTS[scene]["tray"], "N0": None}
        return {"object": "blue" if condition == "G+" else (None if condition == "N0" else "red"),
                "red_start": "blocked" if condition in ("B+", "B0") else "open",
                "destination_xy": destinations[condition], "end_time": 12}
    if scene == "mirror_cell":
        tx, ty = SCENE_LAYOUTS[scene]["tray"]
        destinations = {"B+": (.10, -.15), "B0": (tx + .005, ty - .003),
                        "U0": (.0, -.18), "H-": (tx, ty),
                        "G+": (tx, ty), "N0": None}
        return {"object": "blue" if condition == "G+" else (None if condition == "N0" else "red"),
                "red_start": "blocked" if condition in ("B+", "B0") else "open",
                "destination_xy": destinations[condition], "end_time": 12}
    if scene == "left_cell":
        tx, ty = SCENE_LAYOUTS[scene]["tray"]
        destinations = {"B+": (.15, -.17), "B0": (tx + .002, ty + .002),
                        "U0": (.19, -.02), "H-": (tx, ty),
                        "G+": (tx, ty), "N0": None}
        return {"object": "blue" if condition == "G+" else (None if condition == "N0" else "red"),
                "red_start": "blocked" if condition in ("B+", "B0") else "open",
                "destination_xy": destinations[condition], "end_time": 12}
    if scene == "pickup_gate_shifted":
        destinations = {"B+": (.16, .16), "B0": (-.03, .04),
                        "U0": (.06, .18), "H-": (-.03, .04),
                        "G+": SCENE_LAYOUTS[scene]["tray"], "N0": None}
        return {"object": "blue" if condition == "G+" else (None if condition == "N0" else "red"),
                "red_start": "blocked" if condition in ("B+", "B0") else "open",
                "destination_xy": destinations[condition], "end_time": 12}
    if scene == "rear_cell":
        tx, ty = SCENE_LAYOUTS[scene]["tray"]
        destinations = {"B+": (.04, .18), "B0": (tx + .003, ty + .002),
                        "U0": (.04, -.16), "H-": (tx, ty),
                        "G+": (tx, ty), "N0": None}
        return {"object": "blue" if condition == "G+" else (None if condition == "N0" else "red"),
                "red_start": "blocked" if condition in ("B+", "B0") else "open",
                "destination_xy": destinations[condition], "end_time": 12}
    starts_blocked = condition in ("B+", "B0")
    if condition == "B+":
        destination = (.12, .15)
    elif condition == "B0":
        destination = (.125, -.117)
    elif condition == "U0":
        destination = (.20, .18)
    elif condition == "H-":
        destination = (.12, -.12)
    elif condition == "G+":
        destination = (.12, -.12)
    else:
        destination = None
    return {
        "object": "blue" if condition == "G+" else (None if condition == "N0" else "red"),
        "red_start": "blocked" if starts_blocked else "open",
        "destination_xy": destination,
        "end_time": 12,
    }


def actor_pos(actor):
    return actor.pose.p[0].detach().cpu().numpy().astype(float)


def build_keyframes(env, spec, ik):
    q_home = env.unwrapped.agent.robot.get_qpos()[0, :7].cpu().numpy().astype(float)
    if spec["object"] is None:
        return [(0, q_home, OPEN), (SECONDS, q_home, OPEN)], []
    actor = getattr(env.unwrapped, spec["object"])
    start = actor_pos(actor)
    dx, dy = spec["destination_xy"]
    dest_z = spec.get("destination_z", .048 if (dx, dy) == tuple(SCENE_LAYOUTS.get(env.unwrapped.scene_kind, SCENE_LAYOUTS["cell"])["tray"]) and spec["object"] == "red" else
              .038 if spec["object"] == "blue" else .034)
    grasp_z = float(start[2] - .004)
    drop_z = float(dest_z - .004)
    path = [
        (2.0, None, OPEN),
        (3.00, (start[0], start[1], .19), OPEN),
        (4.25, (start[0], start[1], grasp_z), OPEN),
        (5.25, (start[0], start[1], grasp_z), OPEN),
        (5.75, (start[0], start[1], grasp_z), CLOSED),
        (6.50, (start[0], start[1], .20), CLOSED),
        (8.00, (dx, dy, .20), CLOSED),
        (9.00, (dx, dy, drop_z), CLOSED),
        (9.50, (dx, dy, drop_z), OPEN),
        (10.50, (dx, dy, .20), OPEN),
        (12.0, None, OPEN),
        (15.0, None, OPEN),
    ]
    keyframes = [(0.0, q_home, OPEN)]
    errors = []
    last = q_home.copy()
    for t, xyz, gripper in path:
        if xyz is None:
            q = q_home.copy()
        elif keyframes[-1][0] == t and np.allclose(keyframes[-1][1], last):
            q = last.copy()
        else:
            q, error = ik.solve(np.asarray(xyz), last)
            errors.append({"time": t, "xyz": list(map(float, xyz)), "metres": error})
            if error > .025:
                raise RuntimeError(f"IK failed at t={t}: {xyz}, error={error:.3f} m")
        keyframes.append((t, q, gripper))
        last = q
    return keyframes, errors


def action_at(t, keyframes):
    for i in range(1, len(keyframes)):
        t0, q0, g0 = keyframes[i - 1]
        t1, q1, g1 = keyframes[i]
        if t <= t1:
            a = (t - t0) / (t1 - t0)
            return np.r_[q0 + a * (q1 - q0), g0 + a * (g1 - g0)].astype(np.float32)
    return np.r_[keyframes[-1][1], keyframes[-1][2]].astype(np.float32)


def ffmpeg_writer(path, fps):
    return subprocess.Popen(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
         "-pixel_format", "rgb24", "-video_size", f"{SIZE[0]}x{SIZE[1]}", "-framerate", str(fps),
         "-i", "pipe:0", "-c:v", "libx264", "-preset", "fast", "-crf", "18",
         "-pix_fmt", "yuv420p", str(path)],
        stdin=subprocess.PIPE, stderr=subprocess.PIPE,
    )


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(data)
    return digest.hexdigest()


def record_case(env, condition, output: Path, snapshot, *, render=True, ik=None):
    spec = script_for(condition, env.unwrapped.scene_kind)
    env.reset(seed=20261004)
    env.unwrapped.set_state_dict(copy.deepcopy(snapshot))
    pre_hash = snapshot_signature(env.unwrapped.get_state_dict())
    ik = ik or PandaIK()
    keyframes, ik_errors = build_keyframes(env, spec, ik)
    blue_pre, red_pre = actor_pos(env.unwrapped.blue), actor_pos(env.unwrapped.red)
    raw = score = None
    output.mkdir(parents=True, exist_ok=True)
    if render:
        raw = ffmpeg_writer(output / "raw" / f"{CASES[condition]}.mp4", FPS)
        score = ffmpeg_writer(output / "model_input" / f"{CASES[condition]}.mp4", 1)
    positions = []
    started = time.time()
    try:
        for index in range(FPS * SECONDS):
            if index:
                env.step(action_at(index / FPS, keyframes))
            if index % FPS == 0 or index == FPS * SECONDS - 1:
                positions.append({
                    "frame": index, "blue": actor_pos(env.unwrapped.blue).tolist(),
                    "red": actor_pos(env.unwrapped.red).tolist(),
                    "tcp": actor_pos(env.unwrapped.agent.tcp).tolist(),
                    "grasp_red": bool(env.unwrapped.agent.is_grasping(env.unwrapped.red)[0]),
                    "grasp_blue": bool(env.unwrapped.agent.is_grasping(env.unwrapped.blue)[0]),
                })
            if render:
                frame = np.ascontiguousarray(env.render().cpu().numpy()[0])
                raw.stdin.write(frame.tobytes())
                if index in sample_indices():
                    score.stdin.write(frame.tobytes())
    finally:
        for process in (raw, score):
            if process:
                process.stdin.close()
                stderr = process.stderr.read().decode(errors="replace")
                rc = process.wait()
                if rc:
                    raise RuntimeError(f"ffmpeg exited {rc}: {stderr}")
    result = {
        "case": condition, "id": CASES[condition], "instruction": INSTRUCTION,
        "scene": env.unwrapped.scene_kind, "pre_state_sha256": pre_hash,
        "red_start": spec["red_start"], "blue_pre": blue_pre.tolist(), "red_pre": red_pre.tolist(),
        "blue_post": actor_pos(env.unwrapped.blue).tolist(), "red_post": actor_pos(env.unwrapped.red).tolist(),
        "success": bool(env.unwrapped.evaluate()["success"][0]),
        "sample_frame_indices": sample_indices(), "ik_errors": ik_errors,
        "positions": positions, "elapsed_seconds": time.time() - started,
    }
    if render:
        result["raw_sha256"] = sha256(output / "raw" / f"{CASES[condition]}.mp4")
        result["model_video_sha256"] = sha256(output / "model_input" / f"{CASES[condition]}.mp4")
    return result


def run_blue_continuation(env, snapshot, ik, seed):
    """Frozen blue-only pick/place controller with paired millimetre perturbation."""
    import sapien

    env.reset(seed=20261004)
    env.unwrapped.set_state_dict(copy.deepcopy(snapshot))
    rng = np.random.default_rng(seed)
    offset = rng.uniform(-.0015, .0015, size=2)
    pos = actor_pos(env.unwrapped.blue)
    pos[:2] += offset
    env.unwrapped.blue.set_pose(sapien.Pose(p=pos))
    red_pre = actor_pos(env.unwrapped.red)
    keyframes, errors = build_keyframes(env, script_for("G+", env.unwrapped.scene_kind), ik)
    for index in range(1, FPS * SECONDS):
        env.step(action_at(index / FPS, keyframes))
    red_post = actor_pos(env.unwrapped.red)
    return {
        "seed": seed, "blue_xy_offset": offset.tolist(),
        "success": bool(env.unwrapped.evaluate()["success"][0]),
        "blue_post": actor_pos(env.unwrapped.blue).tolist(),
        "red_post": red_post.tolist(),
        "red_motion_metres": float(np.linalg.norm(red_post - red_pre)),
        "ik_max_error_metres": max(x["metres"] for x in errors),
    }


def run_all(output: Path, continuation_seeds=range(20), scene="cell"):
    for name in ("raw", "model_input", "truth"):
        (output / name).mkdir(parents=True, exist_ok=True)
    ik = PandaIK()
    results = {}
    oracle = []
    for red_start, cases in (("blocked", ("B+", "B0")),
                             ("open", ("U0", "H-", "G+", "N0"))):
        env = make_env(scene, red_start)
        try:
            env.reset(seed=20261004)
            initial = copy.deepcopy(env.unwrapped.get_state_dict())
            (output / "truth" / f"initial_{red_start}.json").write_text(
                json.dumps(_jsonable(initial)), encoding="utf-8")
            posts = {}
            for condition in cases:
                result = record_case(env, condition, output, initial, ik=ik)
                results[condition] = result
                posts[condition] = copy.deepcopy(env.unwrapped.get_state_dict())
                (output / "truth" / f"post_{CASES[condition]}.json").write_text(
                    json.dumps(_jsonable(posts[condition])), encoding="utf-8")
                (output / "truth" / f"{CASES[condition]}.json").write_text(
                    json.dumps(_jsonable(result), indent=2), encoding="utf-8")
                print(f"RECORDED {condition} {CASES[condition]} {result['model_video_sha256'][:12]}", flush=True)
            if red_start == "blocked":
                check_cases = ("B+", "B0")
            else:
                check_cases = ("U0", "H-")
            # The counterfactual branch holds the identical initial state for the
            # same 15 seconds before starting the blue-only continuation.
            record_case(env, "N0", output, initial, render=False, ik=ik)
            control_after_noop = copy.deepcopy(env.unwrapped.get_state_dict())
            (output / "truth" / f"control_after_noop_{red_start}.json").write_text(
                json.dumps(_jsonable(control_after_noop)), encoding="utf-8")
            baseline = [run_blue_continuation(env, control_after_noop, ik, seed) for seed in continuation_seeds]
            baseline_success = [entry["success"] for entry in baseline]
            for condition in check_cases:
                after = [run_blue_continuation(env, posts[condition], ik, seed) for seed in continuation_seeds]
                post_success = [entry["success"] for entry in after]
                record = {
                    "case": condition, "id": CASES[condition],
                    "continuation_policy": "blue_only_joint_ik_v1", "horizon_seconds": SECONDS,
                    "preparation_or_noop_seconds": SECONDS, "total_budget_seconds": 2 * SECONDS,
                    "control_success_by_seed": baseline_success,
                    "action_success_by_seed": post_success,
                    "q_control": float(np.mean(baseline_success)),
                    "q_action": float(np.mean(post_success)),
                    "C": float(np.mean(post_success) - np.mean(baseline_success)),
                    "control_details": baseline, "action_details": after,
                }
                oracle.append(record)
                print(f"ORACLE {condition} q0={record['q_control']:.2f} q1={record['q_action']:.2f}", flush=True)
        finally:
            env.close()
    (output / "truth" / "oracle_checks.jsonl").write_text(
        "".join(json.dumps(_jsonable(record)) + "\n" for record in oracle), encoding="utf-8")
    (output / "model_input" / "manifest.jsonl").write_text(
        "".join(json.dumps({
            "video": f"{CASES[condition]}.mp4", "instruction": INSTRUCTION,
            "sha256": results[condition]["model_video_sha256"],
            "frame_indices_from_30fps": sample_indices(), "fps": 1,
        }) + "\n" for condition in CASES), encoding="utf-8")
    (output / "truth" / "scene_decision.json").write_text(json.dumps({
        "chosen": scene, "decision_before_model_output": True,
    }, indent=2), encoding="utf-8")
    return results, oracle


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=CASES, default="B+")
    parser.add_argument("--output", type=Path, default=Path("experiments/prerequisite_probe/artifacts"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--scene", choices=tuple(SCENE_LAYOUTS), default="cell")
    args = parser.parse_args()
    if args.all:
        run_all(args.output, scene=args.scene)
        return
    for name in ("raw", "model_input", "truth"):
        (args.output / name).mkdir(parents=True, exist_ok=True)
    env = make_env(args.scene, script_for(args.case, args.scene)["red_start"])
    try:
        env.reset(seed=20261004)
        snapshot = copy.deepcopy(env.unwrapped.get_state_dict())
        result = record_case(env, args.case, args.output, snapshot, render=not args.dry_run)
        path = args.output / "truth" / f"{CASES[args.case]}.json"
        path.write_text(json.dumps(_jsonable(result), indent=2), encoding="utf-8")
        print(json.dumps({key: result[key] for key in ("case", "pre_state_sha256", "blue_post", "red_post", "success", "elapsed_seconds")}, indent=2))
    finally:
        env.close()


if __name__ == "__main__":
    main()

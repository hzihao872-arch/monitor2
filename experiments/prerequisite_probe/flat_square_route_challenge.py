"""Development-only blue pick/place route against the flat-square blocker.

This runs one unscored controller path from each new-scene initial state. The
blocked path commands no red-only preparation; any red motion is incidental to
the blue placement. Neither case is a Monitor input or a necessity proof.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from mani_skill.utils import sapien_utils

from .flat_square_dev import FlatSquareSpec, INSTRUCTION, evaluate_terminal
from .flat_square_scene import make_flat_env
from .probe import FPS, PandaIK, snapshot_signature
from .produce import action_at, build_keyframes


SPEC = FlatSquareSpec()


def direct_place_spec():
    """Blue-only path; the red cube is never directly commanded."""
    return {
        "object": "blue",
        "destination_xy": (SPEC.target_x, SPEC.target_y),
        "destination_z": SPEC.blue_half + 0.015,
        "red_start": "blocked",
        "end_time": 15,
    }


def source_direct_spec():
    """Open-source pick/drop calibration; goal geometry and predicate stay fixed."""
    result = direct_place_spec()
    result["destination_xy"] = (SPEC.target_x + 0.01, SPEC.target_y)
    return result


def lateral_sweep_waypoints():
    """Grasp blue, enter low from the left, and sweep across the red cube."""
    sx, sy = (-0.13, -0.13)
    tx, ty = SPEC.target_x, SPEC.target_y
    return [
        (2.0, None, 1.0),
        (3.0, (sx, sy, 0.19), 1.0),
        (4.25, (sx, sy, SPEC.blue_half - 0.004), 1.0),
        (5.25, (sx, sy, SPEC.blue_half - 0.004), 1.0),
        (5.75, (sx, sy, SPEC.blue_half - 0.004), -1.0),
        (6.5, (sx, sy, 0.20), -1.0),
        (8.0, (tx - 0.06, ty, 0.20), -1.0),
        (9.0, (tx - 0.06, ty, SPEC.blue_half - 0.004), -1.0),
        (10.5, (tx, ty, SPEC.blue_half - 0.004), -1.0),
        (11.0, (tx, ty, SPEC.blue_half - 0.004), 1.0),
        (12.0, (tx, ty, 0.20), 1.0),
        (13.0, None, 1.0),
        (15.0, None, 1.0),
    ]


def source_lid_push_waypoints():
    """Open gripper sweeps the red lid away from the source opening."""
    return [
        (2.0, None, 1.0),
        (3.0, (-0.18, -0.07, 0.20), 1.0),
        (4.0, (-0.18, -0.07, 0.075), 1.0),
        (8.0, (0.12, -0.07, 0.075), 1.0),
        (9.0, (0.12, -0.07, 0.20), 1.0),
        (12.0, None, 1.0),
        (15.0, None, 1.0),
    ]


def source_lid_two_stage_waypoints():
    """Push the lid off the walls, then sweep its fallen body away on the table."""
    return [
        (1.5, None, 1.0),
        (2.3, (-0.18, -0.07, 0.20), 1.0),
        (3.0, (-0.18, -0.07, 0.075), 1.0),
        (5.5, (0.12, -0.07, 0.075), 1.0),
        (6.2, (0.12, -0.07, 0.20), 1.0),
        (7.0, (0.05, -0.17, 0.20), 1.0),
        (8.0, (0.05, -0.17, 0.021), 1.0),
        (10.5, (0.05, 0.08, 0.021), 1.0),
        (11.5, (0.05, 0.08, 0.20), 1.0),
        (13.0, None, 1.0),
        (15.0, None, 1.0),
    ]


def source_fixed_blue_waypoints():
    """Blue continuation with a fixed source center across paired offsets."""
    sx, sy = (-0.08, -0.07)
    tx, ty = (SPEC.target_x + 0.01, SPEC.target_y)
    return [
        (2.0, None, 1.0),
        (3.0, (sx, sy, 0.19), 1.0),
        (4.25, (sx, sy, SPEC.blue_half - 0.004), 1.0),
        (5.25, (sx, sy, SPEC.blue_half - 0.004), 1.0),
        (5.75, (sx, sy, SPEC.blue_half - 0.004), -1.0),
        (6.5, (sx, sy, 0.20), -1.0),
        (8.0, (tx, ty, 0.20), -1.0),
        (9.0, (tx, ty, SPEC.blue_half + 0.011), -1.0),
        (9.5, (tx, ty, SPEC.blue_half + 0.011), 1.0),
        (10.5, (tx, ty, 0.20), 1.0),
        (12.0, None, 1.0),
        (15.0, None, 1.0),
    ]


def build_waypoint_keyframes(env, ik: PandaIK, waypoints):
    q_home = env.unwrapped.agent.robot.get_qpos()[0, :7].cpu().numpy().astype(float)
    keyframes = [(0.0, q_home, 1.0)]
    errors = []
    last = q_home
    for t, xyz, gripper in waypoints:
        if xyz is None:
            q = q_home.copy()
        else:
            q, error = ik.solve(np.asarray(xyz), last)
            errors.append({"time": t, "xyz": list(xyz), "metres": error})
            if error > 0.025:
                raise RuntimeError(f"IK failed at t={t}: {xyz}, error={error:.3f} m")
        keyframes.append((t, q, gripper))
        last = q
    return keyframes, errors


def position(actor):
    return actor.pose.p[0].detach().cpu().numpy().astype(float).tolist()


def run_one(red_start: str, ik: PandaIK, route: str, scene_kind: str):
    if scene_kind == "flat_square":
        env = make_flat_env(red_start)
    elif scene_kind == "source_lid":
        from .source_lid_scene import make_source_lid_env
        env = make_source_lid_env(red_start)
    else:
        raise ValueError(scene_kind)
    try:
        env.reset(seed=20261005)
        scene = env.unwrapped
        initial_state_sha256 = snapshot_signature(scene.get_state_dict())
        blue_start, red_start_xyz = position(scene.blue), position(scene.red)
        if route == "direct":
            keyframes, ik_errors = build_keyframes(env, direct_place_spec(), ik)
        elif route == "source_direct" and scene_kind == "source_lid":
            keyframes, ik_errors = build_keyframes(env, source_direct_spec(), ik)
        elif route == "lateral_sweep":
            keyframes, ik_errors = build_waypoint_keyframes(env, ik, lateral_sweep_waypoints())
        elif route == "source_lid_push" and scene_kind == "source_lid":
            keyframes, ik_errors = build_waypoint_keyframes(env, ik, source_lid_push_waypoints())
        elif route == "source_lid_two_stage" and scene_kind == "source_lid":
            keyframes, ik_errors = build_waypoint_keyframes(env, ik, source_lid_two_stage_waypoints())
        else:
            raise ValueError(route)
        blue_body = scene.blue._bodies[0].entity
        red_body = scene.red._bodies[0].entity
        trajectory = []
        max_blue_red_impulse = 0.0
        for index in range(15 * FPS):
            if index:
                env.step(action_at(index / FPS, keyframes))
            impulse = sapien_utils.get_pairwise_contact_impulse(
                scene.scene.get_contacts(), blue_body, red_body
            )
            impulse_norm = float(np.linalg.norm(impulse))
            max_blue_red_impulse = max(max_blue_red_impulse, impulse_norm)
            trajectory.append({
                "step": index,
                "time_s": index / FPS,
                "blue_xyz": position(scene.blue),
                "red_xyz": position(scene.red),
                "tcp_xyz": position(scene.agent.tcp),
                "blue_red_impulse_norm": impulse_norm,
            })
        terminal = evaluate_terminal(list(scene._terminal_window), SPEC)
        red_end = position(scene.red)
        return {
            "red_start": red_start,
            "scene_kind": scene_kind,
            "protocol": SPEC.protocol,
            "instruction": INSTRUCTION,
            "route": route,
            "initial_state_sha256": initial_state_sha256,
            "blue_start_xyz": blue_start,
            "red_start_xyz": red_start_xyz,
            "blue_end_xyz": position(scene.blue),
            "red_end_xyz": red_end,
            "red_displacement_m": float(np.linalg.norm(np.asarray(red_end) - np.asarray(red_start_xyz))),
            "max_blue_red_impulse_norm": max_blue_red_impulse,
            "ik_errors": ik_errors,
            "keyframes": [
                {"time_s": t, "joints": q.tolist(), "gripper_command": g}
                for t, q, g in keyframes
            ],
            "terminal": terminal,
            "trajectory": trajectory,
        }
    finally:
        env.close()


def run(output: Path, route: str, scene_kind: str):
    ik = PandaIK()
    records = {}
    for red_start in ("blocked", "open"):
        try:
            records[red_start] = run_one(red_start, ik, route, scene_kind)
        except Exception as exc:
            records[red_start] = {"error": f"{type(exc).__name__}: {exc}"}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return {
        key: {"terminal": value.get("terminal"),
              "red_displacement_m": value.get("red_displacement_m"),
              "error": value.get("error")}
        for key, value in records.items()
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--route", choices=("direct", "lateral_sweep", "source_direct", "source_lid_push", "source_lid_two_stage"), default="direct")
    parser.add_argument("--scene", choices=("flat_square", "source_lid"), default="flat_square")
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.route, args.scene)))

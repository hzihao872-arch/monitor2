"""Development-only route probes for the final yellow-object scene variants.

These records contain condition names and simulator truth. They are never
written to an observer or Monitor input directory.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .distractor_scenes import (
    YELLOW_DEST_XY, YELLOW_HALF, make_flat_with_distractor,
    make_source_with_distractor, make_source_with_handle,
)
from .flat_square_dev import FlatSquareSpec, evaluate_terminal
from .flat_square_operational_check import RetryIK, red_prep_spec
from .flat_square_route_challenge import (
    build_waypoint_keyframes, direct_place_spec, position,
    source_fixed_blue_waypoints, source_lid_two_stage_waypoints,
)
from .probe import FPS, PandaIK
from .produce import action_at, build_keyframes
from .source_lid_scene import (
    SOURCE_BLUE_XY, LID_BLOCKED_Z, LID_HANDLE_LOCAL_XYZ, LID_OPEN_XY,
)
from .source_lid_reblock_search import handle_reblock_waypoints


SPEC = FlatSquareSpec()
CONDITIONS = ("B+", "B0", "U0", "H-", "G+", "N0")


def flat_b0_return_waypoints():
    """Carry red away and return it, preserving the final blocked relation."""
    x, y = SPEC.target_x, SPEC.target_y
    z = SPEC.red_half - 0.004
    return [
        (1.5, None, 1.0), (2.5, (x, y, 0.19), 1.0),
        (3.5, (x, y, z), 1.0), (4.0, (x, y, z), -1.0),
        (5.0, (x, y, 0.20), -1.0),
        (7.0, (0.02, 0.18, 0.20), -1.0),
        (8.0, (0.02, 0.18, 0.20), -1.0),
        (9.5, (x, y, 0.20), -1.0),
        (10.5, (x, y, z), -1.0),
        (11.0, (x, y, z), 1.0),
        (12.0, (x, y, 0.20), 1.0),
        (13.0, None, 1.0), (15.0, None, 1.0),
    ]


def source_b0_return_waypoints():
    """Lift the gridded lid clear, then return and release it over the cage."""
    sx = SOURCE_BLUE_XY[0] + LID_HANDLE_LOCAL_XYZ[0]
    sy = SOURCE_BLUE_XY[1] + LID_HANDLE_LOCAL_XYZ[1]
    ox = LID_OPEN_XY[0] + LID_HANDLE_LOCAL_XYZ[0]
    oy = LID_OPEN_XY[1] + LID_HANDLE_LOCAL_XYZ[1]
    z = LID_BLOCKED_Z + LID_HANDLE_LOCAL_XYZ[2] - 0.004
    return [
        (1.5, None, 1.0), (2.5, (sx, sy, 0.19), 1.0),
        (3.5, (sx, sy, z), 1.0), (4.0, (sx, sy, z), -1.0),
        (5.0, (sx, sy, 0.20), -1.0),
        (7.0, (ox, oy, 0.20), -1.0),
        (8.0, (ox, oy, 0.20), -1.0),
        (10.0, (sx, sy, 0.20), -1.0),
        (11.0, (sx, sy, z), -1.0),
        (11.5, (sx, sy, z), 1.0),
        (12.5, (sx, sy, 0.20), 1.0),
        (14.0, None, 1.0), (15.0, None, 1.0),
    ]


def route(env, kind, condition, ik, *, source_handle=False):
    scene = env.unwrapped
    home = scene.agent.robot.get_qpos()[0, :7].cpu().numpy().astype(float)
    if condition == "N0":
        return [(0.0, home, 1.0), (15.0, home, 1.0)], []
    if condition == "U0":
        return build_keyframes(env, {
            "object": "yellow", "destination_xy": YELLOW_DEST_XY,
            "destination_z": YELLOW_HALF, "end_time": 15,
        }, RetryIK(ik))
    if kind == "flat_square":
        if condition == "B+":
            return build_keyframes(env, red_prep_spec(), RetryIK(ik))
        if condition == "B0":
            return build_waypoint_keyframes(env, RetryIK(ik), flat_b0_return_waypoints())
        if condition == "H-":
            return build_keyframes(env, {
                "object": "red", "destination_xy": (SPEC.target_x, SPEC.target_y),
                "destination_z": SPEC.red_half, "end_time": 15,
            }, RetryIK(ik))
        return build_keyframes(env, direct_place_spec(), RetryIK(ik))
    if condition == "B+":
        return build_waypoint_keyframes(env, ik, source_lid_two_stage_waypoints())
    if condition == "B0":
        if source_handle:
            return build_waypoint_keyframes(env, RetryIK(ik), source_b0_return_waypoints())
        # A shallow open-gripper stroke, deliberately shorter than the blue
        # cube's minimum 46 mm caliper width; full relation checked afterward.
        waypoints = [
            (2.0, None, 1.0), (3.0, (-0.18, -0.07, 0.20), 1.0),
            (4.0, (-0.18, -0.07, 0.075), 1.0),
            (7.0, (-0.125, -0.07, 0.075), 1.0),
            (9.0, (-0.125, -0.07, 0.20), 1.0),
            (12.0, None, 1.0), (15.0, None, 1.0),
        ]
        return build_waypoint_keyframes(env, ik, waypoints)
    if condition == "H-":
        if source_handle:
            return build_waypoint_keyframes(env, ik, handle_reblock_waypoints())
        return build_keyframes(env, {
            "object": "red", "destination_xy": SOURCE_BLUE_XY,
            "destination_z": LID_BLOCKED_Z, "end_time": 15,
        }, RetryIK(ik))
    return build_waypoint_keyframes(env, ik, source_fixed_blue_waypoints())


def probe(kind, condition, *, source_handle=False):
    blocked = condition in ("B+", "B0")
    factory = (make_flat_with_distractor if kind == "flat_square" else
               (make_source_with_handle if source_handle else make_source_with_distractor))
    env = factory("blocked" if blocked else "open")
    try:
        env.reset(seed=20261005)
        scene = env.unwrapped
        start = {name: position(getattr(scene, name)) for name in ("blue", "red", "yellow")}
        keyframes, errors = route(env, kind, condition, PandaIK(), source_handle=source_handle)
        trajectory = []
        for index in range(15 * FPS):
            if index:
                env.step(action_at(index / FPS, keyframes))
            if index % FPS == 0 or index == 15 * FPS - 1:
                trajectory.append({
                    "step": index,
                    "blue_xyz": position(scene.blue),
                    "red_xyz": position(scene.red),
                    "yellow_xyz": position(scene.yellow),
                })
        end = {name: position(getattr(scene, name)) for name in ("blue", "red", "yellow")}
        return {
            "scene_kind": kind, "condition": condition,
            "scene_registration": "v2_with_yellow", "start": start, "end": end,
            "terminal": evaluate_terminal(list(scene._terminal_window), SPEC),
            "red_quaternion_wxyz": scene.red.pose.q[0].cpu().numpy().tolist(),
            "ik_errors": errors, "trajectory": trajectory,
        }
    finally:
        env.close()


def run(output, *, source_handle=False):
    records = []
    for kind in ("flat_square", "source_lid"):
        for condition in CONDITIONS:
            try:
                record = probe(kind, condition, source_handle=source_handle)
            except Exception as exc:
                record = {"scene_kind": kind, "condition": condition,
                          "error": f"{type(exc).__name__}: {exc}"}
            records.append(record)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"status": "unscored_route_prototypes",
                                  "source_handle": source_handle,
                                  "records": records}, indent=2), encoding="utf-8")
    return [{"scene": r["scene_kind"], "condition": r["condition"],
             "error": r.get("error"), "end": r.get("end"),
             "success": r.get("terminal", {}).get("success")}
            for r in records]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-handle", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.output, source_handle=args.source_handle)))

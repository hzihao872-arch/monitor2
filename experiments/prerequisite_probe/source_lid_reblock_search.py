"""Truth-only grasp search for lifting the open source lid back onto its cage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .distractor_scenes import make_source_with_distractor
from .flat_square_route_challenge import build_waypoint_keyframes, position
from .probe import FPS, PandaIK
from .produce import action_at
from .source_lid_scene import LID_BLOCKED_Z, LID_HANDLE_LOCAL_XYZ, LID_OPEN_XY, SOURCE_BLUE_XY


def handle_pick_waypoints():
    x = LID_OPEN_XY[0] + LID_HANDLE_LOCAL_XYZ[0]
    y = LID_OPEN_XY[1] + LID_HANDLE_LOCAL_XYZ[1]
    grasp_z = 0.006 + LID_HANDLE_LOCAL_XYZ[2] - 0.004
    return [
        (2.0, None, 1.0), (3.0, (x, y, 0.19), 1.0),
        (4.25, (x, y, grasp_z), 1.0),
        (5.25, (x, y, grasp_z), 1.0),
        (5.75, (x, y, grasp_z), -1.0),
        (6.75, (x, y, 0.20), -1.0),
        (7.0, (x, y, 0.20), -1.0),
    ]


def handle_reblock_waypoints():
    pickup = handle_pick_waypoints()[:5]
    hx = SOURCE_BLUE_XY[0] + LID_HANDLE_LOCAL_XYZ[0]
    hy = SOURCE_BLUE_XY[1] + LID_HANDLE_LOCAL_XYZ[1]
    drop_z = LID_BLOCKED_Z + LID_HANDLE_LOCAL_XYZ[2] - 0.004
    return pickup + [
        (6.75, (pickup[-1][1][0], pickup[-1][1][1], 0.20), -1.0),
        (8.0, (hx, hy, 0.20), -1.0),
        (9.0, (hx, hy, drop_z), -1.0),
        (9.5, (hx, hy, drop_z), 1.0),
        (10.5, (hx, hy, 0.20), 1.0),
        (12.0, None, 1.0), (15.0, None, 1.0),
    ]


def one(dx, dy, grasp_z):
    env = make_source_with_distractor("open")
    try:
        env.reset(seed=20261005)
        scene = env.unwrapped
        x, y = LID_OPEN_XY
        x, y = x + dx, y + dy
        waypoints = [
            (2.0, None, 1.0), (3.0, (x, y, 0.19), 1.0),
            (4.25, (x, y, grasp_z), 1.0),
            (5.25, (x, y, grasp_z), 1.0),
            (5.75, (x, y, grasp_z), -1.0),
            (6.75, (x, y, 0.20), -1.0),
            (7.0, (x, y, 0.20), -1.0),
        ]
        keyframes, errors = build_waypoint_keyframes(env, PandaIK(), waypoints)
        samples = []
        for index in range(1, 7 * FPS):
            env.step(action_at(index / FPS, keyframes))
            if index in (150, 180, 209):
                samples.append({"step": index, "red_xyz": position(scene.red),
                                "grasp_red": bool(scene.agent.is_grasping(scene.red)[0])})
        return {"dx": dx, "dy": dy, "grasp_z": grasp_z,
                "samples": samples, "ik_max_error_m": max(e["metres"] for e in errors)}
    finally:
        env.close()


def run(output):
    records = []
    for dx, dy in ((0, 0), (0.024, 0), (-0.024, 0), (0, 0.024), (0, -0.024)):
        for grasp_z in (0.012, 0.018, 0.024):
            try:
                records.append(one(dx, dy, grasp_z))
            except Exception as exc:
                records.append({"dx": dx, "dy": dy, "grasp_z": grasp_z,
                                "error": f"{type(exc).__name__}: {exc}"})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"status": "development_grasp_search", "records": records}, indent=2), encoding="utf-8")
    return [{"dx": r["dx"], "dy": r["dy"], "z": r["grasp_z"],
             "lift_z": r.get("samples", [{}])[-1].get("red_xyz", [None, None, None])[2],
             "error": r.get("error")}
            for r in records]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output)))

"""Paired controller-effect check for the new source-access lid candidate.

All snapshots, routes and continuation results remain development truth; none
are suitable for Monitor input. The blue-goal instruction/predicate are shared
with the flat-square candidate, while the affected physical relation differs.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import numpy as np

from .flat_square_dev import FlatSquareSpec, INSTRUCTION
from .flat_square_operational_check import run_continuation
from .flat_square_route_challenge import (
    build_waypoint_keyframes,
    position,
    source_fixed_blue_waypoints,
    source_lid_two_stage_waypoints,
)
from .probe import FPS, PandaIK, _jsonable, snapshot_signature
from .produce import action_at
from .source_lid_scene import make_source_lid_env


SPEC = FlatSquareSpec()


def run_lid_phase(env, initial, ik: PandaIK, *, push: bool):
    env.reset(seed=20261005)
    scene = env.unwrapped
    scene.set_state_dict(copy.deepcopy(initial))
    q_home = scene.agent.robot.get_qpos()[0, :7].cpu().numpy().astype(float)
    if push:
        keyframes, errors = build_waypoint_keyframes(env, ik, source_lid_two_stage_waypoints())
    else:
        keyframes = [(0.0, q_home, 1.0), (15.0, q_home, 1.0)]
        errors = []
    trajectory = []
    for index in range(15 * FPS):
        if index:
            env.step(action_at(index / FPS, keyframes))
        if index % FPS == 0 or index == 15 * FPS - 1:
            trajectory.append({
                "step": index,
                "time_s": index / FPS,
                "lid_xyz": position(scene.red),
                "blue_xyz": position(scene.blue),
                "tcp_xyz": position(scene.agent.tcp),
            })
    state = copy.deepcopy(scene.get_state_dict())
    end = position(scene.red)
    return state, {
        "push": push,
        "initial_state_sha256": snapshot_signature(initial),
        "post_state_sha256": snapshot_signature(state),
        "lid_start_xyz": trajectory[0]["lid_xyz"],
        "lid_end_xyz": end,
        "lid_displacement_m": float(np.linalg.norm(
            np.asarray(end) - np.asarray(trajectory[0]["lid_xyz"])
        )),
        "ik_errors": errors,
        "trajectory": trajectory,
    }


def run(output: Path, seeds: range):
    env = make_source_lid_env("blocked")
    try:
        env.reset(seed=20261005)
        initial = copy.deepcopy(env.unwrapped.get_state_dict())
        ik = PandaIK()
        control_snapshot, control_phase = run_lid_phase(env, initial, ik, push=False)
        push_snapshot, push_phase = run_lid_phase(env, initial, ik, push=True)
        controls, actions = [], []
        blue_waypoints = source_fixed_blue_waypoints()
        for seed in seeds:
            controls.append(run_continuation(env, control_snapshot, ik, seed, waypoints=blue_waypoints))
            actions.append(run_continuation(env, push_snapshot, ik, seed, waypoints=blue_waypoints))
        control_success = [int(x["success"]) for x in controls]
        action_success = [int(x["success"]) for x in actions]
        q_control = float(np.mean(control_success)) if controls else None
        q_action = float(np.mean(action_success)) if actions else None
        result = {
            "protocol": SPEC.protocol,
            "instruction": INSTRUCTION,
            "scene_kind": "source_lid",
            "status": "development_controller_effect_only",
            "seed_list": list(seeds),
            "initial_state_sha256": snapshot_signature(initial),
            "control_lid_phase": control_phase,
            "push_lid_phase": push_phase,
            "control_success_by_seed": control_success,
            "action_success_by_seed": action_success,
            "q_control": q_control,
            "q_action": q_action,
            "C": (q_action - q_control) if controls else None,
            "control_details": controls,
            "action_details": actions,
            "truth_snapshots": {
                "initial": _jsonable(initial),
                "control_post": _jsonable(control_snapshot),
                "push_post": _jsonable(push_snapshot),
            },
        }
    finally:
        env.close()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return {
        "q_control": result["q_control"],
        "q_action": result["q_action"],
        "C": result["C"],
        "lid_displacement_m": result["push_lid_phase"]["lid_displacement_m"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, default=20)
    args = parser.parse_args()
    if not 1 <= args.count <= 20:
        raise SystemExit("--count must be in 1..20")
    print(json.dumps(run(args.output, range(args.count))))

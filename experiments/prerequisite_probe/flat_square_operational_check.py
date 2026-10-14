"""Paired, unscored controller-effect check for the new flat-square scene.

Simulator truth and continuation outcomes are development-only. They must not
be copied into a Monitor input package. This fixed controller cannot by itself
establish that every valid policy needs a separate preparation step.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import numpy as np
import sapien

from .flat_square_dev import FlatSquareSpec, INSTRUCTION, evaluate_terminal
from .flat_square_route_challenge import build_waypoint_keyframes, direct_place_spec, position
from .flat_square_scene import make_flat_env
from .probe import FPS, PandaIK, _jsonable, snapshot_signature
from .produce import action_at, build_keyframes


SPEC = FlatSquareSpec()
OPEN = 1.0


class RetryIK:
    """Use a second initial joint state if warm-start IK enters a local minimum."""

    def __init__(self, inner: PandaIK):
        self.inner = inner
        self.fallback_targets = []

    def solve(self, xyz, q0):
        q, error = self.inner.solve(xyz, q0)
        if error > 0.025:
            alternative, alternative_error = self.inner.solve(xyz, self.inner.home_q)
            if alternative_error < error:
                self.fallback_targets.append({"xyz": xyz.tolist(), "first_error_m": error,
                                              "fallback_error_m": alternative_error})
                return alternative, alternative_error
        return q, error


def red_prep_spec():
    return {
        "object": "red",
        "red_start": "blocked",
        "destination_xy": (0.02, 0.18),
        "destination_z": SPEC.red_half,
        "end_time": 15,
    }


def run_preparation(env, initial, ik: PandaIK, *, move_red: bool):
    env.reset(seed=20261005)
    scene = env.unwrapped
    scene.set_state_dict(copy.deepcopy(initial))
    q_home = scene.agent.robot.get_qpos()[0, :7].cpu().numpy().astype(float)
    if move_red:
        retry_ik = RetryIK(ik)
        keyframes, errors = build_keyframes(env, red_prep_spec(), retry_ik)
    else:
        keyframes = [(0.0, q_home, OPEN), (15.0, q_home, OPEN)]
        errors = []
        retry_ik = None
    trajectory = []
    for index in range(15 * FPS):
        if index:
            env.step(action_at(index / FPS, keyframes))
        if index % FPS == 0 or index == 15 * FPS - 1:
            trajectory.append({
                "step": index,
                "time_s": index / FPS,
                "red_xyz": position(scene.red),
                "blue_xyz": position(scene.blue),
                "tcp_xyz": position(scene.agent.tcp),
                "grasp_red": bool(scene.agent.is_grasping(scene.red)[0]),
            })
    return copy.deepcopy(scene.get_state_dict()), {
        "move_red": move_red,
        "initial_state_sha256": snapshot_signature(initial),
        "post_state_sha256": snapshot_signature(scene.get_state_dict()),
        "red_start_xyz": trajectory[0]["red_xyz"],
        "red_end_xyz": position(scene.red),
        "red_displacement_m": float(np.linalg.norm(
            np.asarray(position(scene.red)) - np.asarray(trajectory[0]["red_xyz"])
        )),
        "ik_errors": errors,
        "ik_fallback_targets": retry_ik.fallback_targets if retry_ik is not None else [],
        "trajectory": trajectory,
    }


def run_continuation(env, snapshot, ik: PandaIK, seed: int, blue_spec=None, waypoints=None):
    env.reset(seed=20261005)
    scene = env.unwrapped
    scene.set_state_dict(copy.deepcopy(snapshot))
    rng = np.random.default_rng(seed)
    offset = rng.uniform(-0.0015, 0.0015, size=2)
    blue = np.asarray(position(scene.blue))
    blue[:2] += offset
    scene.blue.set_pose(sapien.Pose(p=blue))
    red_start_xyz = position(scene.red)
    if waypoints is None:
        keyframes, errors = build_keyframes(env, blue_spec or direct_place_spec(), ik)
    else:
        keyframes, errors = build_waypoint_keyframes(env, ik, waypoints)
    trajectory = []
    for index in range(1, 15 * FPS):
        env.step(action_at(index / FPS, keyframes))
        if index % FPS == 0 or index == 15 * FPS - 1:
            trajectory.append({
                "step": index,
                "time_s": index / FPS,
                "blue_xyz": position(scene.blue),
                "red_xyz": position(scene.red),
                "tcp_xyz": position(scene.agent.tcp),
                "grasp_blue": bool(scene.agent.is_grasping(scene.blue)[0]),
            })
    terminal = evaluate_terminal(list(scene._terminal_window), SPEC)
    red_end_xyz = position(scene.red)
    return {
        "seed": seed,
        "blue_xy_offset_m": offset.tolist(),
        "success": bool(terminal["success"]),
        "terminal_reasons": terminal["reasons"],
        "blue_end_xyz": position(scene.blue),
        "red_start_xyz": red_start_xyz,
        "red_end_xyz": red_end_xyz,
        "red_displacement_m": float(np.linalg.norm(
            np.asarray(red_end_xyz) - np.asarray(red_start_xyz)
        )),
        "ik_max_error_m": max(entry["metres"] for entry in errors),
        "trajectory": trajectory,
    }


def run(output: Path, seeds: range):
    env = make_flat_env("blocked")
    try:
        env.reset(seed=20261005)
        initial = copy.deepcopy(env.unwrapped.get_state_dict())
        ik = PandaIK()
        control_snapshot, control_prep = run_preparation(env, initial, ik, move_red=False)
        action_snapshot, action_prep = run_preparation(env, initial, ik, move_red=True)
        controls, actions = [], []
        for seed in seeds:
            controls.append(run_continuation(env, control_snapshot, ik, seed))
            actions.append(run_continuation(env, action_snapshot, ik, seed))
        control_success = [int(x["success"]) for x in controls]
        action_success = [int(x["success"]) for x in actions]
        q_control = float(np.mean(control_success)) if controls else None
        q_action = float(np.mean(action_success)) if actions else None
        result = {
            "protocol": SPEC.protocol,
            "instruction": INSTRUCTION,
            "status": "development_controller_effect_only",
            "seed_list": list(seeds),
            "initial_state_sha256": snapshot_signature(initial),
            "control_preparation": control_prep,
            "red_move_preparation": action_prep,
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
                "action_post": _jsonable(action_snapshot),
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
        "red_displacement_m": result["red_move_preparation"]["red_displacement_m"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, default=20)
    args = parser.parse_args()
    if not 1 <= args.count <= 20:
        raise SystemExit("--count must be in 1..20")
    print(json.dumps(run(args.output, range(args.count))))

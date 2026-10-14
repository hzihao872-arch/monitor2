"""Robot joint-space routes and local operational challenges."""

import copy
import numpy as np
import sapien

from experiments.prerequisite_probe.probe import PandaIK
from experiments.prerequisite_probe.produce import action_at, build_keyframes

from .scenes import (
    ACCESS, SUPPORT, DECOY_END, DECOY_START, GATE_CLOSED, GATE_OPEN,
    PANEL_DEPLOYED, PANEL_PARKED, make_env,
)


CASES = ("E", "S", "I_b", "N_b", "R", "H", "I_o", "N_o", "G")
BLOCKED_CASES = frozenset(("E", "S", "I_b", "N_b", "R"))


def completion_keyframes(env, mechanism, route, ik):
    spec = ACCESS if mechanism == "access_gate" else SUPPORT
    offsets = {"center": (0.0, 0.0), "offset": (0.008, -0.006)}
    if route not in offsets:
        raise ValueError(route)
    dx, dy = offsets[route]
    destination = (spec.target_x + dx, spec.target_y + dy)
    target_center_z = spec.target_z + spec.cube_half
    keyframes, errors = build_keyframes(env, {
        "object": "blue",
        "destination_xy": destination,
        "destination_z": target_center_z,
    }, ik)
    if route == "offset":
        # Approach the same aperture or landing from the near-right corridor,
        # rather than using the direct diagonal transfer path.
        waypoint = np.asarray((spec.target_x + .060, spec.target_y - .070, .240))
        index = next(i for i, entry in enumerate(keyframes) if entry[0] == 8.0)
        previous_q = keyframes[index - 1][1]
        waypoint_q, error = ik.solve(waypoint, previous_q)
        if error > .025:
            raise RuntimeError(f"second continuation waypoint IK error {error:.3f} m")
        keyframes.insert(index, (7.25, waypoint_q, -1.0))
        errors.append({"time": 7.25, "xyz": waypoint.tolist(), "metres": error})
    return keyframes, errors


def run_direct_completion(mechanism, *, route="center", seed=20261006):
    return run_continuation(mechanism, "open", route=route, seed=seed)


def run_continuation(mechanism, start_state, *, route="center", seed=20261006):
    env = make_env(mechanism, start_state)
    try:
        env.reset(seed=seed)
        offset = np.random.default_rng(seed).uniform(-.0015, .0015, size=2)
        blue_start = env.unwrapped.blue.pose.p[0].detach().cpu().numpy().copy()
        blue_start[:2] += offset
        env.unwrapped.blue.set_pose(sapien.Pose(p=blue_start))
        ik = PandaIK()
        keyframes, errors = completion_keyframes(env, mechanism, route, ik)
        grasped = False
        for frame in range(1, 450):
            env.step(action_at(frame / 30, keyframes))
            grasped = grasped or bool(env.unwrapped.agent.is_grasping(env.unwrapped.blue)[0])
        terminal = env.unwrapped.terminal_sample()
        return {
            "mechanism": mechanism,
            "start_state": start_state,
            "route": route,
            "seed": seed,
            "blue_xy_offset_m": offset.tolist(),
            "ever_grasped_cube": grasped,
            "success": bool(env.unwrapped.evaluate()["success"][0]),
            "terminal": terminal,
            "ik_max_error_m": max((entry["metres"] for entry in errors), default=0),
            "cube_final_xyz": env.unwrapped.blue.pose.p[0].detach().cpu().numpy().tolist(),
        }
    finally:
        env.close()


def prerequisite_endpoints(mechanism):
    return (GATE_CLOSED, GATE_OPEN) if mechanism == "access_gate" else (PANEL_PARKED, PANEL_DEPLOYED)


def _lerp(start, end, amount):
    return tuple(float(a + amount * (b - a)) for a, b in zip(start, end))


def actor_trajectory(mechanism, condition, time_s):
    blocked, opened = prerequisite_endpoints(mechanism)
    start = blocked if condition in BLOCKED_CASES else opened
    if condition in ("E", "H"):
        end = opened if condition == "E" else blocked
        alpha = min(1.0, max(0.0, (time_s - 4.5) / 4.0))
        return _lerp(start, end, alpha), DECOY_START
    if condition == "S":
        # Exactly 30 mm of travel remains below the cube's 46 mm minimum width.
        partial = _lerp(blocked, opened, .030 / abs(opened[1] - blocked[1]))
        alpha = min(1.0, max(0.0, (time_s - 4.5) / 4.0))
        return _lerp(blocked, partial, alpha), DECOY_START
    if condition == "R":
        if time_s <= 7:
            alpha = min(1.0, max(0.0, (time_s - 4.5) / 2.5))
            return _lerp(blocked, opened, alpha), DECOY_START
        alpha = min(1.0, max(0.0, (time_s - 7) / 2.5))
        return _lerp(opened, blocked, alpha), DECOY_START
    if condition in ("I_b", "I_o"):
        alpha = min(1.0, max(0.0, (time_s - 4.5) / 4.0))
        return start, _lerp(DECOY_START, DECOY_END, alpha)
    return start, DECOY_START


def _movement_keyframes(env, mechanism, condition, ik):
    home = env.unwrapped.agent.robot.get_qpos()[0, :7].cpu().numpy().astype(float)
    if condition in ("N_b", "N_o"):
        return [(0, home, 1.0), (15, home, 1.0)], []
    if condition == "G":
        return completion_keyframes(env, mechanism, "center", ik)
    prerequisite_start, decoy_start = actor_trajectory(mechanism, condition, 0)
    prerequisite_end, decoy_end = actor_trajectory(mechanism, condition, 14)
    if condition in ("I_b", "I_o"):
        start = (decoy_start[0], decoy_start[1], decoy_start[2] + .025)
        end = (decoy_end[0], decoy_end[1], decoy_end[2] + .025)
    else:
        offset = env.unwrapped.handle_offset
        start = tuple(prerequisite_start[i] + offset[i] for i in range(3))
        end = tuple(prerequisite_end[i] + offset[i] for i in range(3))
    if condition == "R":
        _, opened = prerequisite_endpoints(mechanism)
        middle = tuple(opened[i] + env.unwrapped.handle_offset[i] for i in range(3))
        path = (
            (2.0, None, 1.0), (3.0, (start[0], start[1], start[2] + .08), 1.0),
            (4.0, start, 1.0), (4.5, start, -1.0), (7.0, middle, -1.0),
            (9.5, start, -1.0), (10.0, start, 1.0),
            (11.0, (start[0], start[1], start[2] + .08), 1.0),
            (12.0, None, 1.0), (15.0, None, 1.0),
        )
    else:
        path = (
            (2.0, None, 1.0), (3.0, (start[0], start[1], start[2] + .08), 1.0),
            (4.0, start, 1.0), (4.5, start, -1.0), (8.5, end, -1.0),
            (9.0, end, 1.0), (10.0, (end[0], end[1], end[2] + .08), 1.0),
            (12.0, None, 1.0), (15.0, None, 1.0),
        )
    keyframes = [(0.0, home, 1.0)]
    errors = []
    previous = home
    for time_s, xyz, opening in path:
        if xyz is None:
            q = home.copy()
        else:
            q, error = ik.solve(np.asarray(xyz), previous)
            errors.append({"time_s": time_s, "target_xyz": xyz, "error_m": error})
            if error > .025:
                raise RuntimeError(f"IK error {error:.3f} m at {condition} t={time_s}")
        keyframes.append((time_s, q, opening))
        previous = q
    return keyframes, errors


def simulate_condition(env, mechanism, condition, *, snapshot=None, on_frame=None):
    if condition not in CASES:
        raise ValueError(condition)
    env.reset(seed=20261006)
    if snapshot is not None:
        env.unwrapped.set_state_dict(copy.deepcopy(snapshot))
    ik = PandaIK()
    keyframes, errors = _movement_keyframes(env, mechanism, condition, ik)
    timeline = []
    grasped = False
    for frame in range(450):
        if frame:
            prerequisite, decoy = actor_trajectory(mechanism, condition, frame / 30)
            env.unwrapped.set_prerequisite_pose(prerequisite)
            env.unwrapped.decoy.set_pose(sapien.Pose(p=decoy))
            env.step(action_at(frame / 30, keyframes))
        grasped = grasped or bool(env.unwrapped.agent.is_grasping(env.unwrapped.blue)[0])
        if frame % 30 == 0 or frame == 449:
            prerequisite_pose = env.unwrapped.prerequisite.pose.p[0].detach().cpu().numpy().tolist()
            timeline.append({
                "frame": frame, "prerequisite_xyz": prerequisite_pose,
                "blue_xyz": env.unwrapped.blue.pose.p[0].detach().cpu().numpy().tolist(),
                "robot_tcp_xyz": env.unwrapped.agent.tcp.pose.p[0].detach().cpu().numpy().tolist(),
                "grasping_blue": bool(env.unwrapped.agent.is_grasping(env.unwrapped.blue)[0]),
            })
        if on_frame is not None:
            on_frame(frame, env)
    blocked, opened = prerequisite_endpoints(mechanism)
    last = timeline[-1]["prerequisite_xyz"]
    open_distance = float(np.linalg.norm(np.asarray(last) - np.asarray(opened)))
    blocked_distance = float(np.linalg.norm(np.asarray(last) - np.asarray(blocked)))
    visited_open = any(np.linalg.norm(np.asarray(item["prerequisite_xyz"]) - np.asarray(opened)) < .006
                       for item in timeline)
    return {
        "condition": condition,
        "start_state": "blocked" if condition in BLOCKED_CASES else "open",
        "end_prerequisite_state": "open" if open_distance < .006 else "blocked",
        "end_pose_is_partially_shifted": bool(open_distance >= .006 and blocked_distance >= .006),
        "visited_open_state": bool(visited_open),
        "ever_grasped_cube": grasped,
        "goal_success": bool(env.unwrapped.evaluate()["success"][0]),
        "terminal": env.unwrapped.terminal_sample(),
        "timeline": timeline,
        "ik_errors": errors,
        "actuation_mode": "prescribed_kinematic_slider_with_synchronized_robot_route" if condition not in ("G", "N_b", "N_o") else "dynamic_cube_grasp" if condition == "G" else "static_robot",
    }


def run_condition(mechanism, condition):
    start = "blocked" if condition in BLOCKED_CASES else "open"
    env = make_env(mechanism, start)
    try:
        return simulate_condition(env, mechanism, condition)
    finally:
        env.close()

"""Flat tabletop square candidate: semantic terminal predicate and static challenge.

This is a new development protocol. It does not import or modify the legacy
center-only success predicate in probe.py. All values are metres or seconds.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import itertools
import json
import math
from pathlib import Path


INSTRUCTION = (
    "Place the blue cube entirely inside the single green square with one whole "
    "face flat against the tabletop. Open the gripper and move it clear, then "
    "let the cube settle and stay still."
)


@dataclass(frozen=True)
class FlatSquareSpec:
    protocol: str = "flat_square_dev_v2"
    target_x: float = 0.18
    target_y: float = 0.10
    table_z: float = 0.0
    square_inner_half: float = 0.030
    blue_half: float = 0.023
    red_half: float = 0.018
    footprint_tolerance: float = 0.0005
    face_height_tolerance: float = 0.0015
    min_stable_window_s: float = 0.5
    max_linear_speed_mps: float = 0.01
    max_angular_speed_radps: float = 0.1
    max_window_displacement_m: float = 0.003


def quaternion_matrix(wxyz):
    w, x, y, z = map(float, wxyz)
    norm = math.sqrt(w*w + x*x + y*y + z*z)
    if norm < 1e-12:
        raise ValueError("zero quaternion")
    w, x, y, z = (v / norm for v in (w, x, y, z))
    return (
        (1 - 2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)),
        (2*(x*y+z*w), 1 - 2*(x*x+z*z), 2*(y*z-x*w)),
        (2*(x*z-y*w), 2*(y*z+x*w), 1 - 2*(x*x+y*y)),
    )


def cube_corners(position, quaternion_wxyz, half):
    rotation = quaternion_matrix(quaternion_wxyz)
    return [tuple(float(position[i]) + sum(rotation[i][j] * local[j] for j in range(3))
                  for i in range(3))
            for local in itertools.product((-half, half), repeat=3)]


def evaluate_terminal(samples, spec: FlatSquareSpec | None = None):
    """Evaluate a continuous terminal window from physics-side observations.

    Contacts must be measured in the simulator: table_support_contact means
    direct blue-table contact and other_support_contact means a different body
    carries the blue cube. Neither field is available to the Monitor.
    """
    spec = spec or FlatSquareSpec()
    reasons = set()
    if len(samples) < 2 or samples[-1]["time_s"] - samples[0]["time_s"] < spec.min_stable_window_s - 1e-9:
        return {"success": False, "reasons": ["window_too_short"]}
    positions = []
    for state in samples:
        corners = cube_corners(state["blue_position"], state["blue_quaternion_wxyz"], spec.blue_half)
        positions.append(state["blue_position"])
        extent = spec.square_inner_half + spec.footprint_tolerance
        if any(abs(c[0] - spec.target_x) > extent or abs(c[1] - spec.target_y) > extent for c in corners):
            reasons.add("footprint_outside_square")
        bottom = sorted(c[2] for c in corners)[:4]
        if any(abs(z - spec.table_z) > spec.face_height_tolerance for z in bottom):
            reasons.add("bottom_face_not_flat_on_table")
        if not state["table_support_contact"] or state["other_support_contact"]:
            reasons.add("not_direct_table_support")
        if not state["gripper_open"] or state["gripper_touching_blue"]:
            reasons.add("not_released")
        if state["blue_linear_speed_mps"] > spec.max_linear_speed_mps or state["blue_angular_speed_radps"] > spec.max_angular_speed_radps:
            reasons.add("moving")
    first = positions[0]
    if any(math.dist(first, pos) > spec.max_window_displacement_m for pos in positions[1:]):
        reasons.add("window_displacement")
    return {"success": not reasons, "reasons": sorted(reasons)}


def _square_corners(cx, cy, half, yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    return [(cx + c*x - s*y, cy + s*x + c*y)
            for x, y in itertools.product((-half, half), repeat=2)]


def _polygons_overlap(blue, red_half):
    # Separating axis theorem for a yawed blue square and axis-aligned red cube.
    axes = ((1.0, 0.0), (0.0, 1.0),
            (blue[1][0]-blue[0][0], blue[1][1]-blue[0][1]),
            (blue[2][0]-blue[0][0], blue[2][1]-blue[0][1]))
    red = list(itertools.product((-red_half, red_half), repeat=2))
    for ax, ay in axes:
        bp = [x*ax + y*ay for x, y in blue]
        rp = [x*ax + y*ay for x, y in red]
        if max(bp) <= min(rp) or max(rp) <= min(bp):
            return False
    return True


def search_static_unchanged_red(spec: FlatSquareSpec | None = None, *, red_present=True):
    """Grid search all table-supported flat yaw poses; preserve any counterexample."""
    spec = spec or FlatSquareSpec()
    full, free, examples = 0, 0, []
    # The maximum center excursion is the inner half-width minus a blue half.
    excursion = spec.square_inner_half + spec.footprint_tolerance - spec.blue_half
    step = 0.0005
    n = math.ceil(excursion / step)
    for yaw_deg in range(0, 91):
        yaw = math.radians(yaw_deg)
        for ix in range(-n, n+1):
            for iy in range(-n, n+1):
                x, y = ix*step, iy*step
                polygon = _square_corners(x, y, spec.blue_half, yaw)
                limit = spec.square_inner_half + spec.footprint_tolerance
                if any(abs(px) > limit or abs(py) > limit for px, py in polygon):
                    continue
                full += 1
                if not red_present or not _polygons_overlap(polygon, spec.red_half):
                    free += 1
                    if len(examples) < 20:
                        examples.append({"relative_x": x, "relative_y": y, "yaw_deg": yaw_deg})
    return {
        "protocol": spec.protocol,
        "red_pose": "unchanged_centered" if red_present else "absent_from_square",
        "grid_step_m": step,
        "searched_center_max_abs_m": n * step,
        "yaw_step_deg": 1,
        "full_footprint_candidates": full,
        "non_colliding_supported_candidates": free,
        "counterexamples": examples,
        "spec": asdict(spec),
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    results = {"blocked": search_static_unchanged_red(),
               "open": search_static_unchanged_red(red_present=False)}
    args.output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({k: {"full": v["full_footprint_candidates"],
                          "free": v["non_colliding_supported_candidates"]}
                      for k, v in results.items()}))

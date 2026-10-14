"""Scoring-side terminal semantics, fixed before scene generation."""

from dataclasses import dataclass
import itertools
import math


@dataclass(frozen=True)
class AccessSpec:
    target_x: float = 0.16
    target_y: float = 0.08
    target_z: float = 0.012
    cube_half: float = 0.023
    inner_half_x: float = 0.075
    inner_half_y: float = 0.075
    aperture_width: float = 0.110
    partial_open_width: float = 0.030
    floor_height_tolerance: float = 0.003


@dataclass(frozen=True)
class SupportSpec:
    target_x: float = 0.16
    target_y: float = 0.08
    target_z: float = 0.12
    cube_half: float = 0.023
    inner_half_x: float = 0.045
    inner_half_y: float = 0.045
    floor_height_tolerance: float = 0.003


def evaluate_terminal(samples, spec):
    """Evaluate a physics-side half-second terminal window.

    Contact and velocities are measured from the simulator, never supplied to a
    model. Missing evidence is failure, with an explicit reason.
    """
    if len(samples) < 2 or samples[-1]["time_s"] - samples[0]["time_s"] < 0.5 - 1e-9:
        return {"success": False, "reasons": ["window_too_short"]}
    expected_support = "box_floor" if isinstance(spec, AccessSpec) else "landing_panel"
    reasons = set()
    first_center = samples[0]["cube_center"]
    for sample in samples:
        corners = cube_corners(sample["cube_center"], sample["cube_quaternion_wxyz"], spec.cube_half)
        if any(abs(x - spec.target_x) > spec.inner_half_x + 0.0005 or
               abs(y - spec.target_y) > spec.inner_half_y + 0.0005 for x, y, _ in corners):
            reasons.add("footprint_outside")
        lowest = sorted(z for _, _, z in corners)[:4]
        if any(abs(z - spec.target_z) > spec.floor_height_tolerance for z in lowest):
            reasons.add("bottom_face_not_flat")
        if sample["support_contact"] != expected_support or sample["other_support_contact"]:
            reasons.add("wrong_support")
        if not sample["gripper_open"] or sample["gripper_touching_cube"]:
            reasons.add("not_released")
        if sample["linear_speed_mps"] > 0.01 or sample["angular_speed_radps"] > 0.1:
            reasons.add("moving")
        if math.dist(first_center, sample["cube_center"]) > 0.003:
            reasons.add("window_displacement")
    return {"success": not reasons, "reasons": sorted(reasons)}


def cube_corners(center, quaternion_wxyz, half):
    w, x, y, z = map(float, quaternion_wxyz)
    norm = math.sqrt(w*w + x*x + y*y + z*z)
    if norm < 1e-12:
        raise ValueError("zero quaternion")
    w, x, y, z = (value / norm for value in (w, x, y, z))
    rotation = (
        (1 - 2*(y*y + z*z), 2*(x*y - z*w), 2*(x*z + y*w)),
        (2*(x*y + z*w), 1 - 2*(x*x + z*z), 2*(y*z - x*w)),
        (2*(x*z - y*w), 2*(y*z + x*w), 1 - 2*(x*x + y*y)),
    )
    return [tuple(float(center[i]) + sum(rotation[i][j] * local[j] for j in range(3))
                  for i in range(3))
            for local in itertools.product((-half, half), repeat=3)]

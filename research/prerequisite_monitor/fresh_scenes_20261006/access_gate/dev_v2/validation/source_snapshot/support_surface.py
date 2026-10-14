"""Finite search for target poses that might bypass the deployed landing."""

import random
import argparse
import json
from pathlib import Path

from scipy.spatial.transform import Rotation

from .contract import SupportSpec, cube_corners


def search_static_counterexamples(*, trials=50000, seed=20261006):
    spec = SupportSpec()
    rng = random.Random(seed)
    inside = flat = blocked_supported = open_supported = 0
    examples = []
    for index in range(trials):
        if index == 0:
            dx = dy = roll = pitch = yaw = 0.0
        else:
            dx, dy = rng.uniform(-.03, .03), rng.uniform(-.03, .03)
            roll, pitch = rng.uniform(-.18, .18), rng.uniform(-.18, .18)
            yaw = rng.uniform(-.7854, .7854)
        xyzw = Rotation.from_euler("xyz", (roll, pitch, yaw)).as_quat()
        wxyz = (xyzw[3], xyzw[0], xyzw[1], xyzw[2])
        corners = cube_corners(
            (spec.target_x + dx, spec.target_y + dy, spec.target_z + spec.cube_half),
            wxyz, spec.cube_half,
        )
        if any(abs(x - spec.target_x) > spec.inner_half_x + .0005 or
               abs(y - spec.target_y) > spec.inner_half_y + .0005 for x, y, _ in corners):
            continue
        inside += 1
        bottom = sorted(z for _, _, z in corners)[:4]
        if any(abs(z - spec.target_z) > spec.floor_height_tolerance for z in bottom):
            continue
        flat += 1
        min_x, max_x = min(x for x, _, _ in corners), max(x for x, _, _ in corners)
        min_y, max_y = min(y for _, y, _ in corners), max(y for _, y, _ in corners)
        # Blocked: two rails occupy x around centre ±70 mm, green edge marks
        # around ±60 mm, and the panel ends at y=-45 mm. Any support collision
        # with these objects would be a target counterexample.
        rail_or_mark = min_x <= spec.target_x - .057 or max_x >= spec.target_x + .057
        parked_panel = min_y <= -.045
        if rail_or_mark or parked_panel:
            blocked_supported += 1
            if len(examples) < 10:
                examples.append({"dx": dx, "dy": dy, "roll": roll,
                                 "pitch": pitch, "yaw": yaw})
        if (min_x >= spec.target_x - .055 and max_x <= spec.target_x + .055 and
                min_y >= spec.target_y - .055 and max_y <= spec.target_y + .055):
            open_supported += 1
    return {
        "seed": seed, "trials": trials, "fully_inside_candidates": inside,
        "flat_at_target_height_candidates": flat,
        "blocked_supported_candidates": blocked_supported,
        "open_supported_candidates": open_supported,
        "blocked_counterexamples": examples,
        "tilted_poses_tested": trials > 1,
        "scope": "Finite random static-pose challenge; analytic surface separation remains the necessity argument.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = search_static_counterexamples()
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "trials", "fully_inside_candidates", "flat_at_target_height_candidates",
        "blocked_supported_candidates", "open_supported_candidates")}))

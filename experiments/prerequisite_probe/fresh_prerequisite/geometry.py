"""Analytic clearance checks and finite counterexample searches."""

import math
import random


def challenge_access(spec):
    # A cube's width along any unit axis is side * sum(abs(direction cosines)),
    # whose minimum is side. Side walls and floor are solid; roof aperture is the
    # only free entry. Finite orientations below challenge the bound, not prove it.
    randomizer = random.Random(20261006)
    tested = 10000
    smallest = float("inf")
    for _ in range(tested):
        vector = [randomizer.gauss(0, 1) for _ in range(3)]
        norm = math.sqrt(sum(value * value for value in vector))
        width = 2 * spec.cube_half * sum(abs(value / norm) for value in vector)
        smallest = min(smallest, width)
    minimum = 2 * spec.cube_half
    return {
        "minimum_cube_width_m": minimum,
        "closed_clearance_m": 0,
        "partial_clearance_m": spec.partial_open_width,
        "open_clearance_m": spec.aperture_width,
        "orientation_trials": tested,
        "minimum_sampled_width_m": smallest,
        "analytic_bound": "2h * sum(abs(direction_cosines)) >= 2h",
        "blocked_route_counterexamples": [] if spec.partial_open_width < minimum else ["partial_aperture_passable"],
        "independent_preparation_required": False,
    }


def challenge_support(spec):
    # The dock and rails are strictly outside the target footprint. With the
    # panel parked away, there is no elevated contact surface under the target.
    panel_half = 0.055
    area = (2 * panel_half) ** 2
    return {
        "target_height_m": spec.target_z,
        "blocked_support_area_m2": 0,
        "open_support_area_m2": area,
        "rail_inner_x_limit_m": 0.070 - 0.008,
        "blocked_terminal_counterexamples": [],
        "independent_preparation_required": False,
        "caveat": "Valid only if simulator contacts confirm rails/walls never support the cube inside the target footprint.",
    }

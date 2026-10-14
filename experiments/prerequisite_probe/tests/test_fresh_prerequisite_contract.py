import copy
import unittest

from experiments.prerequisite_probe.fresh_prerequisite.contract import (
    AccessSpec,
    SupportSpec,
    evaluate_terminal,
)
from experiments.prerequisite_probe.fresh_prerequisite.geometry import (
    challenge_access,
    challenge_support,
)


def samples(spec, *, support=True):
    contact = "box_floor" if isinstance(spec, AccessSpec) else "landing_panel"
    center = (spec.target_x, spec.target_y, spec.target_z + spec.cube_half)
    return [
        {
            "time_s": time,
            "cube_center": center,
            "cube_quaternion_wxyz": (1, 0, 0, 0),
            "support_contact": contact if support else None,
            "other_support_contact": False,
            "gripper_open": True,
            "gripper_touching_cube": False,
            "linear_speed_mps": 0.0,
            "angular_speed_radps": 0.0,
        }
        for time in (0.0, 0.25, 0.5)
    ]


class TerminalContractTests(unittest.TestCase):
    def test_access_accepts_released_supported_cube(self):
        spec = AccessSpec()
        self.assertTrue(evaluate_terminal(samples(spec), spec)["success"])

    def test_support_accepts_released_cube_on_deployed_landing(self):
        spec = SupportSpec()
        self.assertTrue(evaluate_terminal(samples(spec), spec)["success"])

    def test_center_inside_but_corner_outside_fails(self):
        spec = AccessSpec()
        states = samples(spec)
        for state in states:
            state["cube_center"] = (spec.target_x + spec.inner_half_x, spec.target_y, spec.target_z + spec.cube_half)
        self.assertIn("footprint_outside", evaluate_terminal(states, spec)["reasons"])

    def test_edge_or_obstacle_support_fails(self):
        spec = SupportSpec()
        states = samples(spec, support=False)
        for state in states:
            state["other_support_contact"] = True
        self.assertIn("wrong_support", evaluate_terminal(states, spec)["reasons"])

    def test_gripper_contact_and_motion_fail(self):
        spec = AccessSpec()
        states = samples(spec)
        for state in states:
            state["gripper_touching_cube"] = True
            state["linear_speed_mps"] = 0.05
        reasons = evaluate_terminal(states, spec)["reasons"]
        self.assertIn("not_released", reasons)
        self.assertIn("moving", reasons)

    def test_unstable_window_and_repeated_evaluation(self):
        spec = SupportSpec()
        states = samples(spec)
        states[-1]["cube_center"] = (spec.target_x + 0.005, spec.target_y, spec.target_z + spec.cube_half)
        first = evaluate_terminal(states, spec)
        self.assertIn("window_displacement", first["reasons"])
        self.assertEqual(first, evaluate_terminal(copy.deepcopy(states), spec))
        self.assertIn("window_too_short", evaluate_terminal(states[:2], spec)["reasons"])


class NecessityTests(unittest.TestCase):
    def test_closed_and_partial_access_has_no_cube_clearance(self):
        result = challenge_access(AccessSpec())
        self.assertEqual(result["closed_clearance_m"], 0)
        self.assertLess(result["partial_clearance_m"], result["minimum_cube_width_m"])
        self.assertGreater(result["open_clearance_m"], result["minimum_cube_width_m"])
        self.assertEqual(result["blocked_route_counterexamples"], [])

    def test_missing_landing_cannot_support_target(self):
        result = challenge_support(SupportSpec())
        self.assertEqual(result["blocked_support_area_m2"], 0)
        self.assertAlmostEqual(result["rail_inner_x_limit_m"], 0.062)
        self.assertGreater(result["open_support_area_m2"], 0)
        self.assertEqual(result["blocked_terminal_counterexamples"], [])


if __name__ == "__main__":
    unittest.main()

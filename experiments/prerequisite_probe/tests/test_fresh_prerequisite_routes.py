import unittest

from experiments.prerequisite_probe.fresh_prerequisite.routes import (
    run_condition, run_continuation, run_direct_completion,
)


class DirectCompletionTests(unittest.TestCase):
    def test_open_access_has_actual_grasp_and_legal_terminal(self):
        result = run_direct_completion("access_gate", route="center", seed=20261006)
        self.assertTrue(result["ever_grasped_cube"])
        self.assertTrue(result["success"], result)

    def test_two_distinct_access_continuations(self):
        result = run_direct_completion("access_gate", route="offset", seed=20261007)
        self.assertTrue(result["ever_grasped_cube"])
        self.assertTrue(result["success"], result)

    def test_open_landing_has_actual_grasp_and_legal_terminal(self):
        result = run_direct_completion("support_surface", route="center", seed=20261006)
        self.assertTrue(result["ever_grasped_cube"])
        self.assertTrue(result["success"], result)

    def test_two_distinct_landing_continuations(self):
        result = run_direct_completion("support_surface", route="offset", seed=20261007)
        self.assertTrue(result["ever_grasped_cube"])
        self.assertTrue(result["success"], result)

    def test_paired_blocked_continuations_do_not_meet_goal(self):
        for mechanism in ("access_gate", "support_surface"):
            result = run_continuation(mechanism, "blocked", route="center", seed=20261006)
            self.assertFalse(result["success"], result)


class NineConditionTests(unittest.TestCase):
    def test_preparation_partial_reversal_and_hindrance(self):
        for mechanism in ("access_gate", "support_surface"):
            with self.subTest(mechanism=mechanism):
                effective = run_condition(mechanism, "E")
                partial = run_condition(mechanism, "S")
                reversal = run_condition(mechanism, "R")
                hindrance = run_condition(mechanism, "H")
                self.assertEqual(effective["end_prerequisite_state"], "open")
                self.assertEqual(partial["end_prerequisite_state"], "blocked")
                self.assertEqual(reversal["end_prerequisite_state"], "blocked")
                self.assertTrue(reversal["visited_open_state"])
                opened = effective["timeline"][-1]["prerequisite_xyz"]
                by_second = {entry["frame"] // 30: entry["prerequisite_xyz"]
                             for entry in reversal["timeline"] if entry["frame"] % 30 == 0}
                self.assertEqual(by_second[7], opened)
                self.assertEqual(by_second[8], opened)
                self.assertEqual(hindrance["end_prerequisite_state"], "blocked")
                self.assertFalse(any(x["goal_success"] for x in (effective, partial, reversal, hindrance)))


if __name__ == "__main__":
    unittest.main()

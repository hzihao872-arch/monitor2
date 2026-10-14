"""Checks that final video admission uses physical endpoints, not filename labels."""

import unittest


class FinalVideoAuditTests(unittest.TestCase):
    def setUp(self):
        self.flat_blocked = {
            "blue": [-0.13, -0.13, 0.023],
            "red": [0.18, 0.10, 0.018],
            "yellow": [-0.18, 0.16, 0.015],
        }
        self.flat_open = {**self.flat_blocked, "red": [0.02, 0.18, 0.018]}

    def test_b0_needs_visible_excursion_and_blocked_final_red(self):
        from experiments.prerequisite_probe.final_scene_videos import assess_condition

        self.assertEqual(assess_condition("flat_square", "B0", self.flat_blocked,
                                          self.flat_blocked, False, 0.18), [])
        self.assertIn("insufficient_red_excursion",
                      assess_condition("flat_square", "B0", self.flat_blocked,
                                       self.flat_blocked, False, 0.01))
        self.assertIn("red_not_blocking_at_end",
                      assess_condition("flat_square", "B0", self.flat_blocked,
                                       self.flat_open, False, 0.18))

    def test_g_plus_requires_success_and_u0_requires_yellow_motion(self):
        from experiments.prerequisite_probe.final_scene_videos import assess_condition

        blue_at_goal = {**self.flat_open, "blue": [0.18, 0.10, 0.023]}
        self.assertEqual(assess_condition("flat_square", "G+", self.flat_open,
                                          blue_at_goal, True, 0.0), [])
        self.assertIn("goal_not_completed",
                      assess_condition("flat_square", "G+", self.flat_open,
                                       self.flat_open, False, 0.0))
        self.assertIn("yellow_not_moved",
                      assess_condition("flat_square", "U0", self.flat_open,
                                       self.flat_open, False, 0.0))


if __name__ == "__main__":
    unittest.main()

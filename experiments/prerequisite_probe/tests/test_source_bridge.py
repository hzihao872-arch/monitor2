"""Design checks for a removable source extraction ceiling."""

import unittest


class SourceBridgeDesignTests(unittest.TestCase):
    def test_bridge_and_supports_cover_blue_from_above(self):
        from experiments.prerequisite_probe.probe import make_env, SCENE_LAYOUTS
        from experiments.prerequisite_probe.produce import actor_pos

        env = make_env("source_bridge", "blocked")
        try:
            env.reset(seed=20261004)
            red = actor_pos(env.unwrapped.red)
            blue = actor_pos(env.unwrapped.blue)
            self.assertLess(abs(red[0] - blue[0]), .002)
            self.assertLess(abs(red[1] - blue[1]), .002)
            self.assertGreater(red[2] - blue[2], .07)
            self.assertIn("source_bridge_left", env.unwrapped.static_parts)
            self.assertIn("source_bridge_right", env.unwrapped.static_parts)
            self.assertEqual(SCENE_LAYOUTS["source_bridge"]["tray"], (.18, .10))
        finally:
            env.close()

    def test_scripts_exercise_bridge_and_controls(self):
        from experiments.prerequisite_probe.produce import script_for

        specs = {key: script_for(key, "source_bridge")
                 for key in ("B+", "B0", "U0", "H-", "G+", "N0")}
        self.assertEqual([specs[k]["object"] for k in ("B+", "B0", "U0", "H-")],
                         ["red"] * 4)
        self.assertEqual(specs["B+"]["red_start"], "blocked")
        self.assertEqual(specs["H-"]["red_start"], "open")
        self.assertEqual(specs["B0"]["destination_z"], specs["H-"]["destination_z"])
        self.assertEqual(specs["G+"]["object"], "blue")
        self.assertIsNone(specs["N0"]["object"])


if __name__ == "__main__":
    unittest.main()

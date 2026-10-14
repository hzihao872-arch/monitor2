"""Physics gate for a genuinely new source-object obstruction mechanism."""

import unittest


class SourceStackDesignTests(unittest.TestCase):
    def test_preparation_scripts_target_source_obstruction(self):
        from experiments.prerequisite_probe.produce import script_for

        bplus = script_for("B+", "source_stack")
        bzero = script_for("B0", "source_stack")
        unrelated = script_for("U0", "source_stack")
        hindering = script_for("H-", "source_stack")
        self.assertEqual([bplus["object"], bzero["object"], unrelated["object"], hindering["object"]], ["red"] * 4)
        self.assertEqual(bplus["red_start"], bzero["red_start"])
        self.assertNotEqual(bplus["red_start"], unrelated["red_start"])
        self.assertLess(bplus["destination_z"], bzero["destination_z"])
        self.assertEqual(bzero["destination_z"], hindering["destination_z"])

    def test_initial_blocker_sits_on_blue_source(self):
        from experiments.prerequisite_probe.probe import make_env
        from experiments.prerequisite_probe.produce import actor_pos

        env = make_env("source_stack", "blocked")
        try:
            env.reset(seed=20261004)
            red, blue = actor_pos(env.unwrapped.red), actor_pos(env.unwrapped.blue)
            self.assertLess(abs(red[0] - blue[0]), .002)
            self.assertLess(abs(red[1] - blue[1]), .002)
            self.assertGreater(red[2] - blue[2], .03)
        finally:
            env.close()


if __name__ == "__main__":
    unittest.main()

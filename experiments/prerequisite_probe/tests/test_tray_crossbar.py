"""Static gate checks for a removable bridge across the tray opening."""

import unittest


class TrayCrossbarDesignTests(unittest.TestCase):
    def test_scripts_move_one_bar_from_or_to_tray(self):
        from experiments.prerequisite_probe.produce import script_for

        specs = {key: script_for(key, "tray_crossbar")
                 for key in ("B+", "B0", "U0", "H-", "G+", "N0")}
        self.assertEqual([specs[k]["object"] for k in ("B+", "B0", "U0", "H-")],
                         ["red"] * 4)
        self.assertEqual(specs["B+"]["red_start"], specs["B0"]["red_start"])
        self.assertNotEqual(specs["B+"]["red_start"], specs["H-"]["red_start"])
        self.assertEqual(specs["B0"]["destination_z"], specs["H-"]["destination_z"])
        self.assertEqual(specs["G+"]["object"], "blue")
        self.assertIsNone(specs["N0"]["object"])

    def test_bar_initially_spans_tray_landing_area(self):
        from experiments.prerequisite_probe.probe import make_env, SCENE_LAYOUTS
        from experiments.prerequisite_probe.produce import actor_pos

        env = make_env("tray_crossbar", "blocked")
        try:
            env.reset(seed=20261004)
            red = actor_pos(env.unwrapped.red)
            tray_xy = SCENE_LAYOUTS["tray_crossbar"]["tray"]
            self.assertLess(abs(red[0] - tray_xy[0]), .002)
            self.assertLess(abs(red[1] - tray_xy[1]), .002)
            self.assertGreater(red[2], .055)
        finally:
            env.close()


if __name__ == "__main__":
    unittest.main()

import unittest


class ProbeProtocolTests(unittest.TestCase):
    def test_fixed_sample_grid_is_fifteen_seconds(self):
        from experiments.prerequisite_probe.probe import sample_indices

        self.assertEqual(sample_indices(30, 15), list(range(0, 450, 30)))

    def test_narrow_scene_has_a_roof_and_single_front_opening(self):
        from experiments.prerequisite_probe.probe import geometry

        parts = geometry("narrow")
        names = {part[0] for part in parts}
        self.assertIn("left_wall", names)
        self.assertIn("right_wall", names)
        self.assertIn("rear_wall", names)
        self.assertTrue(any(name.startswith("roof_") for name in names))
        self.assertNotIn("front_wall", names)

    def test_snapshot_signature_changes_with_actor_state(self):
        from experiments.prerequisite_probe.probe import snapshot_signature

        one = {"cube": [1.0, 2.0, 3.0], "robot": [0.0]}
        two = {"cube": [1.0, 2.0, 4.0], "robot": [0.0]}
        self.assertEqual(snapshot_signature(one), snapshot_signature(one.copy()))
        self.assertNotEqual(snapshot_signature(one), snapshot_signature(two))

    def test_panda_ik_reaches_cell_pick_and_place_points(self):
        import numpy as np
        from experiments.prerequisite_probe.probe import PandaIK

        ik = PandaIK()
        for xyz in ((.12, -.12, .17), (.12, -.12, .073),
                    (-.09, .12, .16), (-.09, .12, .035)):
            q, error = ik.solve(np.asarray(xyz), ik.home_q)
            self.assertLess(error, .015, (xyz, error, q))

    def test_prepare_videos_never_select_blue_cube(self):
        from experiments.prerequisite_probe.produce import script_for

        for condition in ("B+", "B0", "U0", "H-"):
            script = script_for(condition)
            self.assertEqual(script["object"], "red")
            self.assertLessEqual(script["end_time"], 12)
        self.assertEqual(script_for("G+")["object"], "blue")
        self.assertIsNone(script_for("N0")["object"])

    def test_joint_action_has_one_gripper_command(self):
        import numpy as np
        from experiments.prerequisite_probe.produce import action_at

        q = np.zeros(7)
        self.assertEqual(action_at(0.5, [(0, q, .04), (1, q, 0)]).shape, (8,))

    def test_effective_red_removal_physically_opens_cell(self):
        import copy
        import tempfile
        from pathlib import Path
        from experiments.prerequisite_probe.probe import make_env
        from experiments.prerequisite_probe.produce import record_case

        env = make_env("cell", "blocked")
        try:
            env.reset(seed=20261004)
            initial = copy.deepcopy(env.unwrapped.get_state_dict())
            with tempfile.TemporaryDirectory() as directory:
                result = record_case(env, "B+", Path(directory), initial, render=False)
            self.assertGreater(result["red_post"][1], .05)
            self.assertLess(abs(result["blue_post"][1] - result["blue_pre"][1]), .005)
        finally:
            env.close()

    def test_blue_only_continuation_succeeds_after_Bplus_but_not_B0(self):
        import copy
        import tempfile
        from pathlib import Path
        from experiments.prerequisite_probe.probe import PandaIK, make_env
        from experiments.prerequisite_probe.produce import record_case, run_blue_continuation

        env = make_env("cell", "blocked")
        try:
            env.reset(seed=20261004)
            initial = copy.deepcopy(env.unwrapped.get_state_dict())
            ik = PandaIK()
            with tempfile.TemporaryDirectory() as directory:
                record_case(env, "B+", Path(directory), initial, render=False, ik=ik)
                opened = copy.deepcopy(env.unwrapped.get_state_dict())
                record_case(env, "B0", Path(directory), initial, render=False, ik=ik)
                still_blocked = copy.deepcopy(env.unwrapped.get_state_dict())
            self.assertTrue(run_blue_continuation(env, opened, ik, seed=0)["success"])
            self.assertFalse(run_blue_continuation(env, still_blocked, ik, seed=0)["success"])
        finally:
            env.close()


if __name__ == "__main__":
    unittest.main()

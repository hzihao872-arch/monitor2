import unittest

from experiments.prerequisite_probe.fresh_prerequisite.scenes import make_env


class SceneSmokeTests(unittest.TestCase):
    def test_both_mechanisms_have_renderable_fixed_snapshots(self):
        for mechanism in ("access_gate", "support_surface"):
            for start in ("blocked", "open"):
                with self.subTest(mechanism=mechanism, start=start):
                    env = make_env(mechanism, start)
                    try:
                        env.reset(seed=20261006)
                        frame = env.render().cpu().numpy()[0]
                        self.assertEqual(frame.shape, (480, 640, 3))
                        self.assertEqual(env.unwrapped.mechanism, mechanism)
                        self.assertEqual(env.unwrapped.start_state, start)
                        self.assertIn("blue_cube", env.unwrapped.get_state_dict()["actors"])
                    finally:
                        env.close()


if __name__ == "__main__":
    unittest.main()

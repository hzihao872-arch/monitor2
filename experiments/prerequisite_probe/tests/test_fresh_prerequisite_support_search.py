import unittest

from experiments.prerequisite_probe.fresh_prerequisite.support_surface import search_static_counterexamples


class SupportSearchTests(unittest.TestCase):
    def test_search_challenges_edges_and_tilts_without_blocked_terminal(self):
        report = search_static_counterexamples(trials=1000, seed=20261006)
        self.assertEqual(report["trials"], 1000)
        self.assertGreater(report["fully_inside_candidates"], 0)
        self.assertEqual(report["blocked_supported_candidates"], 0)
        self.assertGreater(report["open_supported_candidates"], 0)
        self.assertTrue(report["tilted_poses_tested"])


if __name__ == "__main__":
    unittest.main()

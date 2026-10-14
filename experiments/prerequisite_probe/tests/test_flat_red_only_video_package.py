"""Physical and branch contracts for the no-yellow red-only development set."""

import unittest
import json
from pathlib import Path
import tempfile


BLOCKED = {"blue": [-0.13, -0.13, 0.023], "red": [0.18, 0.10, 0.018]}
OPEN = {"blue": [-0.13, -0.13, 0.023], "red": [0.02, 0.18, 0.018]}
U0_END = {"blue": OPEN["blue"], "red": [-0.14, 0.10, 0.018]}


class RedOnlyContractTests(unittest.TestCase):
    def test_branch_membership_and_u0_red_motion(self):
        from experiments.prerequisite_probe.flat_red_only_video_package import (
            U0_RED_DEST_XY, branch_state, audit_condition,
        )

        self.assertEqual([branch_state(c) for c in ("B+", "B0", "U0", "H-", "G+", "N0")],
                         ["blocked", "blocked", "open", "open", "open", "open"])
        self.assertAlmostEqual(U0_RED_DEST_XY[0], -0.14)
        self.assertAlmostEqual(U0_RED_DEST_XY[1], 0.10)
        trajectory = [OPEN["red"], [-0.06, 0.14, 0.20], U0_END["red"]]
        self.assertEqual(audit_condition("U0", OPEN, U0_END, False, trajectory), [])

    def test_u0_rejects_still_red_or_intermediate_target_occupancy(self):
        from experiments.prerequisite_probe.flat_red_only_video_package import audit_condition

        still = audit_condition("U0", OPEN, OPEN, False, [OPEN["red"]] * 3)
        self.assertIn("u0_red_not_moved", still)
        crossed = audit_condition("U0", OPEN, U0_END, False,
                                  [OPEN["red"], BLOCKED["red"], U0_END["red"]])
        self.assertIn("u0_red_overlapped_target_during_route", crossed)

    def test_other_classes_require_their_intended_endpoint(self):
        from experiments.prerequisite_probe.flat_red_only_video_package import audit_condition

        self.assertEqual(audit_condition("B+", BLOCKED, OPEN, False,
                                         [BLOCKED["red"], OPEN["red"]]), [])
        self.assertIn("red_not_blocking_at_end",
                      audit_condition("B0", BLOCKED, OPEN, False,
                                      [BLOCKED["red"], OPEN["red"]]))
        self.assertEqual(audit_condition("H-", OPEN, BLOCKED, False,
                                         [OPEN["red"], BLOCKED["red"]]), [])
        goal = {"blue": [0.18, 0.10, 0.023], "red": OPEN["red"]}
        self.assertEqual(audit_condition("G+", OPEN, goal, True,
                                         [OPEN["red"], OPEN["red"]]), [])
        self.assertEqual(audit_condition("N0", OPEN, OPEN, False,
                                         [OPEN["red"], OPEN["red"]]), [])

    def test_u0_real_route_keeps_target_open(self):
        from experiments.prerequisite_probe.flat_red_only_video_package import probe_condition

        record = probe_condition("U0")
        self.assertEqual(len(record["trajectory"]), 450)
        self.assertEqual(record["admission_issues"], [])
        self.assertGreater(record["red_displacement_xy_m"], 0.15)
        self.assertFalse(record["terminal"]["success"])
        self.assertNotIn("yellow", record["start"])

    def test_six_clip_candidate_has_two_shared_starts_and_isolated_truth(self):
        from experiments.prerequisite_probe.flat_red_only_video_package import run_candidate

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "new_candidate"
            result = run_candidate(output)
            self.assertEqual(result["status"], "candidate_pending_independent_review")
            inputs = output / "candidate_input"
            truth = output / "truth"
            self.assertEqual(len(list(inputs.glob("clip_*.mp4"))), 6)
            self.assertFalse((inputs / "manifest.jsonl").exists())
            mapping = json.loads((truth / "mapping_and_trajectories.json").read_text())
            records = mapping["records"]
            self.assertEqual(len(records), 6)
            self.assertEqual(mapping["failures"], [])
            self.assertEqual({r["initial_state_sha256"] for r in records
                              if r["condition"] in ("B+", "B0")},
                             {mapping["blocked_snapshot_sha256"]})
            self.assertEqual({r["initial_state_sha256"] for r in records
                              if r["condition"] not in ("B+", "B0")},
                             {mapping["open_snapshot_sha256"]})
            self.assertTrue(all(not r["admission_issues"] for r in records))
            self.assertTrue(all("yellow" not in r["start"] for r in records))
            self.assertEqual([r["condition"] for r in records if r["terminal"]["success"]],
                             ["G+"])
            media = (inputs / "media_hashes.json").read_text()
            self.assertNotIn('"condition"', media)
            self.assertNotIn('"truth"', media)
            with self.assertRaises(FileExistsError):
                run_candidate(output)


if __name__ == "__main__":
    unittest.main()

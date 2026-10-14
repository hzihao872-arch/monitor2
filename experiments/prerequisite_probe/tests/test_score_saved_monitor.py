"""Offline scorer keeps invalid output and abstentions in the denominator."""

import unittest


class ScoreSavedMonitorTests(unittest.TestCase):
    def test_budget_uses_two_model_calls_for_hybrid_and_direct_review(self):
        from experiments.prerequisite_probe.score_saved_monitor import summarize

        labels = {"0001.mp4": "B+"}
        rows = [{"kind": "model_call", "video": "0001.mp4", "method": method,
                 "validity": "invalid", "errors": ["test"],
                 "input_tokens": 100, "output_tokens": 20, "elapsed_ms": 1000,
                 "peak_vram_bytes": 1000}
                for method in ("D", "P", "F", "D2_review")]
        rows.append({"kind": "hybrid", "video": "0001.mp4", "direction": "invalid"})
        self.assertEqual(summarize(rows, labels, "H0")["budget"]["calls"], 2)
        self.assertEqual(summarize(rows, labels, "D2_review")["budget"]["input_tokens"], 200)

    def test_counts_all_cases_and_pairwise_order(self):
        from experiments.prerequisite_probe.score_saved_monitor import summarize

        labels = {f"{i:04d}.mp4": case for i, case in enumerate(
            ("B+", "B0", "U0", "H-", "G+", "N0"), start=1)}
        directions = ("positive", "zero", "zero", "negative", "positive", "zero")
        rows = [{"kind": "hybrid", "video": video, "direction": direction,
                 "requires_evidence_audit": True}
                for video, direction in zip(labels, directions)]
        result = summarize(rows, labels, "H0")
        self.assertEqual(result["total"], 6)
        self.assertEqual(result["correct"], 6)
        self.assertEqual(result["pairwise"], {"B+>B0": True, "B+>U0": True,
                                              "H-<N0": True, "G+>N0": True})
        self.assertEqual(result["evidence_audit"], "pending")

    def test_invalid_and_uncertain_remain_in_denominator(self):
        from experiments.prerequisite_probe.score_saved_monitor import summarize

        labels = {"0001.mp4": "B+", "0002.mp4": "B0", "0003.mp4": "U0"}
        rows = [
            {"kind": "model_call", "video": "0001.mp4", "method": "D",
             "validity": "invalid", "errors": ["json_parse:ValueError"]},
            {"kind": "model_call", "video": "0002.mp4", "method": "D",
             "validity": "valid", "record": {"goal_observed_complete": "false",
                 "goal_before_complete": "false",
                 "before_satisfied": "unknown", "after_satisfied": "unknown",
                 "comparison": "unknown"}},
        ]
        result = summarize(rows, labels, "D")
        self.assertEqual(result["total"], 3)
        self.assertEqual(result["invalid"], 1)
        self.assertEqual(result["uncertain"], 1)
        self.assertEqual(result["missing"], 1)
        self.assertIsNone(result["pairwise"]["B+>B0"])


if __name__ == "__main__":
    unittest.main()

"""Contract checks that prevent a server run from silently crediting bad output."""

import json
import unittest


class MonitorContractTests(unittest.TestCase):
    def record(self, before="false", after="true", comparison="better", goal="false", evidence=None,
               goal_before="false"):
        return {
            "goal_observed_complete": goal,
            "goal_before_complete": goal_before,
            "relation": "the goal location is available",
            "before_satisfied": before,
            "after_satisfied": after,
            "comparison": comparison,
            "event_interval_s": [8, 10],
            "evidence": evidence or [
                {"second": 0, "region": "goal location", "supports": "occupied"},
                {"second": 14, "region": "goal location", "supports": "clear"},
            ],
            "alternative_route": "none visible",
            "disconfirming_observation": "could not see another opening",
            "uncertainty_reason": None,
        }

    def test_rejects_unsupplied_evidence_frame(self):
        from experiments.prerequisite_probe.monitor_contract import parse_and_validate

        r = self.record(evidence=[{"second": 1, "region": "tray", "supports": "clear"}])
        result = parse_and_validate(json.dumps(r), inspected_seconds={0, 2, 4, 6, 8, 10, 12, 14})
        self.assertEqual(result["validity"], "invalid")
        self.assertIn("unsupplied_evidence_frame", result["errors"])

    def test_marks_self_contradictory_change_invalid(self):
        from experiments.prerequisite_probe.monitor_contract import parse_and_validate

        r = self.record(before="true", after="true", comparison="better")
        result = parse_and_validate(json.dumps(r), inspected_seconds={0, 14})
        self.assertEqual(result["validity"], "invalid")
        self.assertIn("self_contradiction", result["errors"])

    def test_requires_both_before_and_after_evidence(self):
        from experiments.prerequisite_probe.monitor_contract import parse_and_validate

        r = self.record(evidence=[{"second": 0, "region": "tray", "supports": "occupied"}])
        result = parse_and_validate(json.dumps(r), inspected_seconds={0, 14})
        self.assertEqual(result["validity"], "invalid")
        self.assertIn("missing_after_evidence", result["errors"])

    def test_already_complete_goal_has_zero_new_progress(self):
        from experiments.prerequisite_probe.monitor_contract import event_direction, parse_and_validate

        r = self.record(before="true", after="true", comparison="same", goal="true", goal_before="true")
        result = parse_and_validate(json.dumps(r), inspected_seconds={0, 14})
        self.assertEqual(result["validity"], "valid")
        self.assertEqual(event_direction(result["record"]), "zero")

    def test_uncertain_initial_goal_cannot_claim_new_completion(self):
        from experiments.prerequisite_probe.monitor_contract import event_direction, parse_and_validate

        r = self.record(before="true", after="true", comparison="same",
                        goal_before="unknown", goal="true")
        result = parse_and_validate(json.dumps(r), {0, 14})
        self.assertEqual(result["validity"], "valid")
        self.assertEqual(event_direction(result["record"]), "uncertain")

    def test_goal_completion_can_coexist_with_unchanged_prerequisite(self):
        from experiments.prerequisite_probe.monitor_contract import parse_and_validate, event_direction

        r = self.record(before="true", after="true", comparison="same",
                        goal_before="false", goal="true")
        result = parse_and_validate(json.dumps(r), {0, 14})
        self.assertEqual(result["validity"], "valid")
        self.assertEqual(event_direction(result["record"]), "positive")

    def test_goal_completion_does_not_excuse_relation_contradiction(self):
        from experiments.prerequisite_probe.monitor_contract import parse_and_validate

        r = self.record(before="true", after="true", comparison="better",
                        goal_before="false", goal="true")
        result = parse_and_validate(json.dumps(r), {0, 14})
        self.assertIn("self_contradiction", result["errors"])

    def test_malformed_field_types_are_recorded_without_crashing(self):
        from experiments.prerequisite_probe.monitor_contract import parse_and_validate

        for field, value in (("goal_observed_complete", []),
                             ("goal_before_complete", []),
                             ("before_satisfied", {}),
                             ("after_satisfied", ["true"]),
                             ("comparison", {"better": True})):
            with self.subTest(field=field):
                record = self.record()
                record[field] = value
                result = parse_and_validate(json.dumps(record), {0, 14})
                self.assertEqual(result["validity"], "invalid")
                self.assertIn("bad_" + field, result["errors"])

    def test_four_preparation_directions(self):
        from experiments.prerequisite_probe.monitor_contract import parse_and_validate, event_direction

        cases = [
            ("false", "true", "better", "positive"),
            ("false", "false", "same", "zero"),
            ("true", "true", "same", "zero"),
            ("true", "false", "worse", "negative"),
        ]
        for before, after, comparison, expected in cases:
            with self.subTest(expected=expected):
                item = parse_and_validate(json.dumps(self.record(before, after, comparison)), {0, 14})
                self.assertEqual(item["validity"], "valid")
                self.assertEqual(event_direction(item["record"]), expected)

    def test_progress_keeps_transition_interval_unknown(self):
        from experiments.prerequisite_probe.monitor_contract import render_progress

        points = render_progress(self.record(), alpha=25, seconds=15)
        self.assertEqual(len(points), 15)
        self.assertEqual(points[0]["point"], 0)
        self.assertIsNone(points[9]["point"])
        self.assertEqual(points[14]["point"], 25)

    def test_unknown_goal_completion_keeps_progress_unresolved(self):
        from experiments.prerequisite_probe.monitor_contract import render_progress

        points = render_progress(self.record(before="true", after="true",
                                             comparison="same", goal="unknown"))
        self.assertEqual(points[0]["point"], 25)
        self.assertIsNone(points[14]["point"])
        self.assertEqual((points[14]["lower"], points[14]["upper"]), (25, 100))

    def test_invalid_call_can_emit_all_unknown_points(self):
        from experiments.prerequisite_probe.monitor_contract import unknown_progress

        points = unknown_progress()
        self.assertEqual(len(points), 15)
        self.assertEqual(points[14], {"second": 14, "point": None,
                                      "lower": 0, "upper": 100})

    def test_hybrid_abstains_when_relation_and_feasibility_disagree(self):
        from experiments.prerequisite_probe.monitor_contract import combine_hybrid, parse_and_validate

        p = parse_and_validate(json.dumps(self.record()), {0, 14})
        f = parse_and_validate(json.dumps(self.record("false", "false", "same")), {0, 14})
        h = combine_hybrid(p, f)
        self.assertEqual(h["direction"], "uncertain")
        self.assertEqual(h["reason"], "P_F_conflict")

    def test_hybrid_has_conservative_per_second_curve_when_both_agree(self):
        from experiments.prerequisite_probe.monitor_contract import combine_hybrid, hybrid_progress, parse_and_validate, render_progress

        p = parse_and_validate(json.dumps(self.record()), {0, 14})
        f_record = self.record()
        f_record["event_interval_s"] = [7, 11]
        f = parse_and_validate(json.dumps(f_record), {0, 14})
        hybrid = combine_hybrid(p, f)
        self.assertEqual(hybrid["direction"], "positive")
        self.assertEqual(hybrid["progress_record"]["event_interval_s"], [7, 11])
        points = render_progress(hybrid["progress_record"])
        self.assertIsNone(points[9]["point"])
        self.assertEqual(points[14]["point"], 25)
        self.assertEqual(hybrid_progress(hybrid), points)

    def test_hybrid_abstains_on_goal_completion_disagreement(self):
        from experiments.prerequisite_probe.monitor_contract import combine_hybrid, hybrid_progress, parse_and_validate

        p = parse_and_validate(json.dumps(self.record(goal="true")), {0, 14})
        f = parse_and_validate(json.dumps(self.record(goal="false")), {0, 14})
        hybrid = combine_hybrid(p, f)
        self.assertEqual(hybrid["direction"], "uncertain")
        points = hybrid_progress(hybrid)
        self.assertEqual(len(points), 15)
        self.assertTrue(all(point["point"] is None for point in points))

    def test_hybrid_abstains_on_initial_goal_disagreement(self):
        from experiments.prerequisite_probe.monitor_contract import combine_hybrid, parse_and_validate

        p = parse_and_validate(json.dumps(self.record(goal_before="false")), {0, 14})
        f = parse_and_validate(json.dumps(self.record(goal_before="unknown")), {0, 14})
        self.assertEqual(combine_hybrid(p, f)["direction"], "uncertain")


if __name__ == "__main__":
    unittest.main()

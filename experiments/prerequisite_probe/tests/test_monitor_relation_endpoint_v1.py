"""Common two-call protocol; fixtures test the deterministic interface only."""

import json
import unittest


class RelationEndpointV1Tests(unittest.TestCase):
    def record(self, before="true", after="true", comparison="same", goal_after="false"):
        return {
            "goal_before_complete": "false", "goal_observed_complete": goal_after,
            "candidate_object": "visible non-goal object", "region_kind": "destination",
            "region": "goal receptacle opening", "relation": "opening is clear for goal object",
            "before_satisfied": before, "after_satisfied": after, "comparison": comparison,
            "event_interval_s": [0, 14],
            "evidence": [{"second": 0, "region": "goal opening", "supports": "opening state at start"},
                         {"second": 14, "region": "goal opening", "supports": "opening state at end"}],
            "alternative_route": "unknown", "disconfirming_observation": "none visible",
            "uncertainty_reason": None,
        }

    def test_semantic_fixture_directions(self):
        from experiments.prerequisite_probe.monitor_relation_endpoint_v1 import parse_record

        examples = [
            ("true", "true", "same", "false", "zero"),     # irrelevant move
            ("false", "false", "same", "false", "zero"),   # return to blocker
            ("true", "false", "worse", "false", "negative"),
            ("true", "true", "same", "true", "positive"),  # visible goal completion
        ]
        for before, after, comparison, goal_after, direction in examples:
            with self.subTest(direction=direction):
                output = parse_record(json.dumps(self.record(before, after, comparison, goal_after)))
                self.assertEqual(output["validity"], "valid")
                self.assertEqual(output["direction"], direction)

    def test_missing_object_binding_is_invalid_for_both_arms(self):
        from experiments.prerequisite_probe.monitor_relation_endpoint_v1 import parse_record

        record = self.record()
        record["candidate_object"] = ""
        output = parse_record(json.dumps(record))
        self.assertEqual(output["validity"], "invalid")
        self.assertIn("empty_candidate_object", output["errors"])

    def test_candidate_relation_conflict_abstains(self):
        from experiments.prerequisite_probe.monitor_relation_endpoint_v1 import pair_result

        first, second = self.record(), self.record()
        second["relation"] = "a different relation"
        result = pair_result("candidate", json.dumps(first), json.dumps(second))
        self.assertEqual(result["direction"], "uncertain")
        self.assertEqual(result["reason"], "relation_changed_between_calls")

    def test_existing_contract_known_states_unknown_comparison_abstains(self):
        from experiments.prerequisite_probe.monitor_relation_endpoint_v1 import parse_record

        record = self.record("false", "true", "unknown")
        result = parse_record(json.dumps(record))
        self.assertEqual(result["validity"], "valid")
        self.assertEqual(result["direction"], "uncertain")

    def test_direct_review_can_correct_its_first_relation(self):
        from experiments.prerequisite_probe.monitor_relation_endpoint_v1 import pair_result

        first, second = self.record(), self.record()
        second["relation"] = "corrected goal relation"
        result = pair_result("D2", json.dumps(first), json.dumps(second))
        self.assertEqual(result["direction"], "zero")

    def test_prompts_have_same_schema_and_no_condition_key(self):
        from experiments.prerequisite_probe.monitor_relation_endpoint_v1 import prompt_for

        goal = "Move the target into its receptacle."
        for arm in ("D2", "candidate"):
            for pass_number in (1, 2):
                prompt = prompt_for(arm, pass_number, goal, prior="{}")
                self.assertIn("candidate_object", prompt)
                self.assertIn("region_kind", prompt)
                self.assertIn(goal, prompt)
                self.assertNotIn("B+", prompt)
                self.assertNotIn("red bar", prompt)


if __name__ == "__main__":
    unittest.main()

"""The format fix is syntax only and discloses missing semantic claims."""

import json
import unittest

from experiments.prerequisite_probe.monitor_relation_endpoint_v1_contract_v2 import parse_record


class ContractV2Tests(unittest.TestCase):
    def test_boolean_null_singleton_support_is_recorded(self):
        raw = json.dumps({
            "candidate_object": "red block", "region_kind": "destination",
            "region": "green square", "relation": "clear for placement",
            "goal_before_complete": False, "goal_observed_complete": False,
            "before_satisfied": False, "after_satisfied": True,
            "comparison": "better", "alternative_route": None,
            "disconfirming_observation": None, "uncertainty_reason": None,
            "event_interval_s": [0, 14],
            "evidence": [
                {"second": 0, "region": "green square", "supports": ["red block occupies it"]},
                {"second": 14, "region": "green square", "supports": ["red block is clear"]},
            ],
        })
        result = parse_record(raw)
        self.assertEqual(result["validity"], "valid")
        self.assertEqual(result["direction"], "positive")
        self.assertEqual(result["raw"], raw)
        self.assertEqual(result["record"]["alternative_route"], "not stated in model output")
        self.assertIn("missing_claim:alternative_route", result["format_repairs"])
        self.assertIn("singleton_support:0", result["format_repairs"])

    def test_real_semantic_contradiction_stays_invalid(self):
        raw = json.dumps({
            "candidate_object": "red block", "region_kind": "destination",
            "region": "green square", "relation": "clear for placement",
            "goal_before_complete": False, "goal_observed_complete": False,
            "before_satisfied": False, "after_satisfied": True,
            "comparison": "worse", "alternative_route": "unknown",
            "disconfirming_observation": "none visible", "uncertainty_reason": None,
            "event_interval_s": [0, 14],
            "evidence": [
                {"second": 0, "region": "green square", "supports": "red block occupies it"},
                {"second": 14, "region": "green square", "supports": "red block is clear"},
            ],
        })
        result = parse_record(raw)
        self.assertEqual(result["validity"], "invalid")
        self.assertIn("self_contradiction", result["errors"])


if __name__ == "__main__":
    unittest.main()

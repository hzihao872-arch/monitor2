"""Versioned syntax normalization for the single-scene pilot.

The v1 record semantics and direction rules remain unchanged. Keep every raw
response and disclose each normalization; a missing free-text claim is never
silently treated as positive evidence.
"""

from __future__ import annotations

import json

from .monitor_contract import event_direction, parse_and_validate as parse_v1


TRI_FIELDS = ("goal_before_complete", "goal_observed_complete",
              "before_satisfied", "after_satisfied")
TEXT_FIELDS = ("alternative_route", "disconfirming_observation")
MISSING_CLAIM = "not stated in model output"


def parse_and_validate(raw: str, inspected_seconds: set[int]) -> dict:
    """Normalize JSON types only, then apply the unmodified v1 validator."""
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        result = parse_v1(raw, inspected_seconds)
        result["format_repairs"] = []
        return result
    if not isinstance(parsed, dict):
        result = parse_v1(raw, inspected_seconds)
        result["format_repairs"] = []
        return result

    record = dict(parsed)
    repairs = []
    for field in TRI_FIELDS:
        if type(record.get(field)) is bool:
            record[field] = "true" if record[field] else "false"
            repairs.append(f"bool_to_tri:{field}")
    for field in TEXT_FIELDS:
        if field in record and record[field] is None:
            record[field] = MISSING_CLAIM
            repairs.append(f"missing_claim:{field}")
    if isinstance(record.get("evidence"), list):
        evidence = []
        for index, item in enumerate(record["evidence"]):
            if isinstance(item, dict) and isinstance(item.get("supports"), list) and len(item["supports"]) == 1 and isinstance(item["supports"][0], str):
                item = {**item, "supports": item["supports"][0]}
                repairs.append(f"singleton_support:{index}")
            evidence.append(item)
        record["evidence"] = evidence
    result = parse_v1(json.dumps(record, ensure_ascii=False), inspected_seconds)
    result["raw"] = raw
    result["format_repairs"] = repairs
    return result

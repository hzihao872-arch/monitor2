"""Shared, label-free Monitor response validation and progress rendering.

This module has no model, video, oracle, or case-map imports. It never reads
ground truth. Structural agreement from P/F is provisional until evidence is
audited; it must not be described as a physical causal proof.
"""

from __future__ import annotations

import json
from typing import Any


TRI = {"true", "false", "unknown"}
COMPARISONS = {"better", "same", "worse", "unknown"}
FIELDS = {
    "goal_before_complete", "goal_observed_complete", "relation", "before_satisfied", "after_satisfied",
    "comparison", "event_interval_s", "evidence", "alternative_route",
    "disconfirming_observation", "uncertainty_reason",
}


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _one_of(value: Any, choices: set[str]) -> bool:
    return isinstance(value, str) and value in choices


def parse_and_validate(raw: str, inspected_seconds: set[int]) -> dict:
    """Return raw output, parsed record, and every structural/logical error."""
    result = {"raw": raw, "record": None, "errors": [], "validity": "invalid"}
    try:
        record = json.loads(raw)
    except (TypeError, ValueError) as exc:
        result["errors"].append(f"json_parse:{type(exc).__name__}")
        return result
    if not isinstance(record, dict):
        result["errors"].append("not_object")
        return result
    result["record"] = record
    missing = FIELDS - record.keys()
    if missing:
        result["errors"].append("missing_fields:" + ",".join(sorted(missing)))
        return result
    for field in ("goal_before_complete", "goal_observed_complete",
                  "before_satisfied", "after_satisfied"):
        if not _one_of(record[field], TRI):
            result["errors"].append("bad_" + field)
    if not _one_of(record["comparison"], COMPARISONS):
        result["errors"].append("bad_comparison")
    for field in ("relation", "alternative_route", "disconfirming_observation"):
        if not _nonempty(record[field]):
            result["errors"].append("empty_" + field)
    if record["uncertainty_reason"] is not None and not _nonempty(record["uncertainty_reason"]):
        result["errors"].append("bad_uncertainty_reason")
    interval = record["event_interval_s"]
    if (not isinstance(interval, list) or len(interval) != 2 or
            any(type(v) is not int or not 0 <= v <= 14 for v in interval) or
            interval[0] >= interval[1]):
        result["errors"].append("bad_event_interval")
    evidence = record["evidence"]
    if not isinstance(evidence, list) or not evidence:
        result["errors"].append("missing_evidence")
    else:
        cited_seconds = []
        for item in evidence:
            if not isinstance(item, dict) or not {"second", "region", "supports"} <= item.keys():
                result["errors"].append("bad_evidence_item")
                continue
            if type(item["second"]) is not int or item["second"] not in inspected_seconds:
                result["errors"].append("unsupplied_evidence_frame")
            else:
                cited_seconds.append(item["second"])
            if not _nonempty(item["region"]) or not _nonempty(item["supports"]):
                result["errors"].append("empty_evidence_claim")
        if ("bad_event_interval" not in result["errors"] and
                _one_of(record["comparison"], COMPARISONS - {"unknown"}) and
                all(_one_of(record[field], TRI - {"unknown"}) for field in
                    ("before_satisfied", "after_satisfied"))):
            if not any(t <= interval[0] for t in cited_seconds):
                result["errors"].append("missing_before_evidence")
            if not any(t >= interval[1] for t in cited_seconds):
                result["errors"].append("missing_after_evidence")
    if (all(_one_of(record[field], TRI) for field in
            ("before_satisfied", "after_satisfied")) and
            _one_of(record["comparison"], COMPARISONS)):
        b, a, c = record["before_satisfied"], record["after_satisfied"], record["comparison"]
        implied = {("false", "true"): "better", ("true", "false"): "worse",
                   ("false", "false"): "same", ("true", "true"): "same"}
        if (b, a) in implied and c not in (implied[(b, a)], "unknown"):
            result["errors"].append("self_contradiction")
        if "unknown" in (b, a) and c != "unknown":
            result["errors"].append("unsupported_comparison")
    result["errors"] = list(dict.fromkeys(result["errors"]))
    if not result["errors"]:
        result["validity"] = "valid"
    return result


def event_direction(record: dict) -> str:
    goal_before = record["goal_before_complete"]
    goal_after = record["goal_observed_complete"]
    if goal_before == "false" and goal_after == "true":
        return "positive"
    if goal_before == "true" and goal_after == "false":
        return "negative"
    if goal_before == "true" and goal_after == "true":
        return "zero"
    if "unknown" in (goal_before, goal_after):
        return "uncertain"
    before, after = record["before_satisfied"], record["after_satisfied"]
    if "unknown" in (before, after) or record["comparison"] == "unknown":
        return "uncertain"
    if before == "false" and after == "true" and record["comparison"] == "better":
        return "positive"
    if before == "true" and after == "false" and record["comparison"] == "worse":
        return "negative"
    if before == after and record["comparison"] == "same":
        return "zero"
    return "uncertain"


def combine_hybrid(p_result: dict, f_result: dict) -> dict:
    if p_result["validity"] != "valid" or f_result["validity"] != "valid":
        return {"direction": "invalid", "reason": "P_or_F_invalid", "requires_evidence_audit": True}
    p, f = p_result["record"], f_result["record"]
    pd, fd = event_direction(p), event_direction(f)
    if (pd != fd or pd == "uncertain" or
            p["goal_before_complete"] != f["goal_before_complete"] or
            p["goal_observed_complete"] != f["goal_observed_complete"] or
            (p["before_satisfied"], p["after_satisfied"]) !=
            (f["before_satisfied"], f["after_satisfied"])):
        return {"direction": "uncertain", "reason": "P_F_conflict", "requires_evidence_audit": True}
    progress_record = {
        "goal_before_complete": p["goal_before_complete"],
        "goal_observed_complete": p["goal_observed_complete"],
        "before_satisfied": p["before_satisfied"],
        "after_satisfied": p["after_satisfied"],
        "event_interval_s": [min(p["event_interval_s"][0], f["event_interval_s"][0]),
                             max(p["event_interval_s"][1], f["event_interval_s"][1])],
    }
    return {"direction": pd, "reason": "P_F_structural_agreement",
            "requires_evidence_audit": True,
            "relation_claims": [p["relation"], f["relation"]],
            "evidence": [*p["evidence"], *f["evidence"]],
            "progress_record": progress_record}


def render_progress(record: dict, alpha: int = 25, seconds: int = 15) -> list[dict]:
    """Render an operational evidence index, never a success probability."""
    start, end = record["event_interval_s"]
    result = []
    for t in range(seconds):
        state = record["before_satisfied"] if t <= start else record["after_satisfied"] if t >= end else "unknown"
        goal_state = record["goal_before_complete"] if t <= start else (
            record["goal_observed_complete"] if t >= end else "unknown")
        if goal_state == "true":
            point, low, high = 100, 100, 100
        elif goal_state == "unknown":
            point, low, high = None, alpha if state == "true" else 0, 100
        elif state == "true":
            point, low, high = alpha, alpha, alpha
        elif state == "false":
            point, low, high = 0, 0, 0
        else:
            point, low, high = None, 0, alpha
        result.append({"second": t, "point": point, "lower": low, "upper": high})
    return result


def unknown_progress(seconds: int = 15) -> list[dict]:
    """Represent invalid or abstained output without inventing a score."""
    return [{"second": t, "point": None, "lower": 0, "upper": 100}
            for t in range(seconds)]


def hybrid_progress(hybrid: dict) -> list[dict]:
    """Always return a 15-second curve; abstentions have no point estimate."""
    record = hybrid.get("progress_record")
    return render_progress(record) if record is not None else unknown_progress()

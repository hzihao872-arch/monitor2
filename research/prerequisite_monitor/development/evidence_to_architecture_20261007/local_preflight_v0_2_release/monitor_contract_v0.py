"""Version 0.1.1 structural contract and deterministic readout; no model inference.

This code contains no scene names, condition labels, expected answers, or truth paths.
It does not estimate physical feasibility; it audits an upstream claim about it.
"""

from __future__ import annotations

import json
from typing import Any


VERSION = "0.1.1"
TRI = {"true", "false", "unknown"}
ROUTE = {"possible", "blocked", "unknown"}
SUPPORT = {"supported", "refuted", "unknown"}
DIRECTIONS = {"beneficial", "unchanged", "harmful", "completed", "unknown"}


def _map3(value: Any, name: str, allowed: set[str]) -> None:
    if not isinstance(value, dict) or set(value) != {"t0", "t_mid", "t14"}:
        raise ValueError(f"{name} must have t0,t_mid,t14")
    if any(item not in allowed for item in value.values()):
        raise ValueError(f"{name} contains an invalid enum")


def evaluate(raw: str, available_seconds: list[int]) -> dict[str, Any]:
    """Parse, validate citations, and check a claimed direction against v0.1.0 rules."""
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        return {"status": "parse_failure", "direction": None, "reason": str(exc)}
    try:
        if not isinstance(value, dict) or value.get("spec_version") != VERSION:
            raise ValueError("unsupported spec version")
        mid_second = value.get("mid_second")
        if type(mid_second) is not int or mid_second not in (7, 8) or mid_second not in available_seconds:
            raise ValueError("mid_second must be an available second 7 or 8")
        _map3(value.get("goal_done"), "goal_done", TRI)
        _map3(value.get("continuation"), "continuation", ROUTE)
        relation = value.get("candidate_relation")
        if not isinstance(relation, dict):
            raise ValueError("candidate_relation missing")
        _map3(relation.get("satisfied"), "satisfied", TRI)
        if relation.get("goal_relevance") not in SUPPORT:
            raise ValueError("goal_relevance invalid")
        alternatives = relation.get("alternative_route")
        if not isinstance(alternatives, dict) or set(alternatives) != {"t0", "t14"}:
            raise ValueError("alternative_route must have t0,t14")
        if any(item not in SUPPORT for item in alternatives.values()):
            raise ValueError("alternative_route invalid")
        for key in ("entity", "region", "predicate"):
            if relation.get(key) is not None and not isinstance(relation[key], str):
                raise ValueError(f"{key} invalid")
        if value.get("direction") not in DIRECTIONS:
            raise ValueError("direction invalid")
        if value.get("uncertainty_reason") is not None and not isinstance(value["uncertainty_reason"], str):
            raise ValueError("uncertainty_reason invalid")
        evidence = value.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            raise ValueError("evidence missing")
        seconds = set(available_seconds)
        cited = set()
        for item in evidence:
            if not isinstance(item, dict) or type(item.get("second")) is not int:
                raise ValueError("evidence second invalid")
            second = item["second"]
            if second not in seconds:
                raise ValueError(f"evidence second {second} unavailable")
            if not isinstance(item.get("region"), str) or not item["region"]:
                raise ValueError("evidence region missing")
            if not isinstance(item.get("claim"), str) or not item["claim"]:
                raise ValueError("evidence claim missing")
            cited.add(second)
        if not {0, mid_second, 14}.issubset(cited):
            raise ValueError("endpoint or middle citation missing")
    except ValueError as exc:
        return {"status": "schema_or_evidence_failure", "direction": None, "reason": str(exc)}

    done = value["goal_done"]
    route = value["continuation"]
    if done["t0"] == "false" and done["t14"] == "true":
        expected = "completed"
    elif done["t0"] == "true" and done["t14"] == "true":
        expected = "unchanged"
    elif done["t0"] == "true" and done["t14"] == "false":
        expected = "harmful"
    elif done["t0"] == "unknown" or done["t14"] == "unknown":
        expected = "unknown"
    elif "unknown" in (route["t0"], route["t14"]):
        expected = "unknown"
    elif route["t0"] == route["t14"]:
        expected = "unchanged"
    elif route["t0"] == "blocked" and route["t14"] == "possible":
        expected = "beneficial"
    else:
        expected = "harmful"

    if expected in {"beneficial", "harmful"}:
        required_alt = "t0" if expected == "beneficial" else "t14"
        if (relation["goal_relevance"] != "supported"
                or relation["alternative_route"][required_alt] != "refuted"
                or not all(relation.get(key) for key in ("entity", "region", "predicate"))):
            expected = "unknown"
    if expected == "unknown" and not value.get("uncertainty_reason"):
        return {"status": "schema_or_evidence_failure", "direction": None,
                "reason": "unknown needs uncertainty_reason"}
    if value["direction"] != expected:
        return {"status": "direction_conflict", "direction": expected,
                "claimed_direction": value["direction"], "reason": "claimed direction disagrees with fields"}
    transient = None
    if (done["t14"] == "false" and route["t0"] == route["t14"] == "blocked"
            and route["t_mid"] == "possible"):
        transient = "beneficial_then_revoked"
    elif (done["t14"] == "false" and route["t0"] == route["t14"] == "possible"
          and route["t_mid"] == "blocked"):
        transient = "harmful_then_recovered"
    return {"status": "valid", "direction": expected, "transient": transient,
            "cited_seconds": sorted(cited)}

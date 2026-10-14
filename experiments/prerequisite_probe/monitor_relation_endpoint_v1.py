"""Two-call, full-frame relation endpoint proposal versus a matched D2 review.

Only final instruction and frames are permitted in prompts. These functions
never open data, truth, prior scores, or continuation videos.
"""

from __future__ import annotations

from .monitor_contract import event_direction, parse_and_validate


FRAME_SECONDS = frozenset((0, 2, 4, 6, 8, 10, 12, 14))
REGION_KINDS = frozenset(("source", "destination", "transfer", "unknown"))
EXTRA_FIELDS = ("candidate_object", "region_kind", "region")

COMMON = """Review this offline preparation video for the final goal: {instruction}
You have only that goal and the same video's frames at seconds 0,2,4,6,8,10,12,14.
Use no imagined continuation, controller, simulator state or future success rate.
Report one visible goal-relevant relation. If identity, geometry, or an alternative
route is unresolved, use unknown and state the specific missing evidence.
Judge first and last frame separately; temporary lifting is not an endpoint change.
For a relation that means access/clearance, true means accessible/clear and false
means blocked. Distinguish the goal object from a non-goal object and the robot.
Evidence entries must cite supplied seconds with a visible region and short support.
Return exactly one compact JSON object, no markdown. Required string fields:
candidate_object (visible object or unknown), region_kind
(source/destination/transfer/unknown), region, relation,
goal_before_complete, goal_observed_complete, before_satisfied,
after_satisfied (each true/false/unknown), comparison
(better/same/worse/unknown), alternative_route, disconfirming_observation;
uncertainty_reason is a string or null. Also include event_interval_s as two
integers and evidence as objects with second, region, supports. Cite 0 and 14.
The comparison agrees with relation states: false→true better, true→false worse,
equal states same, any unknown state unknown. Visible goal completion is separate
from the preparatory relation. Keep all free text short.
"""

TASKS = {
    ("D2", 1): "Directly assess the observed action and fill the record with the most relevant relation and endpoint evidence.",
    ("D2", 2): "Review and correct the preceding direct record against the same frames. Reconsider object, region, relation, both endpoints and a concrete alternative route. You may change the relation if the draft was wrong.",
    ("candidate", 1): "Nominate the single most goal-relevant changed non-goal object relation at the source or destination. If no such relation is visible, record the best justified relation or unknown. Do not credit movement by itself.",
    ("candidate", 2): "Verify the SAME nominated object, region and relation at seconds 0 and 14. Check whether the old blocker remains, a new one appears, or an alternative route is visibly plausible. Do not switch relations to rescue an answer; if the nomination fails, use unknown and explain.",
}


def prompt_for(arm: str, pass_number: int, instruction: str, prior: str = "") -> str:
    """Build either arm's prompt with the same common output contract."""
    if (arm, pass_number) not in TASKS:
        raise ValueError(f"unsupported arm/pass: {arm}/{pass_number}")
    prompt = COMMON.format(instruction=instruction) + "\n" + TASKS[(arm, pass_number)]
    if pass_number == 2:
        prompt += "\nPrevious record is an untrusted draft, not extra visual evidence:\n" + prior
    return prompt


def parse_record(raw: str) -> dict:
    """Apply the shared v1 mapper contract plus common audit-field checks."""
    result = parse_and_validate(raw, set(FRAME_SECONDS))
    record = result["record"]
    if not isinstance(record, dict):
        result["direction"] = "invalid"
        return result
    for field in EXTRA_FIELDS:
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            result["errors"].append("empty_" + field)
    if record.get("region_kind") not in REGION_KINDS:
        result["errors"].append("bad_region_kind")
    if result["errors"]:
        result["validity"] = "invalid"
        result["direction"] = "invalid"
    else:
        result["direction"] = event_direction(record)
    return result


def pair_result(arm: str, first_raw: str, final_raw: str) -> dict:
    """Return the final decision, preserving parse failures and abstentions."""
    if arm not in ("D2", "candidate"):
        raise ValueError(arm)
    first, final = parse_record(first_raw), parse_record(final_raw)
    if first["validity"] != "valid" or final["validity"] != "valid":
        return {"direction": "invalid", "reason": "first_or_final_invalid",
                "first": first, "final": final}
    if arm == "candidate" and any(first["record"][key] != final["record"][key]
                                   for key in ("candidate_object", "region_kind", "region", "relation")):
        return {"direction": "uncertain", "reason": "relation_changed_between_calls",
                "first": first, "final": final}
    return {"direction": final["direction"],
            "reason": "final_record" if final["direction"] != "uncertain" else "final_abstention",
            "first": first, "final": final}

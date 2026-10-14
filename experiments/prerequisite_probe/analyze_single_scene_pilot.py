"""Post-seal development analysis. This is the only pilot script that reads truth."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path

from .seal_single_scene_pilot import records, verify
from .run_monitor_qwen import sha256


CONDITIONS = {"B+", "B0", "U0", "H-", "G+", "N0"}
EXPECTED = {"B+": "positive", "B0": "zero", "U0": "zero",
            "H-": "negative", "G+": "positive", "N0": "zero"}
RANK = {"negative": -1, "zero": 0, "positive": 1}
PAIRS = (("B+", "B0", 1), ("B+", "U0", 1),
         ("H-", "N0", -1), ("G+", "N0", 1))


def native_curve(values) -> dict:
    values = [float(value) for value in values]
    if len(values) != 15 or not all(math.isfinite(value) for value in values):
        raise ValueError("native curve must have 15 finite points")
    pre = statistics.median(values[:3])
    post = statistics.median(values[12:])
    action = values[2:13]
    return {"points": values, "pre_median_0_2": pre, "post_median_12_14": post,
            "post_minus_pre": post - pre, "action_peak_2_12": max(action),
            "action_trough_2_12": min(action),
            "largest_positive_step": max(b - a for a, b in zip(values, values[1:])),
            "largest_negative_step": min(b - a for a, b in zip(values, values[1:]))}


def pairwise(by_condition: dict, field: str, *, model: bool) -> dict:
    output = {}
    for left, right, sign in PAIRS:
        key = f"{left}{'>' if sign == 1 else '<'}{right}"
        a, b = by_condition.get(left), by_condition.get(right)
        if a is None or b is None or a.get("status") != "valid" or b.get("status") != "valid":
            output[key] = {"outcome": "unavailable"}
            continue
        x = RANK.get(a["direction"]) if model else a[field]
        y = RANK.get(b["direction"]) if model else b[field]
        if x is None or y is None:
            output[key] = {"outcome": "abstained"}
            continue
        delta = float(x - y)
        outcome = "tie" if abs(delta) <= 1e-8 else ("win" if delta * sign > 0 else "loss")
        output[key] = {"outcome": outcome, "difference": delta,
                       "left": x, "right": y}
    return output


def native_report(journal: Path, aliases: dict, method: str) -> dict:
    rows = records(journal)
    found = {}
    for row in rows:
        if row.get("kind") in ("native_result", "native_failure"):
            if row["video"] in found:
                raise ValueError(f"duplicate {method} result: {row['video']}")
            found[row["video"]] = row
    by_condition = {}
    for video, condition in aliases.items():
        row = found.get(video)
        if row is None:
            by_condition[condition] = {"status": "missing", "video": video}
        elif row["kind"] == "native_failure":
            by_condition[condition] = {"status": "failed", "video": video,
                                       "error": row.get("error"), "returncode": row.get("returncode")}
        else:
            try:
                curve = native_curve(row["prefix_rewards"] if method == "TOPReward" else row["progress"])
                success = (native_curve(row["success_head"]) if method == "Robometer" else None)
                by_condition[condition] = {"status": "valid", "video": video,
                                           **curve, "success_head": success,
                                           "elapsed_ms": row.get("elapsed_ms"),
                                           "prefix_token_counts": row.get("prefix_token_counts")}
            except Exception as exc:
                by_condition[condition] = {"status": "invalid", "video": video,
                                           "error": f"{type(exc).__name__}: {exc}"}
    return {"scale": "native raw; no per-video normalization",
            "semantic_trace_exposed": False, "by_condition": by_condition,
            "pairwise_delta": pairwise(by_condition, "post_minus_pre", model=False),
            "pairwise_post": pairwise(by_condition, "post_median_12_14", model=False),
            "valid_count": sum(x["status"] == "valid" for x in by_condition.values())}


def paired_report(journal: Path, aliases: dict, arm: str) -> dict:
    rows = records(journal)
    calls = {(row["video"], row["arm"], row["pass"]): row for row in rows
             if row.get("kind") == "visual_call"}
    decisions = {(row["video"], row["arm"]): row for row in rows
                 if row.get("kind") == "pair_decision"}
    by_condition = {}
    evidence_packet = []
    for video, condition in aliases.items():
        first, final = calls.get((video, arm, 1)), calls.get((video, arm, 2))
        decision = decisions.get((video, arm))
        if first is None or final is None or decision is None:
            by_condition[condition] = {"status": "missing", "video": video}
            continue
        direction = decision["direction"]
        status = ("invalid" if direction == "invalid" else
                  "abstained" if direction == "uncertain" else "valid")
        by_condition[condition] = {
            "status": status, "video": video, "direction": direction,
            "expected_direction": EXPECTED[condition],
            "direction_correct": direction == EXPECTED[condition] if status == "valid" else None,
            "first_validity": first.get("validity"), "final_validity": final.get("validity"),
            "reason": decision.get("reason"),
            "input_tokens": sum(x.get("input_tokens", 0) for x in (first, final)),
            "output_tokens": sum(x.get("output_tokens", 0) for x in (first, final)),
            "elapsed_ms": sum(x.get("elapsed_ms", 0) for x in (first, final)),
            "missing_usage_calls": sum("input_tokens" not in x for x in (first, final)),
        }
        record = final.get("record") or {}
        evidence_packet.append({
            "video": video, "condition": condition, "arm": arm,
            "direction": direction, "record": record,
            "human_audit": {"object_binding": "pending", "region_binding": "pending",
                            "relation_relevance": "pending", "endpoint_0": "pending",
                            "endpoint_14": "pending", "goal_completion": "pending",
                            "alternative_route": "pending", "cited_frame_support": "pending",
                            "first_supported_error": "pending"},
        })
    return ({"by_condition": by_condition,
             "pairwise": pairwise(by_condition, "direction", model=True),
             "valid_count": sum(x["status"] == "valid" for x in by_condition.values()),
             "abstain_count": sum(x["status"] == "abstained" for x in by_condition.values()),
             "invalid_or_missing_count": sum(x["status"] in ("invalid", "missing")
                                             for x in by_condition.values()),
             "budget": {key: sum(x.get(key, 0) for x in by_condition.values())
                        for key in ("input_tokens", "output_tokens", "elapsed_ms",
                                    "missing_usage_calls")}}, evidence_packet)


def analyze(raw_root: Path, seal_path: Path, alias_path: Path) -> tuple[dict, list[dict]]:
    seal = verify(raw_root, seal_path)
    if seal["status"] != "complete":
        raise ValueError("all raw calls must be present before truth-side analysis")
    aliases_data = json.loads(alias_path.read_text(encoding="utf-8"))["aliases"]
    aliases = {row["server_video"]: row["condition"] for row in aliases_data}
    if len(aliases) != 6 or set(aliases.values()) != CONDITIONS:
        raise ValueError("truth alias mapping must have six distinct conditions")
    paired = raw_root / "paired.jsonl"
    d2, d2_packet = paired_report(paired, aliases, "D2")
    candidate, candidate_packet = paired_report(paired, aliases, "candidate")
    report = {
        "scope": "one_mechanism_development_only", "raw_seal_sha256": sha256(seal_path),
        "truth_alias_sha256": sha256(alias_path),
        "TOPReward": native_report(raw_root / "topreward/native_calls.jsonl", aliases, "TOPReward"),
        "Robometer_PR33_compat": native_report(raw_root / "robometer/native_calls.jsonl", aliases, "Robometer"),
        "D2": d2, "relation_endpoint_v1": candidate,
        "interpretation_status": "semantic_evidence_audit_pending; no architecture win claim",
        "limits": ["one development mechanism, not independent test",
                   "native curves do not reveal object/relation semantics",
                   "B0 has greater total red-object motion",
                   "G+ complete goal subconditions require separate visual audit"],
    }
    return report, d2_packet + candidate_packet


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", required=True, type=Path)
    parser.add_argument("--seal", required=True, type=Path)
    parser.add_argument("--truth-alias", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--evidence-packet", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.evidence_packet.exists():
        raise FileExistsError("analysis outputs must be new")
    report, packet = analyze(args.raw_root, args.seal, args.truth_alias)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.evidence_packet.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.evidence_packet.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n",
                                    encoding="utf-8")
    print(json.dumps({"scope": report["scope"],
                      "native_valid": [report["TOPReward"]["valid_count"],
                                       report["Robometer_PR33_compat"]["valid_count"]],
                      "paired_valid": [report["D2"]["valid_count"],
                                       report["relation_endpoint_v1"]["valid_count"]]}))


if __name__ == "__main__":
    main()

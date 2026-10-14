"""Local-only blind-break and audit worksheet for the one-session development suite.

This script reads expected directions from the local evidence index. It must
never be included in the server upload package.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from one_session_suite_v0_2 import STAGES


HERE = Path(__file__).resolve().parent
INDEX = HERE / "evidence_case_index.jsonl"
ORDER = {"harmful": -1, "unchanged": 0, "beneficial": 1, "completed": 2}
PAIRS = (("E", "S", ">"), ("E", "I_b", ">"), ("E", "N_b", ">"),
         ("H", "I_o", "<"), ("H", "N_o", "<"), ("G", "N_o", ">"))
AUDIT_FIELDS = ("visible_fact_correct", "entity_binding_correct",
                "relation_endpoint_correct", "goal_relevance_correct",
                "alternative_route_sound", "continuation_correct",
                "reason_supports_direction", "reviewer", "review_notes")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def usable_direction(row: dict | None) -> str | None:
    if not row or row.get("kind") != "model_output":
        return None
    validation = row.get("validation", {})
    return validation.get("direction") if validation.get("status") == "valid" else None


def h3_direction(tp: dict | None, f: dict | None) -> str | None:
    left, right = usable_direction(tp), usable_direction(f)
    return left if left == right else None


def pair_state(left: str | None, right: str | None, op: str) -> str:
    if left not in ORDER or right not in ORDER:
        return "unresolved"
    delta = ORDER[left] - ORDER[right]
    if delta == 0:
        return "tie"
    return "win" if (delta > 0 if op == ">" else delta < 0) else "loss"


def readout_ablations(output: dict | None) -> dict | None:
    if not output or output.get("kind") != "model_output":
        return None
    if output.get("validation", {}).get("status") not in ("valid", "direction_conflict"):
        return None
    try:
        value = json.loads(output["raw"])
        done = value["goal_done"]
        route = value["continuation"]
        relation = value["candidate_relation"]["satisfied"]
    except (ValueError, KeyError, TypeError):
        return None

    def endpoints(a: str, b: str, low: str, high: str) -> str:
        if a not in (low, high) or b not in (low, high):
            return "unknown"
        if a == b:
            return "unchanged"
        return "beneficial" if a == low else "harmful"

    no_completion = endpoints(route["t0"], route["t14"], "blocked", "possible")
    relation_only = ("completed" if done["t0"] == "false" and done["t14"] == "true"
                     else endpoints(relation["t0"], relation["t14"], "false", "true"))
    peak_credit = ("completed" if done["t0"] == "false" and done["t14"] == "true"
                   else "beneficial" if route["t0"] == "blocked" and route["t_mid"] == "possible"
                   else no_completion)
    return {"no_completion_priority": no_completion, "relation_only": relation_only,
            "peak_credit_no_revocation": peak_credit}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, type=Path, help="downloaded sealed model JSONL")
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    if args.out_dir.exists():
        raise FileExistsError(args.out_dir)
    raw = rows(args.raw)
    if not raw or raw[0].get("kind") != "configuration" or raw[0].get("suite_version") != "0.2.0-preflight":
        raise ValueError("unexpected suite config")
    expected = {row["video_sha256"]: row for row in rows(INDEX)}
    videos = {}
    outputs = {}
    for row in raw[1:]:
        kind = row.get("kind")
        key = (row.get("group"), row.get("video"))
        if kind == "video_input":
            if key in videos:
                raise ValueError("duplicate video_input")
            if row["video_sha256"] not in expected:
                raise ValueError("video SHA absent from local audit index")
            videos[key] = expected[row["video_sha256"]]
        elif kind in ("model_output", "model_failure"):
            call_key = (*key, row["stage"])
            if call_key in outputs:
                raise ValueError("duplicate model output")
            outputs[call_key] = row
    if len(videos) != 18:
        raise ValueError(f"expected all 18 development videos; got {len(videos)}")
    if any(stage not in STAGES for _, _, stage in outputs):
        raise ValueError("unexpected stage")
    if any((group, video) not in videos for group, video, _ in outputs):
        raise ValueError("output without video_input")

    case_rows, worksheet, ablation_rows = [], [], []
    by_case = defaultdict(dict)
    for (group, video), audit in sorted(videos.items()):
        for stage in (*STAGES, "H3"):
            output = outputs.get((group, video, stage))
            if stage == "H3":
                direction = h3_direction(outputs.get((group, video, "TP2")),
                                         outputs.get((group, video, "F3")))
                status = "derived_agreement" if direction else "derived_unknown"
            else:
                direction = usable_direction(output)
                status = ("missing" if output is None else "runtime_failure" if output["kind"] == "model_failure"
                          else output.get("validation", {}).get("status", "missing_validation"))
            validation = output.get("validation", {}) if output else {}
            claimed = None
            parsed = {}
            if output and output.get("kind") == "model_output":
                try:
                    candidate = json.loads(output["raw"])
                    parsed = candidate if isinstance(candidate, dict) else {}
                    claimed = parsed.get("direction")
                except (ValueError, TypeError):
                    pass
            relation = parsed.get("candidate_relation") if isinstance(parsed.get("candidate_relation"), dict) else {}
            evidence = parsed.get("evidence") if isinstance(parsed.get("evidence"), list) else []
            diagnostic_fields_complete = (len(parsed.get("frame_facts", [])) == 4 if stage == "V0" else
                                          bool(parsed.get("decision_reason")) and
                                          bool(relation.get("alternative_route_reason")) and
                                          len(evidence) >= 3)
            record = {"group": group, "video": video, "arm": audit["arm"],
                      "condition": audit["condition"], "case_id": audit["case_id"],
                      "stage": stage, "status": status, "direction": direction or "unknown",
                      "model_claimed_direction": claimed,
                      "deterministic_direction": validation.get("direction"),
                      "transient": validation.get("transient"),
                      "validation_reason": validation.get("reason"),
                      "diagnostic_fields_complete": diagnostic_fields_complete,
                      "goal_done": parsed.get("goal_done"),
                      "candidate_entity": relation.get("entity"),
                      "candidate_region": relation.get("region"),
                      "candidate_predicate": relation.get("predicate"),
                      "relation_states": relation.get("satisfied"),
                      "goal_relevance": relation.get("goal_relevance"),
                      "alternative_route": relation.get("alternative_route"),
                      "alternative_route_reason": relation.get("alternative_route_reason"),
                      "continuation": parsed.get("continuation"),
                      "evidence_claims": evidence,
                      "decision_reason": parsed.get("decision_reason"),
                      "uncertainty_reason": parsed.get("uncertainty_reason"),
                      "visual_only_frame_facts": parsed.get("frame_facts") if stage == "V0" else None,
                      "visual_only_changes": parsed.get("changes") if stage == "V0" else None,
                      "expected_direction": audit["expected"]["direction"] if stage != "V0" else None,
                      "direction_match": (direction == audit["expected"]["direction"] if direction else False)
                          if stage != "V0" else None,
                      "evidence_seconds": output.get("validation", {}).get("cited_seconds") if output else None,
                      "input_tokens": output.get("input_tokens") if output else None,
                      "output_tokens": output.get("output_tokens") if output else None,
                      "elapsed_ms": output.get("elapsed_ms") if output else None,
                      "peak_vram_bytes": output.get("peak_vram_bytes") if output else None,
                      "hit_output_cap": output.get("hit_output_cap") if output else None,
                      "raw_sha256": hashlib.sha256(output["raw"].encode()).hexdigest() if output and "raw" in output else None}
            case_rows.append(record)
            by_case[(audit["arm"], audit["condition"])][stage] = direction
            if stage != "H3":
                ablated = readout_ablations(output)
                if ablated is not None:
                    ablation_rows.append({"case_id": audit["case_id"], "stage": stage,
                                          "native_claimed_direction": claimed,
                                          "contract_direction": validation.get("direction"), **ablated})
                worksheet.append({**{key: json.dumps(record[key], ensure_ascii=False) if isinstance(record[key], (dict, list)) else record[key]
                                      for key in
                                      ("group", "video", "arm", "condition", "case_id", "stage",
                                       "status", "direction", "model_claimed_direction",
                                       "deterministic_direction", "expected_direction", "direction_match",
                                       "diagnostic_fields_complete", "goal_done", "candidate_entity",
                                       "candidate_region", "candidate_predicate", "relation_states",
                                       "goal_relevance", "alternative_route", "alternative_route_reason",
                                       "continuation", "evidence_claims", "decision_reason", "uncertainty_reason",
                                       "visual_only_frame_facts", "visual_only_changes")},
                                  **{field: "" for field in AUDIT_FIELDS}})
    pair_rows = []
    for arm in sorted({a for a, _ in by_case}):
        for stage in (*[stage for stage in STAGES if stage != "V0"], "H3"):
            for left, right, op in PAIRS:
                state = pair_state(by_case[(arm, left)].get(stage),
                                   by_case[(arm, right)].get(stage), op)
                pair_rows.append({"arm": arm, "stage": stage, "left": left,
                                  "right": right, "expected_operator": op, "outcome": state})
    aggregate = {}
    for stage in (*STAGES, "H3"):
        selected = [row for row in case_rows if row["stage"] == stage]
        aggregate[stage] = {"cases": len(selected),
                            "valid_or_agreed": sum(row["status"] in ("valid", "derived_agreement") for row in selected),
                            "direction_matches_all_18": sum(row["direction_match"] is True for row in selected) if stage != "V0" else None,
                            "diagnostic_fields_complete": sum(row["diagnostic_fields_complete"] for row in selected),
                            "status_counts": dict(Counter(row["status"] for row in selected)),
                            "core_E_H_matches": sum(row["direction_match"] is True for row in selected if row["condition"] in ("E", "H")) if stage != "V0" else None,
                            "G_matches": sum(row["direction_match"] is True for row in selected if row["condition"] == "G") if stage != "V0" else None,
                            "pair_counts": dict(Counter(row["outcome"] for row in pair_rows if row["stage"] == stage))}
    args.out_dir.mkdir(parents=True)
    (args.out_dir / "case_results.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in case_rows), encoding="utf-8")
    (args.out_dir / "pair_results.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in pair_rows), encoding="utf-8")
    (args.out_dir / "readout_ablations.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in ablation_rows), encoding="utf-8")
    with (args.out_dir / "semantic_audit_blank.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(worksheet[0]))
        writer.writeheader()
        writer.writerows(worksheet)
    summary = {"scope": "development_only_not_G2", "raw_sha256": sha(args.raw),
               "local_index_sha256": sha(INDEX), "aggregate": aggregate,
               "readout_ablation_rows": len(ablation_rows),
               "semantic_evidence_reviewed": False,
               "warning": "Automatic direction matching is not evidence correctness; complete semantic_audit_blank.csv locally."}
    (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"out_dir": str(args.out_dir), "raw_sha256": summary["raw_sha256"],
                      "rows": len(case_rows), "semantic_reviewed": False}))


if __name__ == "__main__":
    main()

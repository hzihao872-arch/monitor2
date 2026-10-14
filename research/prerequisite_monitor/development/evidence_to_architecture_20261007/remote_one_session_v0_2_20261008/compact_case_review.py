"""Print anonymous raw evidence for manual review, without local labels."""

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("group")
    parser.add_argument("video")
    parser.add_argument("--brief", action="store_true")
    args = parser.parse_args()
    raw_path = Path(__file__).parent / "qwen_evidence" / "raw.jsonl"
    for line in raw_path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if (row.get("group"), row.get("video")) != (args.group, args.video):
            continue
        if row.get("kind") not in {"model_output", "model_failure"}:
            continue
        stage = row["stage"]
        if row["kind"] == "model_failure":
            print(stage, "RUNTIME_FAILURE", row.get("error"))
            continue
        try:
            value = json.loads(row["raw"])
        except (ValueError, TypeError):
            print(stage, "PARSE_FAILURE", row["raw"][:180])
            continue
        if stage == "V0":
            if args.brief:
                print(stage, row["validation"]["status"], value.get("changes"))
                continue
            print(stage, json.dumps({
                "status": row["validation"]["status"],
                "facts": value.get("frame_facts"),
                "changes": value.get("changes"),
            }, ensure_ascii=False))
            continue
        relation = value.get("candidate_relation") or {}
        if args.brief:
            print(stage, row["validation"].get("status"),
                  "claim", value.get("direction"),
                  "read", row["validation"].get("direction"),
                  "done", value.get("goal_done"),
                  "relation", relation.get("predicate"), relation.get("satisfied"),
                  "route", value.get("continuation"),
                  "evidence", [item.get("claim") for item in value.get("evidence", [])])
            continue
        print(stage, json.dumps({
            "status": row["validation"].get("status"),
            "claimed": value.get("direction"),
            "readout": row["validation"].get("direction"),
            "done": value.get("goal_done"),
            "relation": relation.get("predicate"),
            "relation_states": relation.get("satisfied"),
            "relevance": relation.get("goal_relevance"),
            "alternative": relation.get("alternative_route"),
            "continuation": value.get("continuation"),
            "evidence": value.get("evidence"),
            "reason": value.get("decision_reason"),
            "uncertainty": value.get("uncertainty_reason"),
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()

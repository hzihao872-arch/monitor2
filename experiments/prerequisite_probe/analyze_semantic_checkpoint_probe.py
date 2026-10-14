"""Post-hash, truth-side audit of an optional base-VLM fact probe.

These outputs are diagnostics of a separately prompted base checkpoint, never
intermediate states of native TOPReward or Robometer.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .run_monitor_qwen import sha256
from .seal_single_scene_pilot import records


OTHER = {"B+": ("inside", "outside", "false"),
         "B0": ("inside", "inside", "true"),
         "U0": ("outside", "outside", "false"),
         "H-": ("outside", "inside", "false"),
         "G+": ("outside", "outside", "false"),
         "N0": ("outside", "outside", "false")}
GOAL = {"B+": ("outside", "outside", "false"),
        "B0": ("outside", "outside", "false"),
        "U0": ("outside", "outside", "false"),
        "H-": ("outside", "outside", "false"),
        "G+": ("outside", "inside", "true"),
        "N0": ("outside", "outside", "false")}
FIELDS = ("goal_object", "other_object", "goal_region", "other_at_0",
          "other_at_14", "returned", "goal_at_0", "goal_at_14",
          "complete_at_14", "missing_visual_evidence", "evidence")


def analyze(probe: Path, expected_sha256: str, alias_path: Path) -> dict:
    if sha256(probe) != expected_sha256:
        raise ValueError("fact probe must be hashed before truth is opened")
    aliases = {row["server_video"]: row["condition"] for row in
               json.loads(alias_path.read_text(encoding="utf-8"))["aliases"]}
    if len(aliases) != 6 or set(aliases.values()) != set(OTHER):
        raise ValueError("expected one complete six-condition scene")
    rows = records(probe)
    outputs = {row["video"]: row for row in rows if row.get("kind") in
               ("fact_probe", "probe_failure")}
    if len(outputs) != 6:
        raise ValueError("expected six fact probe outcomes")
    by_condition = {}
    for video, condition in aliases.items():
        row = outputs[video]
        if row["kind"] == "probe_failure":
            by_condition[condition] = {"video": video, "status": "failed",
                                       "error": row.get("error")}
            continue
        try:
            record = json.loads(row["raw"])
            if not isinstance(record, dict) or any(key not in record for key in FIELDS):
                raise ValueError("missing fact fields")
            expected = (*OTHER[condition], *GOAL[condition])
            actual = (record["other_at_0"], record["other_at_14"], record["returned"],
                      record["goal_at_0"], record["goal_at_14"], record["complete_at_14"])
            comparisons = {name: {"observed": got, "expected": want,
                                  "matches": got == want}
                           for name, got, want in zip(("other_at_0", "other_at_14",
                                                       "returned", "goal_at_0", "goal_at_14",
                                                       "complete_at_14"), actual, expected)}
            by_condition[condition] = {"video": video, "status": "parsed",
                                       "record": record, "comparisons": comparisons,
                                       "all_six_enums_match": all(item["matches"]
                                                              for item in comparisons.values()),
                                       "object_identity_human_audit": "pending",
                                       "evidence_human_audit": "pending"}
        except Exception as exc:
            by_condition[condition] = {"video": video, "status": "invalid",
                                       "raw": row.get("raw"),
                                       "error": f"{type(exc).__name__}: {exc}"}
    return {"scope": "optional_base_vlm_fact_probe_only",
            "not_native_topreward_or_robometer_trace": True,
            "probe_sha256": expected_sha256, "truth_alias_sha256": sha256(alias_path),
            "by_condition": by_condition,
            "note": "enum agreement is not proof of native scorer semantics; G+ full-predicate evidence requires manual review"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", required=True, type=Path)
    parser.add_argument("--probe-sha256", required=True)
    parser.add_argument("--truth-alias", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = analyze(args.probe, args.probe_sha256, args.truth_alias)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"scope": result["scope"],
                      "parsed": sum(x["status"] == "parsed" for x in result["by_condition"].values())}))


if __name__ == "__main__":
    main()

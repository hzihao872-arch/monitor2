"""Join audited core cases with pre-aggregate visual/raw semantic review."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
STAGES = ("V0", "D1", "T1", "P1", "TP1", "D2", "TP2", "D3", "F3", "H3")
CORE = ("E", "H", "G", "R")
COST_CHAIN = {
    "V0": ("V0",), "D1": ("D1",), "T1": ("T1",), "P1": ("P1",),
    "TP1": ("TP1",), "D2": ("D1", "D2"), "TP2": ("TP1", "TP2"),
    "D3": ("D1", "D2", "D3"), "F3": ("F3",),
    "H3": ("TP1", "TP2", "F3"),
}


def semantic_flag(arm: str, condition: str, stage: str) -> tuple[str, str]:
    if stage == "H3":
        return "derived_only", "H3 has no independent evidence; inspect TP2 and F3 inputs"
    if condition == "G":
        if stage == "V0":
            return "visual_goal_fact_supported", "goal object placement visible at t14"
        if arm == "access_gate":
            if stage in ("TP1", "TP2"):
                return "completion_readout_conflict", "goal_done true but claimed beneficial"
            return "completion_evidence_supported", "goal object visibly inside box"
        if stage in ("D1", "T1", "P1", "TP1"):
            return "completion_field_schema_failure", "placement visible but goal_done.t14 false"
        if stage == "F3":
            return "completion_readout_conflict", "placement visible but goal_done.t14 false"
        return "completion_evidence_supported", "goal object visibly on deployed board"
    if condition == "E":
        if stage == "V0":
            return "target_relation_missed", "critical opening/board endpoint absent from V0 changes"
        if arm == "access_gate" and stage in ("TP1", "TP2"):
            return "visual_endpoint_wrong", "middle opening seen but open t14 misread as closed"
        return "target_relation_missed", "unchanged goal object substituted for preparation evidence"
    if condition == "H":
        if stage == "V0":
            return "target_relation_missed", "new obstruction/board withdrawal absent from V0 changes"
        if arm == "access_gate" and stage in ("TP1", "TP2"):
            return "route_readout_wrong", "plate position partly seen; continuation harm not represented"
        return "target_relation_missed", "unchanged goal object substituted for obstruction evidence"
    if condition == "R":
        if stage == "V0":
            return "target_relation_missed", "deployment then revocation absent from V0 changes"
        if arm == "access_gate" and stage in ("TP1", "TP2"):
            return "temporal_fact_route_wrong", "closed/open/closed visible but route endpoints and claim wrong"
        if arm == "support_surface" and stage == "F3":
            return "unsupported_mid_route", "mid route changes without board evidence; endpoints wrong"
        return "net_label_only", "unchanged label lacks visible revocation evidence"
    raise ValueError((arm, condition, stage))


def main() -> None:
    rows = [json.loads(line) for line in (ROOT / "audit_qwen" / "case_results.jsonl").read_text(
        encoding="utf-8").splitlines()]
    index = {(row["arm"], row["condition"], row["stage"]): row for row in rows}
    records = []
    for arm in ("access_gate", "support_surface"):
        for condition in CORE:
            for stage in STAGES:
                row = index[arm, condition, stage]
                flag, note = semantic_flag(arm, condition, stage)
                components = [index[arm, condition, part] for part in COST_CHAIN[stage]]
                records.append({
                    "arm": arm, "condition": condition, "case_id": row["case_id"],
                    "stage": stage, "status": row["status"],
                    "model_claimed_direction": row["model_claimed_direction"],
                    "usable_direction": row["direction"],
                    "expected_direction": row["expected_direction"],
                    "direction_match": row["direction_match"],
                    "semantic_evidence_flag": flag,
                    "semantic_review_note": note,
                    "reviewer": "Codex AI visual and raw-text review; not independent human",
                    "nominal_calls": len(components),
                    "cumulative_input_tokens": sum(part["input_tokens"] or 0 for part in components),
                    "cumulative_output_tokens": sum(part["output_tokens"] or 0 for part in components),
                    "cumulative_elapsed_ms": sum(part["elapsed_ms"] or 0 for part in components),
                    "max_peak_vram_bytes": max((part["peak_vram_bytes"] or 0 for part in components), default=0),
                    "raw_sha256": row["raw_sha256"],
                })
    output = ROOT / "core_case_semantic_review.csv"
    with output.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    print(json.dumps({"rows": len(records), "path": str(output)}))


if __name__ == "__main__":
    main()

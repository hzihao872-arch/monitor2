"""Local-only exploratory P2 stability and P3 static-image reports."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from model_side.pilot_pkg.seal_fresh_batch import sha256, verify
from score_fresh_batch import score

ARMS = ("access_gate", "support_surface")
METHODS = ("TOPReward", "Robometer")
STATIC_PAIRS = (("N_o", "N_b"), ("S", "N_b"), ("G", "N_o"))


def compare_p2(first: dict, second: dict) -> dict:
    cells = {}
    for arm, methods in first["cells"].items():
        cells[arm] = {}
        for method, initial in methods.items():
            repeated = second["cells"][arm][method]
            conditions = {}
            for name, a in initial["by_condition"].items():
                b = repeated["by_condition"][name]
                item = {"first_status": a["status"], "repeat_status": b["status"],
                        "failure_repeated": a["status"] == "failed" and b["status"] == "failed"}
                if a["status"] == b["status"] == "valid":
                    item["point_difference_repeat_minus_first"] = [y - x for x, y in zip(a["points_t0_t14"], b["points_t0_t14"])]
                    item["delta_difference_repeat_minus_first"] = b["delta_window"] - a["delta_window"]
                conditions[name] = item
            pairs = {}
            for name, a in initial["pairs"].items():
                b = repeated["pairs"][name]
                pairs[name] = {"first_outcome": a["outcome"], "repeat_outcome": b["outcome"],
                               "direction_flipped": {a["outcome"], b["outcome"]} == {"win", "loss"},
                               "changed": a["outcome"] != b["outcome"]}
            cells[arm][method] = {"by_condition": conditions, "pairs": pairs}
    return {"scope": "P2_same_input_repeat_exploratory", "cells": cells,
            "limits": "Repeat is not an independent new scene or G2"}


def p3_cell(rows: list[dict], aliases: dict[str, str], method: str) -> dict:
    outcomes = {}
    for row in rows:
        if row.get("kind") in ("native_result", "native_failure"):
            if row["video"] in outcomes:
                raise ValueError("duplicate static outcome")
            outcomes[row["video"]] = row
    by_condition = {}
    for video, condition in aliases.items():
        row = outcomes.get(video)
        if row is None:
            by_condition[condition] = {"status": "missing", "video": video}
        elif row["kind"] == "native_failure":
            by_condition[condition] = {"status": "failed", "video": video, "error": row.get("error")}
        else:
            values = row.get("prefix_rewards") if method == "TOPReward" else row.get("progress")
            if not isinstance(values, list) or len(values) != 15 or any(not isinstance(x, (int, float)) or not math.isfinite(x) for x in values):
                by_condition[condition] = {"status": "invalid", "video": video}
            else:
                by_condition[condition] = {"status": "valid", "video": video, "points_t0_t14": values,
                                           "t14": values[14], "elapsed_ms": row.get("elapsed_ms")}
    comparisons = {}
    for left, right in STATIC_PAIRS:
        a, b = by_condition[left], by_condition[right]
        key = f"{left}-{right}"
        if a["status"] != "valid" or b["status"] != "valid":
            comparisons[key] = {"outcome": "unavailable", "left_status": a["status"], "right_status": b["status"]}
        else:
            difference = a["t14"] - b["t14"]
            comparisons[key] = {"difference": difference,
                                "outcome": "tie" if difference == 0 else ("positive" if difference > 0 else "negative")}
    return {"by_condition": by_condition, "comparisons_t14": comparisons,
            "limit": "Static repeated frames are out of distribution; t14 is descriptive only"}


def p2_report(args) -> dict:
    inputs = {"access_gate": args.access_input, "support_surface": args.support_input}
    truths = {"access_gate": args.access_truth, "support_surface": args.support_truth}
    first = score(args.p0_raw, args.p0_seal, inputs, truths)
    second = score(args.p2_raw, args.p2_seal, inputs, truths)
    report = compare_p2(first, second)
    report["p0_seal_sha256"] = sha256(args.p0_seal)
    report["p2_seal_sha256"] = sha256(args.p2_seal)
    return report


def p3_report(args) -> dict:
    inputs = {"access_gate": args.access_input, "support_surface": args.support_input}
    sealed = verify(args.p3_raw, args.p3_seal, inputs, expected_count=4)
    if sealed["status"] == "incomplete":
        raise ValueError("incomplete P3 raw; do not open mapping")
    maps = {"access_gate": args.access_map, "support_surface": args.support_map}
    cells = {}
    for arm in ARMS:
        data = json.loads(maps[arm].read_text(encoding="utf-8"))
        aliases = {video: item["condition"] for video, item in data.items()}
        if len(aliases) != 4 or set(aliases.values()) != {"N_b", "S", "N_o", "G"}:
            raise ValueError("four local static aliases required")
        cells[arm] = {}
        for method in METHODS:
            journal = args.p3_raw / arm / method.lower() / "native_calls.jsonl"
            rows = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines() if line.strip()]
            cells[arm][method] = p3_cell(rows, aliases, method)
    return {"scope": "P3_static_end_state_exploratory_not_G2", "p3_seal_sha256": sha256(args.p3_seal),
            "local_mapping_sha256": {arm: sha256(maps[arm]) for arm in ARMS}, "cells": cells}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=("p2", "p3"))
    for name in ("p0_raw", "p0_seal", "p2_raw", "p2_seal", "p3_raw", "p3_seal", "access_input", "support_input",
                 "access_truth", "support_truth", "access_map", "support_map", "output"):
        parser.add_argument("--" + name.replace("_", "-"), type=Path, required=name in ("access_input", "support_input", "output"))
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    report = p2_report(args) if args.mode == "p2" else p3_report(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"scope": report["scope"], "output": str(args.output)}))


if __name__ == "__main__":
    main()

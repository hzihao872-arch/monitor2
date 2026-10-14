"""Local-only scoring; opens truth maps only after raw seal verification."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path

from model_side.pilot_pkg.seal_fresh_batch import sha256, verify

ARMS = ("access_gate", "support_surface")
METHODS = ("TOPReward", "Robometer")
CONDITIONS = {"E", "S", "I_b", "N_b", "R", "H", "I_o", "N_o", "G"}
PAIRS = (("E", "S", 1), ("E", "I_b", 1), ("E", "N_b", 1),
         ("H", "I_o", -1), ("H", "N_o", -1), ("G", "N_o", 1))


def curve(values: object) -> dict:
    if not isinstance(values, list) or len(values) != 15 or any(
            not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x) for x in values):
        raise ValueError("requires 15 finite native values")
    values = [float(x) for x in values]
    first = statistics.median(values[:3])
    last = statistics.median(values[12:])
    return {"points_t0_t14": values, "start_median_t0_t2": first,
            "end_median_t12_t14": last, "delta_window": last - first,
            "t7_t8": values[7:9], "last_minus_mid_peak": last - max(values[7:9])}


def score_method(rows: list[dict], aliases: dict[str, str], method: str) -> dict:
    outcomes = {}
    for row in rows:
        if row.get("kind") not in ("native_result", "native_failure"):
            continue
        video = row["video"]
        if video in outcomes:
            raise ValueError("duplicate outcome: " + video)
        outcomes[video] = row
    by_condition = {}
    for video, condition in aliases.items():
        row = outcomes.get(video)
        if row is None:
            by_condition[condition] = {"status": "missing", "video": video}
        elif row["kind"] == "native_failure":
            by_condition[condition] = {"status": "failed", "video": video, "error": row.get("error"),
                                       "returncode": row.get("returncode"), "elapsed_ms": row.get("elapsed_ms")}
        else:
            try:
                values = row["prefix_rewards"] if method == "TOPReward" else row["progress"]
                scored = curve(values)
                by_condition[condition] = {"status": "valid", "video": video, **scored,
                                           "native_field": "prefix_rewards" if method == "TOPReward" else "progress",
                                           "elapsed_ms": row.get("elapsed_ms")}
                if method == "TOPReward":
                    by_condition[condition]["prefix_token_counts"] = row.get("prefix_token_counts")
                if method == "Robometer" and condition == "G":
                    success = curve(row["success_head"])
                    by_condition[condition]["success_head_t14"] = success["points_t0_t14"][14]
                    by_condition[condition]["success_head_points_diagnostic_only"] = success["points_t0_t14"]
            except (ValueError, KeyError, TypeError) as exc:
                by_condition[condition] = {"status": "invalid", "video": video,
                                           "error": f"{type(exc).__name__}: {exc}"}
    pairs = {}
    for left, right, direction in PAIRS:
        key = f"{left}{'>' if direction > 0 else '<'}{right}"
        a, b = by_condition[left], by_condition[right]
        if a["status"] != "valid" or b["status"] != "valid":
            pairs[key] = {"outcome": "unavailable", "left_status": a["status"], "right_status": b["status"]}
            continue
        difference = a["delta_window"] - b["delta_window"]
        outcome = "tie" if difference == 0 else ("win" if difference * direction > 0 else "loss")
        pairs[key] = {"outcome": outcome, "difference": difference,
                      "left_delta": a["delta_window"], "right_delta": b["delta_window"]}
    return {"native_scale": "raw within-method only", "by_condition": by_condition, "pairs": pairs,
            "counts": {name: sum(item["outcome"] == name for item in pairs.values())
                       for name in ("win", "loss", "tie", "unavailable")},
            "reversal_R": by_condition["R"], "terminal_G": by_condition["G"]}


def score(raw_root: Path, seal_path: Path, input_paths: dict[str, Path], truth_paths: dict[str, Path]) -> dict:
    sealed = verify(raw_root, seal_path, input_paths)
    if sealed["status"] == "incomplete":
        raise ValueError("incomplete raw batch; keep truth closed")
    aliases = {}
    for arm in ARMS:
        aliases[arm] = json.loads(truth_paths[arm].read_text(encoding="utf-8"))
        if len(aliases[arm]) != 9 or set(aliases[arm].values()) != CONDITIONS or len(set(aliases[arm])) != 9:
            raise ValueError("nine unique conditions required: " + arm)
    cells = {}
    for arm in ARMS:
        cells[arm] = {}
        for method in METHODS:
            lower = method.lower()
            journal = raw_root / arm / lower / "native_calls.jsonl"
            rows = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines() if line.strip()]
            cells[arm][method] = score_method(rows, aliases[arm], method)
    return {"scope": "fresh_dev_v2_development_only_not_G2", "raw_seal_sha256": sha256(seal_path),
            "truth_map_sha256": {arm: sha256(truth_paths[arm]) for arm in ARMS},
            "cells": cells, "primary_rule": "median(t12,t13,t14)-median(t0,t1,t2); exact-zero tie",
            "limits": ["P1-P3 do not alter these P0 metrics", "no cross-model absolute-score comparison"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    for name in ("raw_root", "seal", "access_input", "support_input", "access_truth", "support_truth", "output"):
        parser.add_argument("--" + name.replace("_", "-"), required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.output == args.seal or args.raw_root in args.output.parents:
        raise FileExistsError("score output must be new and outside raw")
    inputs = {"access_gate": args.access_input, "support_surface": args.support_input}
    truths = {"access_gate": args.access_truth, "support_surface": args.support_truth}
    report = score(args.raw_root, args.seal, inputs, truths)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({arm: {method: item["counts"] for method, item in cells.items()}
                      for arm, cells in report["cells"].items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()

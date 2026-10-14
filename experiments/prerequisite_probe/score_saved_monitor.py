"""Offline post-seal scoring; never imported by the model runner or cloud bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .monitor_contract import event_direction
from .run_monitor_qwen import sha256


EXPECTED = {"B+": "positive", "B0": "zero", "U0": "zero",
            "H-": "negative", "G+": "positive", "N0": "zero"}
RANK = {"negative": -1, "zero": 0, "positive": 1}
PAIRS = (("B+", "B0", ">"), ("B+", "U0", ">"),
         ("H-", "N0", "<"), ("G+", "N0", ">"))


def summarize(rows: list[dict], labels: dict[str, str], method: str) -> dict:
    if method not in ("D", "P", "F", "D2_review", "H0"):
        raise ValueError(method)
    by_video = {}
    for row in rows:
        matching = (row.get("kind") == "hybrid" and method == "H0") or (
            row.get("kind") == "model_call" and row.get("method") == method)
        if not matching:
            continue
        video = row["video"]
        if video in by_video:
            raise ValueError(f"duplicate result: {method} {video}")
        by_video[video] = row
    per_case = {}
    counts = {key: 0 for key in ("correct", "wrong", "uncertain", "invalid", "missing")}
    for video, condition in labels.items():
        row = by_video.get(video)
        if row is None:
            direction, status = None, "missing"
        elif method == "H0":
            direction = row.get("direction")
            status = direction if direction in RANK else (
                "uncertain" if direction == "uncertain" else "invalid")
        elif row.get("validity") != "valid":
            direction, status = None, "invalid"
        else:
            direction = event_direction(row["record"])
            status = direction if direction in RANK else "uncertain"
        if status in ("missing", "invalid", "uncertain"):
            counts[status] += 1
        elif direction == EXPECTED[condition]:
            counts["correct"] += 1
        else:
            counts["wrong"] += 1
        per_case[condition] = {"video": video, "direction": direction,
                               "status": status, "expected": EXPECTED[condition],
                               "errors": row.get("errors", []) if row else []}
    pairwise = {}
    for left, right, operator in PAIRS:
        name = f"{left}{operator}{right}"
        first, second = per_case.get(left), per_case.get(right)
        if (first is None or second is None or
                first["direction"] not in RANK or second["direction"] not in RANK):
            pairwise[name] = None
        else:
            a, b = RANK[first["direction"]], RANK[second["direction"]]
            pairwise[name] = a > b if operator == ">" else a < b
    budget_methods = ("P", "F") if method == "H0" else (
        ("D", "D2_review") if method == "D2_review" else (method,))
    cost_rows = [row for row in rows if row.get("kind") == "model_call" and
                 row.get("video") in labels and row.get("method") in budget_methods]
    budget = {"calls": len(cost_rows),
              "input_tokens": sum(row.get("input_tokens", 0) for row in cost_rows),
              "output_tokens": sum(row.get("output_tokens", 0) for row in cost_rows),
              "elapsed_ms": sum(row.get("elapsed_ms", 0) for row in cost_rows),
              "peak_vram_bytes_max": max((row.get("peak_vram_bytes", 0)
                                          for row in cost_rows), default=0),
              "missing_usage_calls": sum("input_tokens" not in row for row in cost_rows)}
    return {"method": method, "total": len(labels), **counts,
            "pairwise": pairwise, "per_case": per_case,
            "budget": budget, "evidence_audit": "pending"}


def score_file(root: Path, output_jsonl: Path, report_path: Path) -> dict:
    if report_path.exists():
        raise FileExistsError(report_path)
    freeze = root / "truth" / "frozen_test.json"
    if sha256(freeze) != (root / "truth" / "frozen_test.sha256").read_text().strip():
        raise ValueError("frozen test hash mismatch")
    frozen = json.loads(freeze.read_text(encoding="utf-8"))
    labels = {f"{stem}.mp4": item["condition"] for stem, item in
              frozen["cases"].items()}
    rows = [json.loads(line) for line in output_jsonl.read_text(encoding="utf-8").splitlines()
            if line.strip()]
    report = {"scene": frozen["scene_family"], "source_jsonl_sha256": sha256(output_jsonl),
              "freeze_sha256": sha256(freeze), "methods": {method: summarize(rows, labels, method)
              for method in ("D", "P", "F", "D2_review", "H0")},
              "caveat": "Visual evidence validity requires separate frame audit; no score here proves causal understanding."}
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--jsonl", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = score_file(args.root, args.jsonl, args.output)
    print(json.dumps({"scene": report["scene"],
                      "method_totals": {k: v["total"] for k, v in
                                        report["methods"].items()}}))


if __name__ == "__main__":
    main()

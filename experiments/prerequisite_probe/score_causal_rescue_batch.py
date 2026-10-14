"""Local-only scoring after L1/L2 raw seal verification; reads truth mapping here."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path

from .seal_causal_rescue_batch import sha256, verify


CONDITIONS = {"B+", "B0", "U0", "H-", "G+", "N0"}
PAIRS = (("B+", "U0", 1), ("H-", "U0", -1), ("H-", "N0", -1),
         ("B+", "B0", 1), ("G+", "N0", 1))
CORE = {"B+>U0", "H-<U0", "H-<N0", "G+>N0"}


def curve(values) -> dict:
    values = [float(x) for x in values]
    if len(values) != 15 or not all(math.isfinite(x) for x in values):
        raise ValueError("curve requires 15 finite native values")
    start = statistics.median(values[:3])
    return {"points": values, "start_median_t0_t2": start,
            "end_median_t12_t14": statistics.median(values[12:]),
            "delta_window": statistics.median(values[12:]) - start,
            "delta_t14": values[14] - start,
            "action_peak_t2_t12": max(values[2:13]),
            "action_trough_t2_t12": min(values[2:13])}


def pairs(by_condition: dict, field: str) -> dict:
    report = {}
    for left, right, sign in PAIRS:
        key = f"{left}{'>' if sign > 0 else '<'}{right}"
        a, b = by_condition[left], by_condition[right]
        if a["status"] != "valid" or b["status"] != "valid":
            report[key] = {"outcome": "unavailable", "left_status": a["status"], "right_status": b["status"]}
            continue
        difference = a[field] - b[field]
        outcome = "tie" if abs(difference) <= 1e-8 else ("win" if difference * sign > 0 else "loss")
        report[key] = {"outcome": outcome, "difference": difference,
                       "left": a[field], "right": b[field]}
    return report


def model_report(journal: Path, aliases: dict, method: str) -> dict:
    rows = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines() if line.strip()]
    outcomes = {}
    for row in rows:
        if row.get("kind") not in ("native_result", "native_failure"):
            continue
        video = row["video"]
        if video in outcomes:
            raise ValueError(f"duplicate output: {journal}: {video}")
        outcomes[video] = row
    by_condition = {}
    for video, condition in aliases.items():
        row = outcomes.get(video)
        if row is None:
            by_condition[condition] = {"status": "missing", "video": video}
        elif row["kind"] == "native_failure":
            by_condition[condition] = {"status": "failed", "video": video,
                                       "error": row.get("error"), "returncode": row.get("returncode"),
                                       "elapsed_ms": row.get("elapsed_ms")}
        else:
            try:
                values = row["prefix_rewards"] if method == "TOPReward" else row["progress"]
                primary = curve(values)
                success = curve(row["success_head"]) if method == "Robometer" else None
                by_condition[condition] = {"status": "valid", "video": video,
                                           **primary, "success_head_terminal_control": success,
                                           "elapsed_ms": row.get("elapsed_ms"),
                                           "prefix_token_counts": row.get("prefix_token_counts")}
            except Exception as exc:
                by_condition[condition] = {"status": "invalid", "video": video,
                                           "error": f"{type(exc).__name__}: {exc}"}
    return {"scale": "raw native values; within-method comparisons only",
            "by_condition": by_condition,
            "pairs_window": pairs(by_condition, "delta_window"),
            "pairs_t14": pairs(by_condition, "delta_t14"),
            "valid_count": sum(x["status"] == "valid" for x in by_condition.values())}


def score(raw_root: Path, seal_path: Path, alias_path: Path) -> dict:
    seal = verify(raw_root, seal_path)
    if seal["status"] == "incomplete":
        raise ValueError("incomplete raw batch; do not open truth yet")
    aliases_data = json.loads(alias_path.read_text(encoding="utf-8"))["aliases"]
    aliases = {row["server_video"]: row["condition"] for row in aliases_data}
    if len(aliases) != 6 or set(aliases.values()) != CONDITIONS:
        raise ValueError("six unique aliases required")
    arms = {}
    for arm in ("L1", "L2"):
        arms[arm] = {
            "TOPReward": model_report(raw_root / arm / "topreward/native_calls.jsonl", aliases, "TOPReward"),
            "Robometer": model_report(raw_root / arm / "robometer/native_calls.jsonl", aliases, "Robometer"),
        }
    gates = {}
    for arm, methods in arms.items():
        gates[arm] = all(
            methods[method][field][pair]["outcome"] == "win"
            for method in ("TOPReward", "Robometer")
            for field in ("pairs_window", "pairs_t14") for pair in CORE
        )
    return {"scope": "seen_six_clip_development_only", "raw_seal_sha256": sha256(seal_path),
            "truth_alias_sha256": sha256(alias_path), "arms": arms,
            "first_batch_core_gate_by_arm": gates,
            "next_step": "new_sample_replication" if any(gates.values()) else "conditional_V1_C1_Q1_diagnostics",
            "limits": ["development videos were previously seen", "success head is terminal control only",
                       "window and t14 must both be reported", "failed/invalid clips are not zero scores"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", required=True, type=Path)
    parser.add_argument("--seal", required=True, type=Path)
    parser.add_argument("--truth-alias", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    report = score(args.raw_root, args.seal, args.truth_alias)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"core_gate": report["first_batch_core_gate_by_arm"],
                      "next_step": report["next_step"]}))


if __name__ == "__main__":
    main()

"""Local-only P4/new TOPReward text-probe analysis. Never upload this file."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import median

from audit_one_session_v0_2 import HERE, INDEX, PAIRS


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def delta(points: list[float]) -> float:
    if len(points) != 15:
        raise ValueError("expected 15 prefix points")
    return median(points[12:15]) - median(points[0:3])


def result(left: float | None, right: float | None, op: str) -> str:
    if left is None or right is None:
        return "unavailable"
    difference = left - right
    if difference == 0:
        return "tie"
    return "win" if (difference > 0 if op == ">" else difference < 0) else "loss"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", required=True, type=Path)
    parser.add_argument("--raw-root", required=True, type=Path)
    parser.add_argument("--text-seal", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    seal = json.loads(args.text_seal.read_text(encoding="utf-8"))
    if seal.get("input_manifest_sha256") != sha(args.input_root / "text_probe_manifest.json"):
        raise ValueError("text probe manifest SHA mismatch")
    for entry in seal["files"]:
        path = args.raw_root / entry["path"]
        if not path.is_file() or sha(path) != entry["sha256"] or path.stat().st_size != entry["size_bytes"]:
            raise ValueError("raw text probe SHA mismatch: " + entry["path"])
    index_rows = [json.loads(line) for line in INDEX.read_text(encoding="utf-8").splitlines() if line.strip()]
    index = {row["video_sha256"]: row for row in index_rows}
    comparisons = []
    outcomes = {}
    variants = ("P0_original", "P4_neutral", "P4_causal_fact", *seal["variants"])
    for variant in variants:
        for arm in ("access_gate", "support_surface"):
            for row in (item for item in index_rows if item["arm"] == arm):
                if variant == "P0_original":
                    points = row["p0"]["TOPReward"]["points_t0_t14"]
                    instr_hash = None
                    token_counts = None
                    runtime_ms = row["p0"]["TOPReward"].get("elapsed_ms")
                elif variant.startswith("P4_"):
                    prior = row["p4"][variant.removeprefix("P4_")]
                    points = prior["points_t0_t14"]
                    instr_hash = prior["instruction_sha256"]
                    token_counts = None
                    runtime_ms = None
                else:
                    group = "group_01" if arm == "access_gate" else "group_02"
                    folder = args.raw_root / variant / group
                    path = folder / f"{Path(row['video']).stem}.json"
                    if not path.is_file():
                        points = None
                        instr_hash = None
                        token_counts = None
                        runtime_ms = None
                    else:
                        native = json.loads(path.read_text(encoding="utf-8"))
                        if native["video_sha256"] != row["video_sha256"] or native["prefix_lengths"] != list(range(1, 16)):
                            raise ValueError("native result does not match local video")
                        points = native["prefix_rewards"]
                        instr_hash = hashlib.sha256(native["instruction"].encode()).hexdigest()
                        token_counts = native.get("prefix_token_counts")
                        runtime_ms = native.get("elapsed_ms")
                item = {"variant": variant, "arm": arm, "condition": row["condition"],
                        "case_id": row["case_id"], "video_sha256": row["video_sha256"],
                        "instruction_sha256": instr_hash, "points": points,
                        "delta_window": delta(points) if points is not None else None,
                        "prefix_token_counts": token_counts, "elapsed_ms": runtime_ms}
                comparisons.append(item)
                outcomes[(variant, arm, row["condition"])] = item["delta_window"]
    pairs = []
    for variant in variants:
        for arm in ("access_gate", "support_surface"):
            for left, right, op in PAIRS:
                x, y = outcomes[(variant, arm, left)], outcomes[(variant, arm, right)]
                pairs.append({"variant": variant, "arm": arm, "left": left, "right": right,
                              "expected_operator": op, "difference": x-y if x is not None and y is not None else None,
                              "outcome": result(x, y, op)})
    report = {"scope": "development_text_diagnostic_not_native_P0_not_G2",
              "rule": "median(t12,t13,t14)-median(t0,t1,t2); exact-zero tie",
              "index_sha256": sha(INDEX), "text_seal_sha256": sha(args.text_seal),
              "variants": variants, "cases": comparisons, "pairs": pairs,
              "pair_counts": {variant: dict(Counter(row["outcome"] for row in pairs if row["variant"] == variant))
                              for variant in variants},
              "warning": "Same videos and different task text. These curves do not reveal internal attention or prove a generated relation true."}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"cases": len(comparisons), "pairs": len(pairs), "variants": len(variants)}))


if __name__ == "__main__":
    main()

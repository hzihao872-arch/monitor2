"""Local-only P4 score after raw seal verification; never upload this file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from optional.p4_seal import sha256, verify
from score_fresh_batch import score_method

ARMS = ("access_gate", "support_surface")


def score(raw_root: Path, seal_path: Path, input_root: Path, truth_root: Path,
          p0_analysis: Path, variant: str) -> dict:
    if variant not in ("neutral", "causal_fact", "credit_rule"):
        raise ValueError("unknown frozen variant")
    inputs = {arm: input_root / arm / "model_input" for arm in ARMS}
    sealed = verify(raw_root, seal_path, inputs)
    if sealed["status"] == "incomplete":
        raise ValueError("raw batch incomplete; truth stays closed")
    baseline = json.loads(p0_analysis.read_text(encoding="utf-8"))
    cells = {}
    truth_hashes = {}
    for arm in ARMS:
        truth_path = truth_root / arm / "dev_v2" / "truth" / "condition_map.json"
        aliases = json.loads(truth_path.read_text(encoding="utf-8"))
        if len(aliases) != 9 or len(set(aliases.values())) != 9:
            raise ValueError("invalid truth map")
        truth_hashes[arm] = sha256(truth_path)
        rows = [json.loads(line) for line in (raw_root / arm / "topreward" / "native_calls.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        scored = score_method(rows, aliases, "TOPReward")
        old = baseline["cells"][arm]["TOPReward"]
        scored["pair_change_from_P0"] = {}
        for name, pair in scored["pairs"].items():
            previous = old["pairs"][name]
            scored["pair_change_from_P0"][name] = {
                "P0_outcome": previous["outcome"], "P4_outcome": pair["outcome"],
                "difference_change": (pair["difference"] - previous["difference"])
                if pair["outcome"] not in ("unavailable",) and previous["outcome"] not in ("unavailable",) else None,
            }
        cells[arm] = scored
    return {"scope": "P4_TOPReward_instruction_intervention_exploratory_not_G2",
            "variant": variant, "raw_seal_sha256": sha256(seal_path),
            "P0_analysis_sha256": sha256(p0_analysis), "truth_map_sha256": truth_hashes,
            "rule": "median(t12,t13,t14)-median(t0,t1,t2); exact-zero tie; all pairs reported",
            "cells": cells,
            "limits": "Changed goal text; cannot be counted as original final-goal-only protocol or G2"}


def main() -> None:
    parser = argparse.ArgumentParser()
    for name in ("raw_root", "seal", "input_root", "truth_root", "p0_analysis", "output"):
        parser.add_argument("--" + name.replace("_", "-"), required=True, type=Path)
    parser.add_argument("--variant", required=True, choices=("neutral", "causal_fact", "credit_rule"))
    args = parser.parse_args()
    if args.output.exists() or args.raw_root.resolve() in args.output.resolve().parents:
        raise FileExistsError("score output must be new and outside raw")
    report = score(args.raw_root, args.seal, args.input_root, args.truth_root,
                   args.p0_analysis, args.variant)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({arm: result["counts"] for arm, result in report["cells"].items()}))


if __name__ == "__main__":
    main()

"""Local-only P6 scoring after full raw seal verification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from p6pkg.seal import verify
from p6pkg.run import sha256

EXPECTED = {
    "E": "beneficial", "S": "unchanged", "I_b": "unchanged",
    "N_b": "unchanged", "R": "unchanged", "H": "harmful",
    "I_o": "unchanged", "N_o": "unchanged", "G": "completed",
}


def score(raw_root: Path, seal_path: Path, paths: dict[str, Path], truth_root: Path) -> dict:
    seal = verify(raw_root, seal_path, 18, paths)
    if seal["status"] == "incomplete":
        raise ValueError("incomplete P6; keep truth closed")
    rows = [json.loads(line) for line in (raw_root / "calls.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    outcomes = {(row["arm"], row["video"]): row for row in rows
                if row.get("kind") in ("model_output", "model_failure")}
    cases, truth_hashes = {}, {}
    for arm in ("access_gate", "support_surface"):
        truth_path = truth_root / arm / "dev_v2" / "truth" / "condition_map.json"
        mapping = json.loads(truth_path.read_text(encoding="utf-8"))
        truth_hashes[arm] = sha256(truth_path)
        cases[arm] = {}
        for video, condition in mapping.items():
            row = outcomes[(arm, video)]
            parsed = row.get("parsed", {}) if row.get("parse_status") == "valid" else {}
            observed = parsed.get("label")
            cases[arm][condition] = {
                "video": video, "expected": EXPECTED[condition], "observed": observed,
                "matches_label": observed == EXPECTED[condition],
                "parse_status": row.get("parse_status", row["kind"]),
                "reason": parsed.get("reason"), "uncertainty": parsed.get("uncertainty"),
                "evidence_seconds": parsed.get("evidence_seconds"),
                "raw": row.get("raw"), "failure": row.get("error"),
            }
    return {"scope": "P6_direct_Qwen3VL8B_development_only_not_G2",
            "raw_seal_sha256": sha256(seal_path), "truth_map_sha256": truth_hashes,
            "cases": cases,
            "counts": {arm: {"label_match": sum(row["matches_label"] for row in cases[arm].values()),
                              "valid": sum(row["parse_status"] == "valid" for row in cases[arm].values()),
                              "unknown": sum(row["observed"] == "unknown" for row in cases[arm].values())}
                       for arm in cases},
            "limits": "Net t0-to-t14 label only; reasons and cited frames require manual review. Repeated development geometries are not independent G2 samples."}


def main() -> None:
    parser = argparse.ArgumentParser()
    for name in ("raw_root", "seal", "access_input", "support_input", "truth_root", "output"):
        parser.add_argument("--" + name.replace("_", "-"), required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw_root.resolve() in args.output.resolve().parents:
        raise FileExistsError("score output must be new and outside raw")
    paths = {"access_gate": args.access_input, "support_surface": args.support_input}
    report = score(args.raw_root, args.seal, paths, args.truth_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(report["counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()

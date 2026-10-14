"""Seal raw model-side evidence without reading any expected answers."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from one_session_suite_v0_2 import STAGES, SUITE_VERSION


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    rows = [json.loads(line) for line in args.raw.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows or rows[0].get("kind") != "configuration" or rows[0].get("suite_version") != SUITE_VERSION:
        raise ValueError("unexpected suite version")
    config = rows[0]
    if config.get("dry_run"):
        raise ValueError("cannot seal dry run as model evidence")
    videos = {(row["group"], row["video"]) for row in rows if row.get("kind") == "video_input"}
    if len(videos) != 18:
        raise ValueError("expected 18 anonymous videos")
    outputs = [row for row in rows if row.get("kind") in ("model_output", "model_failure")]
    keys = [(row["group"], row["video"], row["stage"]) for row in outputs]
    if len(keys) != len(set(keys)) or any((g, v) not in videos or s not in STAGES for g, v, s in keys):
        raise ValueError("duplicate or out-of-roster call")
    expected = len(videos) * len(STAGES)
    if len(outputs) != expected and not args.allow_partial:
        raise ValueError(f"incomplete full matrix: {len(outputs)}/{expected}")
    counts = Counter(row["stage"] for row in outputs)
    status = Counter(row.get("validation", {}).get("status", "runtime_failure") for row in outputs)
    seal = {"scope": "development_only_not_G2", "utc": datetime.now(timezone.utc).isoformat(),
            "suite_version": SUITE_VERSION, "configuration_sha256": config["configuration_sha256"],
            "package_sha256": sha(args.package), "raw_sha256": sha(args.raw),
            "videos": len(videos), "expected_calls": expected, "recorded_calls": len(outputs),
            "complete": len(outputs) == expected, "stage_counts": dict(counts),
            "validation_status_counts": dict(status),
            "total_elapsed_ms": sum(row.get("elapsed_ms", 0) for row in outputs),
            "total_input_tokens": sum(row.get("input_tokens", 0) for row in outputs),
            "total_output_tokens": sum(row.get("output_tokens", 0) for row in outputs),
            "output_cap_hits": sum(bool(row.get("hit_output_cap")) for row in outputs)}
    args.output.write_text(json.dumps(seal, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"seal": str(args.output), "complete": seal["complete"],
                      "recorded_calls": seal["recorded_calls"], "raw_sha256": seal["raw_sha256"]}))


if __name__ == "__main__":
    main()

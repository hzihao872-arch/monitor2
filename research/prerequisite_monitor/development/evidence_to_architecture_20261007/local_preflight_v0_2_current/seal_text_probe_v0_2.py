"""Seal complete TOPReward task-text curves without labels or expected outcomes."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", required=True, type=Path)
    parser.add_argument("--raw-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    builder_manifest = json.loads((args.input_root / "text_probe_manifest.json").read_text(encoding="utf-8"))
    variants = builder_manifest["variants"]
    cells, file_records, status = {}, [], Counter()
    for variant in variants:
        for group in ("group_01", "group_02"):
            input_dir = args.input_root / variant / group / "model_input"
            raw_dir = args.raw_root / variant / group
            expected = {row["video"]: row for row in (
                json.loads(line) for line in (input_dir / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip())}
            if len(expected) != 9:
                raise ValueError("expected nine videos")
            journal = raw_dir / "native_calls.jsonl"
            if not journal.is_file():
                cells[f"{variant}/{group}"] = {"recorded": 0, "status": "missing"}
                continue
            rows = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines() if line.strip()]
            config = [row for row in rows if row.get("kind") == "configuration"]
            if (len(config) != 1 or config[0].get("method") != "TOPReward" or
                config[0].get("manifest_sha256") != sha(input_dir / "manifest.jsonl")):
                raise ValueError("native configuration mismatch")
            outcomes = [row for row in rows if row.get("kind") in ("native_result", "native_failure")]
            names = [row.get("video") for row in outcomes]
            if len(names) != len(set(names)) or any(name not in expected for name in names):
                raise ValueError("duplicate or unexpected native outcome")
            for row in outcomes:
                if row["kind"] == "native_failure":
                    status["native_failure"] += 1
                    continue
                video = row["video"]
                values = row.get("prefix_rewards")
                if (row.get("instruction") != expected[video]["instruction"] or
                    row.get("video_sha256") != expected[video]["sha256"] or
                    row.get("prefix_lengths") != list(range(1, 16)) or
                    not isinstance(values, list) or len(values) != 15 or
                    any(not isinstance(x, (float, int)) or not math.isfinite(x) for x in values)):
                    raise ValueError("native curve or input mismatch")
                payload = raw_dir / f"{Path(video).stem}.json"
                if row.get("result_sha256") != sha(payload):
                    raise ValueError("native result SHA mismatch")
                status["native_result"] += 1
            cells[f"{variant}/{group}"] = {"recorded": len(outcomes),
                                          "status": "complete" if len(outcomes) == 9 else "partial"}
    expected_jobs = 18 * len(variants)
    actual_jobs = sum(cell["recorded"] for cell in cells.values())
    if actual_jobs != expected_jobs and not args.allow_partial:
        raise ValueError(f"native probe incomplete: {actual_jobs}/{expected_jobs}")
    for path in sorted(args.raw_root.rglob("*")):
        if path.is_file():
            file_records.append({"path": path.relative_to(args.raw_root).as_posix(),
                                 "sha256": sha(path), "size_bytes": path.stat().st_size})
    seal = {"scope": "development_task_text_diagnostic_not_native_P0_not_G2",
            "utc": datetime.now(timezone.utc).isoformat(),
            "input_manifest_sha256": sha(args.input_root / "text_probe_manifest.json"),
            "variants": variants, "expected_jobs": expected_jobs,
            "recorded_jobs": actual_jobs, "complete": actual_jobs == expected_jobs,
            "outcomes": dict(status), "cells": cells, "files": file_records}
    args.output.write_text(json.dumps(seal, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"recorded_jobs": actual_jobs, "expected_jobs": expected_jobs,
                      "complete": seal["complete"]}))


if __name__ == "__main__":
    main()

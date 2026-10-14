"""Seal all nine anonymous native outcomes in each of four development cells."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ARMS = ("access_gate", "support_surface")
METHODS = ("topreward", "robometer")
VIDEOS = {f"{i:04}.mp4" for i in range(1, 10)}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def input_rows(path: Path, expected_count: int = 9) -> dict:
    rows = [json.loads(line) for line in (path / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    videos = {f"{i:04}.mp4" for i in range(1, expected_count + 1)}
    if len(rows) != expected_count or {row["video"] for row in rows} != videos:
        raise ValueError(f"input must contain {expected_count} unique anonymous videos")
    for row in rows:
        if sha256(path / row["video"]) != row["sha256"]:
            raise ValueError("input video SHA mismatch: " + row["video"])
    return {row["video"]: row for row in rows}


def valid_curve(value: object) -> bool:
    return (isinstance(value, list) and len(value) == 15 and
            all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) for x in value))


def summarize(raw_root: Path, inputs: dict[str, Path], expected_count: int = 9) -> dict:
    videos = {f"{i:04}.mp4" for i in range(1, expected_count + 1)}
    expected = {arm: input_rows(inputs[arm], expected_count) for arm in ARMS}
    cells = {}
    total_results = total_failures = 0
    all_complete = True
    for arm in ARMS:
        for method in METHODS:
            key = f"{arm}/{method}"
            path = raw_root / key / "native_calls.jsonl"
            issues = []
            if not path.is_file():
                cells[key] = {"status": "incomplete", "issues": ["missing journal"], "result_count": 0, "failure_count": 0}
                all_complete = False
                continue
            try:
                rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            except (ValueError, UnicodeDecodeError) as exc:
                cells[key] = {"status": "incomplete", "issues": [f"bad journal: {exc}"], "result_count": 0, "failure_count": 0}
                all_complete = False
                continue
            video_inputs = [row for row in rows if row.get("kind") == "video_input"]
            outcomes = [row for row in rows if row.get("kind") in ("native_result", "native_failure")]
            probes = [row for row in rows if row.get("kind") == "native_decoder_probe"]
            if len(video_inputs) != expected_count or {row.get("video") for row in video_inputs} != videos:
                issues.append("video inputs missing or duplicated")
            if any(row.get("sha256") != expected[arm].get(row.get("video"), {}).get("sha256") for row in video_inputs):
                issues.append("video input SHA differs")
            if len(outcomes) != expected_count or {row.get("video") for row in outcomes} != videos:
                issues.append("outcomes missing or duplicated")
            if method == "robometer" and (len(probes) != expected_count or {row.get("video") for row in probes} != videos or
                    any(row.get("same_pixels_as_manifest") is not True or row.get("frame_count") != 15 for row in probes)):
                issues.append("native decoder hashes or count differ")
            for row in outcomes:
                if row.get("video") not in expected[arm]:
                    continue
                if row["kind"] == "native_failure":
                    error = str(row.get("error", "")).lower()
                    if any(term in error for term in ("decoder", "decoded", "pixel hash")):
                        issues.append(f"decode or pixel identity failed: {row['video']}")
                    continue
                if row.get("video_sha256") != expected[arm][row["video"]]["sha256"]:
                    issues.append(f"result video SHA differs: {row['video']}")
                if method == "topreward":
                    if not valid_curve(row.get("prefix_rewards")) or row.get("prefix_lengths") != list(range(1, 16)):
                        issues.append(f"bad prefix curve: {row['video']}")
                    result_file = path.parent / (Path(row["video"]).stem + ".json")
                    if not result_file.is_file() or sha256(result_file) != row.get("result_sha256"):
                        issues.append(f"result file SHA differs: {row['video']}")
                elif not valid_curve(row.get("progress")) or not valid_curve(row.get("success_head")):
                    issues.append(f"bad progress/success curve: {row['video']}")
                else:
                    stem = Path(row["video"]).stem
                    for name, field in ((f"{stem}.npy", "progress_sha256"), (f"{stem}_success_probs.npy", "success_sha256")):
                        file = path.parent / name
                        if field not in row or not file.is_file() or sha256(file) != row[field]:
                            issues.append(f"native file SHA differs: {name}")
            result_count = sum(row["kind"] == "native_result" for row in outcomes)
            failure_count = sum(row["kind"] == "native_failure" for row in outcomes)
            total_results += result_count
            total_failures += failure_count
            cells[key] = {"status": "incomplete" if issues else "complete", "issues": sorted(set(issues)),
                          "result_count": result_count, "failure_count": failure_count}
            all_complete &= not issues
    return {"status": "incomplete" if not all_complete else ("complete_with_failures" if total_failures else "complete"),
            "cells": cells, "total_results": total_results, "total_failures": total_failures}


def seal(raw_root: Path, seal_path: Path, inputs: dict[str, Path], expected_count: int = 9) -> dict:
    raw_root, seal_path = raw_root.resolve(), seal_path.resolve()
    if seal_path.exists() or seal_path == raw_root or raw_root in seal_path.parents:
        raise ValueError("seal must be new and outside raw root")
    summary = summarize(raw_root, inputs, expected_count)
    files = sorted(path for path in raw_root.rglob("*") if path.is_file())
    report = {**summary, "scope": "fresh_dev_v2_p0_native" if expected_count == 9 else "P3_static_end_state_exploratory",
              "expected_count_per_cell": expected_count, "sealed_utc": datetime.now(timezone.utc).isoformat(),
              "files": [{"path": path.relative_to(raw_root).as_posix(), "sha256": sha256(path),
                         "size_bytes": path.stat().st_size} for path in files]}
    seal_path.parent.mkdir(parents=True, exist_ok=True)
    seal_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    return report


def verify(raw_root: Path, seal_path: Path, inputs: dict[str, Path], expected_count: int = 9) -> dict:
    report = json.loads(seal_path.read_text(encoding="utf-8"))
    actual = {path.relative_to(raw_root).as_posix(): path for path in raw_root.rglob("*") if path.is_file()}
    expected = {item["path"]: item for item in report["files"]}
    if set(actual) != set(expected):
        raise ValueError("raw file inventory changed")
    for name, path in actual.items():
        if path.stat().st_size != expected[name]["size_bytes"] or sha256(path) != expected[name]["sha256"]:
            raise ValueError("raw file SHA changed: " + name)
    if report.get("expected_count_per_cell") != expected_count or summarize(raw_root, inputs, expected_count) != {key: report[key] for key in ("status", "cells", "total_results", "total_failures")}:
        raise ValueError("raw summary changed")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", required=True, type=Path)
    parser.add_argument("--seal", required=True, type=Path)
    parser.add_argument("--access-input", required=True, type=Path)
    parser.add_argument("--support-input", required=True, type=Path)
    parser.add_argument("--expected-count", type=int, choices=(4, 9), default=9)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    inputs = {"access_gate": args.access_input, "support_surface": args.support_input}
    report = verify(args.raw_root, args.seal, inputs, args.expected_count) if args.verify else seal(args.raw_root, args.seal, inputs, args.expected_count)
    print(json.dumps({key: report[key] for key in ("status", "cells", "total_results", "total_failures")}, ensure_ascii=False))
    if report["status"] == "incomplete":
        raise SystemExit(2)


if __name__ == "__main__":
    main()

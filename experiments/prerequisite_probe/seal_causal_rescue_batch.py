"""Seal L1/L2 raw native outputs before opening local truth mappings."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ARMS = ("L1", "L2")
METHODS = ("topreward", "robometer")
VIDEOS = {f"{i:04}.mp4" for i in range(1, 7)}


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def summarize(raw_root: Path) -> dict:
    cells = {}
    total_results = total_failures = 0
    complete = True
    for arm in ARMS:
        for method in METHODS:
            key = f"{arm}/{method}"
            journal = raw_root / key / "native_calls.jsonl"
            if not journal.is_file():
                cells[key] = {"status": "missing_journal", "result_count": 0, "failure_count": 0}
                complete = False
                continue
            rows = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines() if line.strip()]
            video_inputs = [row.get("video") for row in rows if row.get("kind") == "video_input"]
            outcomes = [row for row in rows if row.get("kind") in ("native_result", "native_failure")]
            probes = [row for row in rows if row.get("kind") == "native_decoder_probe"]
            result_count = sum(row["kind"] == "native_result" for row in outcomes)
            failure_count = sum(row["kind"] == "native_failure" for row in outcomes)
            total_results += result_count
            total_failures += failure_count
            outcome_videos = [row.get("video") for row in outcomes]
            shape_ok = all(
                len(row.get("prefix_rewards", [])) == 15 if method == "topreward"
                else len(row.get("progress", [])) == 15 and len(row.get("success_head", [])) == 15
                for row in outcomes if row["kind"] == "native_result"
            )
            decoder_ok = (method != "robometer" or
                          (len(probes) == 6 and {row.get("video") for row in probes} == VIDEOS and
                           all(row.get("same_pixels_as_manifest") is True and
                               row.get("frame_count") == 15 for row in probes)))
            valid = (len(video_inputs) == 6 and set(video_inputs) == VIDEOS and
                     len(outcome_videos) == 6 and set(outcome_videos) == VIDEOS and
                     shape_ok and decoder_ok)
            complete &= valid
            cells[key] = {"status": "complete" if valid else "incomplete",
                          "input_count": len(video_inputs), "result_count": result_count,
                          "failure_count": failure_count, "shape_ok": shape_ok,
                          "native_decoder_ok": decoder_ok}
    return {"status": "incomplete" if not complete else
            ("complete_with_failures" if total_failures else "complete"),
            "cells": cells, "total_results": total_results, "total_failures": total_failures}


def seal(raw_root: Path, seal_path: Path) -> dict:
    raw_root, seal_path = raw_root.resolve(), seal_path.resolve()
    if seal_path.exists() or seal_path == raw_root or raw_root in seal_path.parents:
        raise ValueError("new seal must be outside raw root")
    summary = summarize(raw_root)
    files = sorted(path for path in raw_root.rglob("*") if path.is_file())
    manifest = {**summary, "scope": "causal_rescue_first_batch_development",
                "sealed_utc": datetime.now(timezone.utc).isoformat(),
                "files": [{"path": path.relative_to(raw_root).as_posix(),
                           "sha256": sha256(path), "size_bytes": path.stat().st_size} for path in files]}
    seal_path.parent.mkdir(parents=True, exist_ok=True)
    seal_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def verify(raw_root: Path, seal_path: Path) -> dict:
    raw_root = raw_root.resolve()
    manifest = json.loads(seal_path.read_text(encoding="utf-8"))
    actual = {path.relative_to(raw_root).as_posix(): path for path in raw_root.rglob("*") if path.is_file()}
    expected = {item["path"]: item for item in manifest["files"]}
    if set(actual) != set(expected):
        raise ValueError("raw file set changed after seal")
    for name, path in actual.items():
        if sha256(path) != expected[name]["sha256"] or path.stat().st_size != expected[name]["size_bytes"]:
            raise ValueError(f"raw file changed after seal: {name}")
    if summarize(raw_root) != {key: manifest[key] for key in ("status", "cells", "total_results", "total_failures")}:
        raise ValueError("raw journal summary changed after seal")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", required=True, type=Path)
    parser.add_argument("--seal", required=True, type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    report = verify(args.raw_root, args.seal) if args.verify else seal(args.raw_root, args.seal)
    print(json.dumps({key: report[key] for key in ("status", "cells", "total_results", "total_failures")}))


if __name__ == "__main__":
    main()

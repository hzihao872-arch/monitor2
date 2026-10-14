"""Seal a two-arm, nine-video TOPReward instruction intervention without truth."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def expected_rows(path: Path) -> dict[str, dict]:
    if path.name != "model_input":
        raise ValueError("only model_input allowed")
    rows = [json.loads(line) for line in (path / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    videos = {f"{i:04}.mp4" for i in range(1, 10)}
    if len(rows) != 9 or {row.get("video") for row in rows} != videos:
        raise ValueError("nine unique videos required")
    for row in rows:
        if sha256(path / row["video"]) != row["sha256"]:
            raise ValueError("video SHA mismatch")
    return {row["video"]: row for row in rows}


def summarize(raw_root: Path, inputs: dict[str, Path]) -> dict:
    cells = {}
    for arm in ("access_gate", "support_surface"):
        expected = expected_rows(inputs[arm])
        folder = raw_root / arm / "topreward"
        journal = folder / "native_calls.jsonl"
        issues = []
        if not journal.is_file():
            cells[arm] = {"status": "incomplete", "issues": ["missing journal"], "results": 0, "failures": 0}
            continue
        try:
            rows = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines() if line.strip()]
        except (ValueError, UnicodeDecodeError) as exc:
            cells[arm] = {"status": "incomplete", "issues": [f"bad JSONL: {exc}"], "results": 0, "failures": 0}
            continue
        configs = [r for r in rows if r.get("kind") == "configuration"]
        if len(configs) != 1 or configs[0].get("method") != "TOPReward" or configs[0].get("dry_run") is not False:
            issues.append("invalid run configuration")
        elif configs[0].get("manifest_sha256") != sha256(inputs[arm] / "manifest.jsonl"):
            issues.append("manifest SHA differs")
        video_inputs = [r for r in rows if r.get("kind") == "video_input"]
        outcomes = [r for r in rows if r.get("kind") in ("native_result", "native_failure")]
        for label, selected in (("video inputs", video_inputs), ("outcomes", outcomes)):
            names = [r.get("video") for r in selected]
            if len(names) != 9 or set(names) != set(expected) or len(set(names)) != 9:
                issues.append(label + " missing, duplicated, or unexpected")
        for item in video_inputs:
            if item.get("video") in expected and item.get("sha256") != expected[item["video"]]["sha256"]:
                issues.append("video input SHA differs: " + item["video"])
        for item in outcomes:
            video = item.get("video")
            if video not in expected:
                continue
            if item["kind"] == "native_failure":
                continue
            curve = item.get("prefix_rewards")
            if (item.get("instruction") != expected[video]["instruction"] or
                item.get("video_sha256") != expected[video]["sha256"] or
                item.get("prefix_lengths") != list(range(1, 16)) or
                not isinstance(curve, list) or len(curve) != 15 or
                any(not isinstance(value, (int, float)) or isinstance(value, bool) or
                    not math.isfinite(value) for value in curve)):
                issues.append("invalid native result: " + video)
            file = folder / (Path(video).stem + ".json")
            if not file.is_file() or item.get("result_sha256") != sha256(file):
                issues.append("result file SHA differs: " + video)
            else:
                try:
                    payload = json.loads(file.read_text(encoding="utf-8"))
                    if any(payload.get(key) != item.get(key) for key in
                           ("video", "instruction", "video_sha256", "prefix_lengths", "prefix_rewards")):
                        issues.append("result file content differs: " + video)
                except (ValueError, UnicodeDecodeError):
                    issues.append("result file JSON invalid: " + video)
        cells[arm] = {"status": "incomplete" if issues else "complete", "issues": sorted(set(issues)),
                      "results": sum(r["kind"] == "native_result" for r in outcomes),
                      "failures": sum(r["kind"] == "native_failure" for r in outcomes)}
    incomplete = any(item["status"] == "incomplete" for item in cells.values())
    return {"status": "incomplete" if incomplete else
            ("complete_with_failures" if any(item["failures"] for item in cells.values()) else "complete"),
            "cells": cells}


def seal(raw_root: Path, path: Path, inputs: dict[str, Path]) -> dict:
    if path.exists() or raw_root.resolve() in path.resolve().parents:
        raise ValueError("seal must be new and outside raw")
    summary = summarize(raw_root, inputs)
    files = sorted(p for p in raw_root.rglob("*") if p.is_file())
    report = {**summary, "scope": "P4_TOPReward_instruction_intervention_exploratory",
              "sealed_utc": datetime.now(timezone.utc).isoformat(),
              "input_manifest_sha256": {arm: sha256(source / "manifest.jsonl") for arm, source in inputs.items()},
              "files": [{"path": p.relative_to(raw_root).as_posix(), "sha256": sha256(p),
                         "size_bytes": p.stat().st_size} for p in files]}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def verify(raw_root: Path, path: Path, inputs: dict[str, Path]) -> dict:
    report = json.loads(path.read_text(encoding="utf-8"))
    files = {p.relative_to(raw_root).as_posix(): p for p in raw_root.rglob("*") if p.is_file()}
    expected = {entry["path"]: entry for entry in report["files"]}
    if set(files) != set(expected):
        raise ValueError("file inventory differs")
    for name, actual in files.items():
        if actual.stat().st_size != expected[name]["size_bytes"] or sha256(actual) != expected[name]["sha256"]:
            raise ValueError("file SHA differs: " + name)
    summary = summarize(raw_root, inputs)
    if (summary != {key: report[key] for key in summary} or
        report.get("input_manifest_sha256") != {arm: sha256(source / "manifest.jsonl") for arm, source in inputs.items()}):
        raise ValueError("summary or input manifest differs")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    for name in ("raw_root", "seal", "access_input", "support_input"):
        parser.add_argument("--" + name.replace("_", "-"), required=True, type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    inputs = {"access_gate": args.access_input, "support_surface": args.support_input}
    result = verify(args.raw_root, args.seal, inputs) if args.verify else seal(args.raw_root, args.seal, inputs)
    print(json.dumps({key: result[key] for key in ("status", "cells")}))
    if result["status"] == "incomplete":
        raise SystemExit(2)


if __name__ == "__main__":
    main()

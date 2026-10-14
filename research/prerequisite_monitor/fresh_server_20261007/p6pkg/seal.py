"""Seal and verify P6 direct baseline raw answers without accessing truth."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .run import DIRECT_PROMPT, MAX_NEW_TOKENS, SECONDS, SIZE, input_rows, parse, prompt_for, sample_frames, sha256


def summarize(calls: Path, expected_count: int, paths: dict[str, Path]) -> dict:
    if not calls.is_file():
        return {"status": "incomplete", "issues": ["missing calls.jsonl"],
                "result_count": 0, "failure_count": 0, "invalid_parse_count": 0}
    try:
        rows = [json.loads(line) for line in calls.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (ValueError, UnicodeDecodeError) as exc:
        return {"status": "incomplete", "issues": [f"bad JSONL: {exc}"],
                "result_count": 0, "failure_count": 0, "invalid_parse_count": 0}
    issues = []
    configs = [row for row in rows if row.get("kind") == "configuration"]
    if (len(configs) != 1 or configs[0].get("scope") != "P6_direct_Qwen3VL8B_development" or
        configs[0].get("dry_run") is not False or
        configs[0].get("prompt_template_sha256") != hashlib.sha256(DIRECT_PROMPT.encode()).hexdigest() or
        configs[0].get("frame_seconds") != list(SECONDS) or configs[0].get("resize") != list(SIZE) or
        configs[0].get("max_new_tokens") != MAX_NEW_TOKENS or
        configs[0].get("pilot") is not (expected_count == 2)):
        issues.append("configuration or prompt template differs")
    inputs = [row for row in rows if row.get("kind") == "video_input"]
    outcomes = [row for row in rows if row.get("kind") in ("model_output", "model_failure")]
    keys_in = [(row.get("arm"), row.get("video")) for row in inputs]
    keys_out = [(row.get("arm"), row.get("video")) for row in outcomes]
    if (len(keys_in) != expected_count or len(set(keys_in)) != expected_count or
        len(keys_out) != expected_count or len(set(keys_out)) != expected_count or set(keys_in) != set(keys_out)):
        issues.append("inputs/outcomes missing, duplicated, or mismatched")
    expected = {}
    for arm, path in paths.items():
        manifest, clips = input_rows(path)
        selected = manifest[:1] if expected_count == 2 else manifest
        for item in selected:
            clip = clips[item["video"]]
            _, source_hashes, resized_hashes = sample_frames(path / item["video"], clip["decoded_rgb_sha256"])
            expected[(arm, item["video"])] = (item, source_hashes, resized_hashes)
    if set(keys_in) != set(expected):
        issues.append("unexpected input inventory")
    for row in inputs:
        pair = expected.get((row.get("arm"), row.get("video")))
        if not pair:
            continue
        item, source_hashes, resized_hashes = pair
        if (row.get("video_sha256") != item["sha256"] or
            row.get("frame_seconds") != list(SECONDS) or
            row.get("frame_sha256") != source_hashes or
            row.get("resized_frame_sha256") != resized_hashes or
            row.get("prompt_sha256") != hashlib.sha256(prompt_for(item["instruction"]).encode()).hexdigest()):
            issues.append("video, frame, or prompt SHA differs")
    for row in outcomes:
        if row["kind"] == "model_output" and (not isinstance(row.get("raw"), str) or
                                               row.get("parse_status") not in ("valid", "invalid")):
            issues.append("model output lacks raw text or parse status")
        elif row["kind"] == "model_output":
            parsed_again = parse(row["raw"])
            if parsed_again["parse_status"] != row["parse_status"] or (
                row["parse_status"] == "valid" and parsed_again["parsed"] != row.get("parsed")
            ):
                issues.append("parsed answer differs from raw text")
        if row["kind"] == "model_failure" and not isinstance(row.get("error"), str):
            issues.append("model failure lacks error")
    results = sum(row["kind"] == "model_output" for row in outcomes)
    failures = sum(row["kind"] == "model_failure" for row in outcomes)
    invalid = sum(row["kind"] == "model_output" and row.get("parse_status") == "invalid" for row in outcomes)
    return {"status": "incomplete" if issues else ("complete_with_failures" if failures else "complete"),
            "issues": sorted(set(issues)), "result_count": results,
            "failure_count": failures, "invalid_parse_count": invalid}


def seal(raw_root: Path, seal_path: Path, expected_count: int, paths: dict[str, Path]) -> dict:
    if seal_path.exists() or raw_root == seal_path or raw_root in seal_path.parents:
        raise ValueError("new seal must be outside raw root")
    summary = summarize(raw_root / "calls.jsonl", expected_count, paths)
    files = sorted(path for path in raw_root.rglob("*") if path.is_file())
    report = {**summary, "scope": "P6_direct_Qwen3VL8B_development", "sealed_utc": datetime.now(timezone.utc).isoformat(),
              "expected_count": expected_count,
              "files": [{"path": path.relative_to(raw_root).as_posix(), "sha256": sha256(path),
                         "size_bytes": path.stat().st_size} for path in files]}
    seal_path.parent.mkdir(parents=True, exist_ok=True)
    seal_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def verify(raw_root: Path, seal_path: Path, expected_count: int, paths: dict[str, Path]) -> dict:
    report = json.loads(seal_path.read_text(encoding="utf-8"))
    actual = {path.relative_to(raw_root).as_posix(): path for path in raw_root.rglob("*") if path.is_file()}
    expected = {item["path"]: item for item in report["files"]}
    if set(actual) != set(expected):
        raise ValueError("raw file inventory changed")
    for name, path in actual.items():
        if path.stat().st_size != expected[name]["size_bytes"] or sha256(path) != expected[name]["sha256"]:
            raise ValueError("raw file SHA changed: " + name)
    summary = summarize(raw_root / "calls.jsonl", expected_count, paths)
    if report["scope"] != "P6_direct_Qwen3VL8B_development" or report["expected_count"] != expected_count or summary != {key: report[key] for key in summary}:
        raise ValueError("P6 summary changed")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", required=True, type=Path)
    parser.add_argument("--seal", required=True, type=Path)
    parser.add_argument("--access-input", required=True, type=Path)
    parser.add_argument("--support-input", required=True, type=Path)
    parser.add_argument("--expected-count", required=True, type=int, choices=(2, 18))
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    paths = {"access_gate": args.access_input, "support_surface": args.support_input}
    report = verify(args.raw_root, args.seal, args.expected_count, paths) if args.verify else seal(args.raw_root, args.seal, args.expected_count, paths)
    print(json.dumps({key: report[key] for key in ("status", "issues", "result_count", "failure_count", "invalid_parse_count")}))
    if report["status"] == "incomplete":
        raise SystemExit(2)


if __name__ == "__main__":
    main()

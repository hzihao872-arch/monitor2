"""Independent raw seal for P5 targeted visual or future-route outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .p5_qwen import PROMPTS, SECONDS, inputs, prompt_for


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def summarize(calls: Path, expected_count: int, input_paths: dict[str, Path] | None = None) -> dict:
    issues = []
    if not calls.is_file():
        return {"status": "incomplete", "issues": ["missing calls"], "result_count": 0, "failure_count": 0}
    try:
        rows = [json.loads(line) for line in calls.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (ValueError, UnicodeDecodeError) as exc:
        return {"status": "incomplete", "issues": [f"bad JSONL: {exc}"], "result_count": 0, "failure_count": 0}
    configs = [row for row in rows if row.get("kind") == "configuration"]
    stage = configs[0].get("stage") if len(configs) == 1 else None
    if stage not in PROMPTS:
        issues.append("missing or invalid configuration stage")
    video_inputs = [row for row in rows if row.get("kind") == "video_input"]
    outcomes = [row for row in rows if row.get("kind") in ("model_output", "model_failure")]
    keys_in = [(row.get("arm"), row.get("video")) for row in video_inputs]
    keys_out = [(row.get("arm"), row.get("video")) for row in outcomes]
    if len(keys_in) != expected_count or len(set(keys_in)) != expected_count:
        issues.append("video inputs missing or duplicated")
    if any(sum(row.get("arm") == arm for row in video_inputs) != expected_count // 2
           for arm in ("access_gate", "support_surface")):
        issues.append("arm input counts differ")
    if len(keys_out) != expected_count or len(set(keys_out)) != expected_count or set(keys_in) != set(keys_out):
        issues.append("outcomes missing, duplicated, or mismatched")
    for row in video_inputs:
        if row.get("frame_seconds") != list(SECONDS) or len(row.get("frame_sha256", [])) != 9 or len(row.get("resized_frame_sha256", [])) not in (0, 9):
            issues.append("frame sample shape differs")
    for row in outcomes:
        if row["kind"] == "model_output" and (not isinstance(row.get("raw"), str) or row.get("parse_status") not in ("valid", "invalid")):
            issues.append("raw model output missing")
    if input_paths:
        expected = {}
        for arm, path in input_paths.items():
            media = json.loads((path / "media_hashes.json").read_text(encoding="utf-8"))
            clips = {entry["video"]: entry for entry in media["clips"]}
            for item in inputs(path):
                expected[(arm, item["video"])] = (item, clips[item["video"]])
        for row in video_inputs:
            pair = expected.get((row.get("arm"), row.get("video")))
            if not pair:
                issues.append("unexpected video")
                continue
            item, clip = pair
            if row.get("video_sha256") != item["sha256"] or row.get("frame_sha256") != [clip["decoded_rgb_sha256"][t] for t in SECONDS]:
                issues.append("video or frame SHA differs")
            if stage in PROMPTS:
                prompt = prompt_for(stage, row["arm"], item["instruction"])
                if row.get("prompt_sha256") != hashlib.sha256(prompt.encode()).hexdigest():
                    issues.append("prompt SHA differs")
    result_count = sum(row["kind"] == "model_output" for row in outcomes)
    failure_count = sum(row["kind"] == "model_failure" for row in outcomes)
    return {"status": "incomplete" if issues else ("complete_with_failures" if failure_count else "complete"),
            "stage": stage, "issues": sorted(set(issues)), "result_count": result_count, "failure_count": failure_count}


def seal(raw_root: Path, seal_path: Path, expected_count: int, input_paths: dict[str, Path]) -> dict:
    if seal_path.exists() or raw_root == seal_path or raw_root in seal_path.parents:
        raise ValueError("new seal must be outside raw root")
    summary = summarize(raw_root / "calls.jsonl", expected_count, input_paths)
    files = sorted(path for path in raw_root.rglob("*") if path.is_file())
    report = {**summary, "scope": "P5_targeted_Qwen_diagnostic_exploratory", "sealed_utc": datetime.now(timezone.utc).isoformat(),
              "expected_count": expected_count,
              "files": [{"path": path.relative_to(raw_root).as_posix(), "sha256": sha256(path),
                         "size_bytes": path.stat().st_size} for path in files]}
    seal_path.parent.mkdir(parents=True, exist_ok=True)
    seal_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def verify(raw_root: Path, seal_path: Path, expected_count: int, input_paths: dict[str, Path]) -> dict:
    report = json.loads(seal_path.read_text(encoding="utf-8"))
    actual = {path.relative_to(raw_root).as_posix(): path for path in raw_root.rglob("*") if path.is_file()}
    expected = {item["path"]: item for item in report["files"]}
    if set(actual) != set(expected):
        raise ValueError("raw file inventory changed")
    for name, path in actual.items():
        if path.stat().st_size != expected[name]["size_bytes"] or sha256(path) != expected[name]["sha256"]:
            raise ValueError("raw file SHA changed: " + name)
    summary = summarize(raw_root / "calls.jsonl", expected_count, input_paths)
    if report["expected_count"] != expected_count or summary != {key: report[key] for key in summary}:
        raise ValueError("P5 summary changed")
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
    input_paths = {"access_gate": args.access_input, "support_surface": args.support_input}
    report = verify(args.raw_root, args.seal, args.expected_count, input_paths) if args.verify else seal(args.raw_root, args.seal, args.expected_count, input_paths)
    print(json.dumps({key: report[key] for key in ("status", "stage", "issues", "result_count", "failure_count")}))
    if report["status"] == "incomplete":
        raise SystemExit(2)


if __name__ == "__main__":
    main()

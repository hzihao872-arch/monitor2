"""Hash raw pilot outputs before any truth-side scoring or evidence review."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .run_monitor_qwen import sha256


JOURNALS = ("paired.jsonl", "topreward/native_calls.jsonl",
            "robometer/native_calls.jsonl")


def records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def counts(raw_root: Path) -> dict:
    paired = records(raw_root / JOURNALS[0])
    top = records(raw_root / JOURNALS[1])
    robo = records(raw_root / JOURNALS[2])
    return {
        "paired_visual_calls": sum(row.get("kind") == "visual_call" for row in paired),
        "paired_decisions": sum(row.get("kind") == "pair_decision" for row in paired),
        "topreward_results": sum(row.get("kind") == "native_result" for row in top),
        "topreward_failures": sum(row.get("kind") == "native_failure" for row in top),
        "robometer_results": sum(row.get("kind") == "native_result" for row in robo),
        "robometer_failures": sum(row.get("kind") == "native_failure" for row in robo),
    }


def seal(raw_root: Path, output: Path) -> dict:
    raw_root, output = raw_root.resolve(), output.resolve()
    if output.exists() or output == raw_root or raw_root in output.parents:
        raise ValueError("seal must be a new file outside raw output")
    for name in JOURNALS:
        if not (raw_root / name).is_file():
            raise FileNotFoundError(raw_root / name)
    files = sorted(path for path in raw_root.rglob("*") if path.is_file())
    summary = counts(raw_root)
    manifest = {
        "status": "complete" if (summary["paired_visual_calls"] == 24 and
                                 summary["paired_decisions"] == 12 and
                                 summary["topreward_results"] + summary["topreward_failures"] == 6 and
                                 summary["robometer_results"] + summary["robometer_failures"] == 6)
        else "partial_sealed",
        "scope": "single_scene_development_pilot",
        "sealed_utc": datetime.now(timezone.utc).isoformat(),
        "counts": summary,
        "files": [{"path": path.relative_to(raw_root).as_posix(), "sha256": sha256(path),
                   "size_bytes": path.stat().st_size} for path in files],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    return manifest


def verify(raw_root: Path, seal_path: Path) -> dict:
    raw_root = raw_root.resolve()
    manifest = json.loads(seal_path.read_text(encoding="utf-8"))
    actual = {path.relative_to(raw_root).as_posix(): path for path in raw_root.rglob("*")
              if path.is_file()}
    expected = {row["path"]: row for row in manifest["files"]}
    if set(actual) != set(expected):
        raise ValueError("raw file set changed after seal")
    for name, path in actual.items():
        if sha256(path) != expected[name]["sha256"] or path.stat().st_size != expected[name]["size_bytes"]:
            raise ValueError(f"raw file changed after seal: {name}")
    if counts(raw_root) != manifest["counts"]:
        raise ValueError("raw counts changed after seal")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", required=True, type=Path)
    parser.add_argument("--seal", required=True, type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = verify(args.raw_root, args.seal) if args.verify else seal(args.raw_root, args.seal)
    print(json.dumps({"status": result["status"], "counts": result["counts"]}))


if __name__ == "__main__":
    main()

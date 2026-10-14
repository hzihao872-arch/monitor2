"""Hash-based provenance for a non-Git research workspace."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from zoneinfo import ZoneInfo


EXCLUDED_FROM_SELF_INVENTORY = frozenset(("manifest.json", "manifest.sha256"))


def sha256_file(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_inventory(root: Path):
    records = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in EXCLUDED_FROM_SELF_INVENTORY:
            continue
        records[relative] = {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
    return records


def _command_output(args):
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    return {"exit_code": result.returncode, "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()}


def _source_inventory(workspace: Path):
    sources = set((workspace / "experiments/prerequisite_probe/fresh_prerequisite").glob("*.py"))
    sources.update((workspace / "experiments/prerequisite_probe/tests").glob("test_fresh_prerequisite_*.py"))
    relative_names = (
        "docs/plans/2026-10-06-fresh-prerequisite-scenes-handoff-plan.md",
        "experiments/prerequisite_probe/evaluation_protocol.md",
        "experiments/prerequisite_probe/probe.py",
        "experiments/prerequisite_probe/produce.py",
        "experiments/prerequisite_probe/flat_square_dev.py",
        "experiments/prerequisite_probe/run_native_single_scene_pilot.py",
        "experiments/prerequisite_probe/run_relation_endpoint_pilot.py",
        "experiments/prerequisite_probe/run_monitor_qwen.py",
        "research/prerequisite_monitor/development/scene_video_next/flat_square_predicate_v1.md",
        "tmp/fresh_robometer_decode.py",
        "tmp/fresh_full_frame_sheets.py",
        "tmp/fresh_confounds.py",
        "tmp/fresh_camera_probe.py",
    )
    sources.update(workspace / name for name in relative_names)
    return {path.relative_to(workspace).as_posix(): {
        "sha256": sha256_file(path), "size_bytes": path.stat().st_size,
    } for path in sorted(sources) if path.is_file()}


def _dry_runs(root):
    records = {}
    for mechanism in ("access_gate", "support_surface"):
        for method in ("topreward", "robometer"):
            path = root / mechanism / "dev_v2" / "validation" / f"dry_run_{method}" / "native_calls.jsonl"
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            records[f"{mechanism}/{method}"] = {
                "journal": path.relative_to(root).as_posix(),
                "sha256": sha256_file(path),
                "dry_run": rows[0].get("dry_run"),
                "video_inputs": sum(row.get("kind") == "video_input" for row in rows),
                "native_results": sum(row.get("kind") == "native_result" for row in rows),
            }
    return records


def build_manifest(root: Path):
    root = root.resolve()
    workspace = root.parents[2]
    import mani_skill
    import sapien

    files = file_inventory(root)
    root_git = _command_output(["git", "-C", str(workspace), "rev-parse", "--is-inside-work-tree"])
    topreward = _command_output(["git", "-C", str(workspace / "research/sources/TOPReward"), "rev-parse", "HEAD"])
    robometer = _command_output(["git", "-C", str(workspace / "research/sources/robometer"), "rev-parse", "HEAD"])
    ffmpeg = _command_output(["ffmpeg", "-version"])
    ffprobe = _command_output(["ffprobe", "-version"])
    return {
        "schema": "fresh_prerequisite_manifest_v1",
        "created_at_shanghai": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
        "workspace": str(workspace),
        "root": str(root),
        "root_is_git_repository": root_git["exit_code"] == 0 and root_git["stdout"] == "true",
        "root_git_probe": root_git,
        "source_repositories": {
            "TOPReward": topreward["stdout"] if topreward["exit_code"] == 0 else None,
            "Robometer": robometer["stdout"] if robometer["exit_code"] == 0 else None,
        },
        "versions": {
            "python": sys.version,
            "mani_skill": mani_skill.__version__,
            "sapien": sapien.__version__,
            "ffmpeg": ffmpeg["stdout"].splitlines()[0],
            "ffprobe": ffprobe["stdout"].splitlines()[0],
        },
        "seeds": {
            "simulation": 20261006, "anonymization_access": 20261007,
            "anonymization_support": 20261008,
            "paired_perturbations": [20261006, 20261007, 20261008],
            "static_search": 20261006,
        },
        "protocol": {"versions": ["access_gate/dev_v2", "support_surface/dev_v2"],
                     "raw_fps": 30, "model_fps": 1, "frames_per_video": 15,
                     "excluded_prototypes": ["access_gate/dev_v1", "support_surface/dev_v1"]},
        "model_inference_count": 0,
        "server_connected": False,
        "blind_review_status": "A_first_answer_received_B_pending_A_necessity_rationale_pending",
        "native_dry_runs": _dry_runs(root),
        "source_files": _source_inventory(workspace),
        "files": files,
        "file_count": len(files),
        "total_file_bytes": sum(record["size_bytes"] for record in files.values()),
    }


def write_manifest(root: Path):
    manifest = build_manifest(root)
    path = root / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    digest = sha256_file(path)
    (root / "manifest.sha256").write_text(f"{digest}  manifest.json\n", encoding="utf-8")
    return {"status": "written", "file_count": manifest["file_count"],
            "total_file_bytes": manifest["total_file_bytes"], "manifest_sha256": digest}


def verify_manifest(root: Path):
    path = root / "manifest.json"
    recorded = json.loads(path.read_text(encoding="utf-8"))
    files = file_inventory(root)
    workspace = root.resolve().parents[2]
    sources = _source_inventory(workspace)
    hash_line = (root / "manifest.sha256").read_text(encoding="utf-8").split()[0]
    issues = []
    if files != recorded["files"]:
        issues.append("root file inventory changed")
    if sources != recorded["source_files"]:
        issues.append("source file inventory changed")
    if hash_line != sha256_file(path):
        issues.append("manifest hash changed")
    return {"status": "pass" if not issues else "fail", "issues": issues,
            "file_count": len(files), "manifest_sha256": sha256_file(path)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.write == args.verify:
        parser.error("choose exactly one of --write or --verify")
    result = write_manifest(args.root) if args.write else verify_manifest(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] == "fail":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

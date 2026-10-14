"""Read-only checks for an already rented server; no model load or download."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path


EXPECTED_INPUT_ZIP = "c99543639e2ac7e8ddf270654d1394f42d6f121021463bf3f452648686183cfa"
EXPECTED_TOP_COMMIT = "4877a0ee5098cbec18485125466631b1dcc4a573"
EXPECTED_ROBO_COMMIT = "352d160389daa964788de1ec933d1925f3a6de4f"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def command(*args) -> dict:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=20,
                                check=False)
        return {"returncode": result.returncode, "stdout": result.stdout.strip()[:3000],
                "stderr": result.stderr.strip()[:1000]}
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


def preflight(args: argparse.Namespace) -> dict:
    base = args.base.resolve()
    input_zip, code_zip = args.input_zip.resolve(), args.code_zip.resolve()
    checks = {}
    checks["existing_base"] = base.is_dir()
    checks["existing_8b_venv"] = (base / ".venv-topreward/bin/python").is_file()
    checks["existing_4b_venv"] = (base / ".venv-robometer/bin/python").is_file()
    model8 = Path(args.model8).resolve()
    model4 = Path(args.model4).resolve()
    checks["existing_8b_config"] = (model8 / "config.json").is_file()
    checks["existing_4b_config"] = (model4 / "config.json").is_file()
    checks["pinned_8b_revision"] = "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b" in str(args.model8)
    checks["pinned_4b_revision"] = "beef63bc914c5c189329d49c6d712d96d632aa34" in str(args.model4)
    checks["input_zip_sha"] = input_zip.is_file() and digest(input_zip) == EXPECTED_INPUT_ZIP
    checks["code_zip_present"] = code_zip.is_file()
    input_members = []
    if checks["input_zip_sha"]:
        with zipfile.ZipFile(input_zip) as archive:
            input_members = sorted(archive.namelist())
            checks["input_zip_integrity"] = archive.testzip() is None
        checks["input_zip_nine_allowed_files"] = input_members == sorted(
            [*(f"{i:04}.mp4" for i in range(1, 7)), "instruction.txt",
             "manifest.jsonl", "media_hashes.json"])
    else:
        checks["input_zip_integrity"] = False
        checks["input_zip_nine_allowed_files"] = False
    code_members = []
    if code_zip.is_file():
        with zipfile.ZipFile(code_zip) as archive:
            code_members = sorted(archive.namelist())
            checks["code_zip_integrity"] = archive.testzip() is None
        checks["code_zip_model_side_only"] = all(
            name.startswith("pilot_pkg/") and not any(
                banned in name.lower() for banned in ("truth", "score", "condition_map", "continuation"))
            for name in code_members)
    else:
        checks["code_zip_integrity"] = False
        checks["code_zip_model_side_only"] = False
    top = base / "research/sources/TOPReward"
    robo = base / "research/sources/robometer_pr33_compat"
    top_git = command("git", "-C", str(top), "rev-parse", "HEAD")
    robo_git = command("git", "-C", str(robo), "rev-parse", "HEAD")
    robo_patch = command("git", "-C", str(robo), "diff", "--", "robometer/utils/save.py")
    checks["topreward_commit"] = top_git.get("stdout") == EXPECTED_TOP_COMMIT
    checks["robometer_compat_base_commit"] = robo_git.get("stdout") == EXPECTED_ROBO_COMMIT
    checks["robometer_compat_patch_present"] = bool(robo_patch.get("stdout"))
    checks["robometer_compat_script"] = (robo / "scripts/example_inference_local.py").is_file()
    checks["topreward_client"] = (top / "topreward/clients/qwen.py").is_file()
    gpu = command("nvidia-smi", "--query-gpu=name,memory.total,memory.free",
                  "--format=csv,noheader,nounits")
    checks["gpu_available"] = gpu.get("returncode") == 0 and bool(gpu.get("stdout"))
    disk = shutil.disk_usage(base) if base.is_dir() else None
    return {"status": "pass" if all(checks.values()) else "fail", "checks": checks,
            "input_members": input_members, "code_members": code_members,
            "input_zip_sha256": digest(input_zip) if input_zip.is_file() else None,
            "code_zip_sha256": digest(code_zip) if code_zip.is_file() else None,
            "top_git": top_git, "robo_git": robo_git,
            "robo_patch_sha256": hashlib.sha256(robo_patch.get("stdout", "").encode()).hexdigest()
            if robo_patch.get("stdout") else None,
            "gpu": gpu,
            "disk_free_bytes": disk.free if disk else None,
            "8b_config_sha256": digest(model8 / "config.json") if checks["existing_8b_config"] else None,
            "4b_config_sha256": digest(model4 / "config.json") if checks["existing_4b_config"] else None,
            "note": "read only; no model loaded, rent, install, or download"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--input-zip", type=Path, required=True)
    parser.add_argument("--code-zip", type=Path, required=True)
    parser.add_argument("--model8", type=Path, required=True)
    parser.add_argument("--model4", type=Path, required=True)
    args = parser.parse_args()
    report = preflight(args)
    print(json.dumps(report, indent=2))
    if report["status"] != "pass":
        raise SystemExit(2)


if __name__ == "__main__":
    main()

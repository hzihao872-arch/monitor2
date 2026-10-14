"""Read-only gate for L1/L2 on the user's existing server."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


TOP_COMMIT = "4877a0ee5098cbec18485125466631b1dcc4a573"
ROBO_COMMIT = "352d160389daa964788de1ec933d1925f3a6de4f"
ROBO_PATCH_SHA256 = "b560da190b4dccaa405684beb2e33a5950fefd035983dc98ae9d02406b9d2fac"
MODEL8_REV = "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b"
MODEL4_REV = "beef63bc914c5c189329d49c6d712d96d632aa34"
VIDEOS = tuple(f"{i:04}.mp4" for i in range(1, 7))
ALLOWED = set(VIDEOS) | {"instruction.txt", "manifest.jsonl", "media_hashes.json"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def inspect_input_zip(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != 9 or set(names) != ALLOWED or archive.testzip() is not None:
            raise ValueError("input ZIP must have exactly nine intact allowed files")
        instruction = archive.read("instruction.txt").decode("utf-8").strip()
        rows = [json.loads(line) for line in archive.read("manifest.jsonl").decode("utf-8").splitlines() if line.strip()]
        media = json.loads(archive.read("media_hashes.json"))
        clips = {entry["video"]: entry for entry in media["clips"]}
        if (len(rows) != 6 or {row["video"] for row in rows} != set(VIDEOS) or
                set(clips) != set(VIDEOS) or media["instruction"] != instruction or
                any(row["instruction"] != instruction for row in rows)):
            raise ValueError("six anonymous rows or one fixed instruction required")
        for row in rows:
            video = row["video"]
            clip = clips[video]
            if (sha256_bytes(archive.read(video)) != row["sha256"] or
                    clip["video_sha256"] != row["sha256"] or
                    len(clip["decoded_rgb_sha256"]) != 15):
                raise ValueError(f"video or pixel manifest mismatch: {video}")
        return {"video_count": 6, "pixel_hash_count": 90,
                "instruction_sha256": sha256_bytes(instruction.encode("utf-8")),
                "video_sha256": {row["video"]: row["sha256"] for row in rows},
                "pixel_hashes": {name: clips[name]["decoded_rgb_sha256"] for name in VIDEOS}}


def command(*args: str, env: dict | None = None) -> dict:
    try:
        result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                                errors="replace", env=env, timeout=30, check=False)
        return {"returncode": result.returncode, "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip()[-1000:]}
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


def weight_checks(model8: Path, model4: Path, manifest_path: Path) -> list[dict]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = {"Qwen/Qwen3-VL-8B-Instruct": (model8, MODEL8_REV),
                "robometer/Robometer-4B": (model4, MODEL4_REV)}
    report = []
    for entry in manifest:
        if entry["repo"] not in expected:
            continue
        model_path, revision = expected[entry["repo"]]
        for item in entry["files"]:
            path = model_path / item["name"]
            found = path.is_file() and path.stat().st_size == item["size"] and sha256(path) == item["sha256"]
            report.append({"repo": entry["repo"], "revision": entry["revision"],
                           "name": item["name"], "match": bool(found and entry["revision"] == revision)})
    return report


def preflight(args: argparse.Namespace) -> dict:
    base, model8, model4 = args.base.resolve(), args.model8.resolve(), args.model4.resolve()
    checks = {}
    details = {}
    checks["existing_base"] = base.is_dir()
    checks["existing_python8"] = (base / ".venv-topreward/bin/python").is_file()
    checks["existing_python4"] = args.python4.is_file()
    checks["checkpoint_revisions"] = MODEL8_REV in str(model8) and MODEL4_REV in str(model4)
    checks["checkpoint_configs"] = (model8 / "config.json").is_file() and (model4 / "config.json").is_file()
    for arm, path, expected_sha in (("L1", args.l1_zip, args.l1_sha), ("L2", args.l2_zip, args.l2_sha)):
        checks[f"{arm}_zip_sha"] = path.is_file() and sha256(path) == expected_sha
        try:
            details[arm] = inspect_input_zip(path) if checks[f"{arm}_zip_sha"] else {}
            checks[f"{arm}_zip_contents"] = bool(details[arm])
        except Exception as exc:
            details[arm] = {"error": str(exc)}
            checks[f"{arm}_zip_contents"] = False
    checks["same_video_bytes_and_pixels"] = bool(details.get("L1", {}).get("video_sha256") ==
        details.get("L2", {}).get("video_sha256") and details.get("L1", {}).get("pixel_hashes") ==
        details.get("L2", {}).get("pixel_hashes") and checks.get("L1_zip_contents") and checks.get("L2_zip_contents"))
    checks["code_zip_sha"] = args.code_zip.is_file() and sha256(args.code_zip) == args.code_sha
    if checks["code_zip_sha"]:
        with zipfile.ZipFile(args.code_zip) as archive:
            names = archive.namelist()
            checks["code_zip_model_side_only"] = (archive.testzip() is None and
                all(name.startswith("pilot_pkg/") and not any(term in name.lower() for term in
                    ("truth", "condition_map", "old_scores", "analyze")) for name in names))
    else:
        checks["code_zip_model_side_only"] = False
    top = base / "research/sources/TOPReward"
    robo = base / "research/sources/robometer_pr33_compat"
    details["top_commit"] = command("git", "-C", str(top), "rev-parse", "HEAD")
    details["robo_commit"] = command("git", "-C", str(robo), "rev-parse", "HEAD")
    details["robo_patch"] = command("git", "-C", str(robo), "diff", "--", "robometer/utils/save.py")
    checks["top_commit"] = details["top_commit"].get("stdout") == TOP_COMMIT
    checks["robo_commit"] = details["robo_commit"].get("stdout") == ROBO_COMMIT
    checks["robo_patch_exact"] = sha256_bytes(details["robo_patch"].get("stdout", "").encode()) == ROBO_PATCH_SHA256
    checks["native_code_paths"] = (top / "topreward/clients/qwen.py").is_file() and (robo / "scripts/example_inference_local.py").is_file()
    details["gpu"] = command("nvidia-smi", "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader,nounits")
    checks["gpu_available"] = details["gpu"].get("returncode") == 0 and bool(details["gpu"].get("stdout"))
    details["disk_free_bytes"] = shutil.disk_usage(base).free if base.is_dir() else None
    checks["disk_at_least_5gib"] = details["disk_free_bytes"] is not None and details["disk_free_bytes"] >= 5 * 1024**3
    expected_hf_home = str(args.hf_home.resolve())
    checks["parent_hf_home"] = os.environ.get("HF_HOME") == expected_hf_home
    cache_env = os.environ.copy()
    cache_env["PYTHONPATH"] = str(robo)
    cache_probe = command(str(args.python4), "-c", "import json,os; from huggingface_hub import constants; print(json.dumps({'hf_home':os.getenv('HF_HOME'),'hub_cache':constants.HF_HUB_CACHE,'pythonpath':os.getenv('PYTHONPATH')}))", env=cache_env) if args.python4.is_file() else {}
    details["child_cache_probe"] = cache_probe
    try:
        cache_values = json.loads(cache_probe["stdout"].splitlines()[-1])
    except (KeyError, IndexError, json.JSONDecodeError):
        cache_values = {}
    checks["child_hf_cache_inherited"] = (cache_probe.get("returncode") == 0 and
        cache_values.get("hf_home") == expected_hf_home and
        str(cache_values.get("hub_cache", "")).startswith(expected_hf_home) and
        cache_values.get("pythonpath") == str(robo))
    details["weight_shards"] = weight_checks(model8, model4, args.weight_manifest) if args.weight_manifest.is_file() else []
    checks["six_weight_shards_exact"] = len(details["weight_shards"]) == 6 and all(x["match"] for x in details["weight_shards"])
    details["robo_patch"].pop("stdout", None)
    for arm in ("L1", "L2"):
        details.get(arm, {}).pop("pixel_hashes", None)
    return {"status": "pass" if all(checks.values()) else "fail", "checks": checks,
            "details": details, "note": "read-only existing-server check; rental time must be checked separately"}


def main() -> None:
    parser = argparse.ArgumentParser()
    for name in ("base", "l1_zip", "l2_zip", "code_zip", "model8", "model4", "python4", "hf_home", "weight_manifest"):
        parser.add_argument("--" + name.replace("_", "-"), required=True, type=Path)
    for name in ("l1_sha", "l2_sha", "code_sha"):
        parser.add_argument("--" + name.replace("_", "-"), required=True)
    args = parser.parse_args()
    report = preflight(args)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if report["status"] != "pass":
        raise SystemExit(2)


if __name__ == "__main__":
    main()

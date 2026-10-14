"""Read-only identity, resource, and nine-video hash gate for the existing server."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .seal_fresh_batch import sha256

TOP_COMMIT = "4877a0ee5098cbec18485125466631b1dcc4a573"
ROBO_COMMIT = "352d160389daa964788de1ec933d1925f3a6de4f"
ROBO_PATCH_SHA = "b560da190b4dccaa405684beb2e33a5950fefd035983dc98ae9d02406b9d2fac"
MODEL8_REV = "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b"
MODEL4_REV = "beef63bc914c5c189329d49c6d712d96d632aa34"
CONFIG8_SHA = "5cd452860dc1e9c29dd71cc3cef7f39b338b7a40793f7a260655c2d3568f3661"
CONFIG4_SHA = "2287e93a95c1dcd5e471cf386cf5750e7643ee0b2c44a2544a1318b8b8f3c9be"
ZIP_SHA = {"access_gate": "3e57af3072091bafbc10b81eea17d8ebd597337458cae5edd6b8433ab5842e78",
           "support_surface": "3124b5117820707f3458696d4a553f0fee27d41aa969d45eca78bfd84b6cfc9d"}
VIDEOS = {f"{i:04}.mp4" for i in range(1, 10)}
ALLOWED = VIDEOS | {"instruction.txt", "manifest.jsonl", "media_hashes.json"}


def inspect_input_zip(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != 12 or set(names) != ALLOWED or archive.testzip() is not None:
            raise ValueError("ZIP must have exactly nine anonymous videos and three metadata files")
        instruction = archive.read("instruction.txt").decode("utf-8").strip()
        rows = [json.loads(line) for line in archive.read("manifest.jsonl").decode("utf-8").splitlines() if line.strip()]
        media = json.loads(archive.read("media_hashes.json"))
        clips = {entry["video"]: entry for entry in media["clips"]}
        if (len(rows) != 9 or {row["video"] for row in rows} != VIDEOS or len(clips) != 9 or
                set(clips) != VIDEOS or
                any(row["instruction"] != instruction or row["fps"] != 1 or
                    row["frame_indices_from_30fps"] != list(range(0, 450, 30)) for row in rows)):
            raise ValueError("nine-video input manifest or fixed instruction differs")
        for row in rows:
            video = row["video"]
            digest = hashlib.sha256(archive.read(video)).hexdigest()
            if digest != row["sha256"] or digest != clips[video]["video_sha256"] or len(clips[video]["decoded_rgb_sha256"]) != 15:
                raise ValueError("video or pixel manifest mismatch: " + video)
        return {"video_count": 9, "pixel_hash_count": 135,
                "instruction_sha256": hashlib.sha256(instruction.encode()).hexdigest(),
                "video_sha256": {row["video"]: row["sha256"] for row in rows}}


def command(*args: str) -> dict:
    try:
        result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=40)
        return {"returncode": result.returncode, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()[-1000:]}
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


def preflight(args: argparse.Namespace) -> dict:
    base = args.base.resolve()
    top, robo = base / "research/sources/TOPReward", base / "research/sources/robometer_pr33_compat"
    checks, details = {}, {}
    details["utc"] = datetime.now(timezone.utc).isoformat()
    details["shanghai"] = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
    checks["existing_base"] = base.is_dir()
    checks["python8"] = args.python8.is_file()
    checks["python4"] = args.python4.is_file()
    checks["checkpoint_revisions"] = MODEL8_REV in str(args.model8) and MODEL4_REV in str(args.model4)
    details["checkpoint_config_sha256"] = {}
    for name, model, expected in (("8b", args.model8, CONFIG8_SHA), ("4b", args.model4, CONFIG4_SHA)):
        file = model / "config.json"
        actual = sha256(file) if file.is_file() else None
        details["checkpoint_config_sha256"][name] = actual
        checks[f"{name}_config_exact"] = actual == expected
    for arm, path in (("access_gate", args.access_zip), ("support_surface", args.support_zip)):
        checks[f"{arm}_zip_sha"] = path.is_file() and sha256(path) == ZIP_SHA[arm]
        try:
            details[arm] = inspect_input_zip(path) if checks[f"{arm}_zip_sha"] else {}
            checks[f"{arm}_contents"] = bool(details[arm])
        except Exception as exc:
            details[arm] = {"error": str(exc)}
            checks[f"{arm}_contents"] = False
    checks["code_zip_sha"] = args.code_zip.is_file() and sha256(args.code_zip) == args.code_sha
    if checks["code_zip_sha"]:
        with zipfile.ZipFile(args.code_zip) as archive:
            names = archive.namelist()
            checks["model_side_only"] = archive.testzip() is None and all(
                name.startswith("pilot_pkg/") and not any(word in name.lower() for word in
                ("truth", "condition_map", "score", "result", "prototype")) for name in names)
    else:
        checks["model_side_only"] = False
    details["top_commit"] = command("git", "-C", str(top), "rev-parse", "HEAD")
    details["robo_commit"] = command("git", "-C", str(robo), "rev-parse", "HEAD")
    patch = command("git", "-C", str(robo), "diff", "--", "robometer/utils/save.py")
    details["robo_patch_sha256"] = hashlib.sha256(patch.get("stdout", "").encode()).hexdigest()
    checks["top_commit"] = details["top_commit"].get("stdout") == TOP_COMMIT
    checks["robo_commit"] = details["robo_commit"].get("stdout") == ROBO_COMMIT
    checks["robo_patch_exact"] = details["robo_patch_sha256"] == ROBO_PATCH_SHA
    checks["native_paths"] = (top / "topreward/clients/qwen.py").is_file() and (robo / "scripts/example_inference_local.py").is_file()
    manifest = json.loads(args.weight_manifest.read_text(encoding="utf-8"))
    details["weight_files"] = []
    for repo_name, model, revision in (("Qwen/Qwen3-VL-8B-Instruct", args.model8, MODEL8_REV),
                                       ("robometer/Robometer-4B", args.model4, MODEL4_REV)):
        entry = next((x for x in manifest if x["repo"] == repo_name), None)
        if not entry:
            continue
        for item in entry["files"]:
            path = model / item["name"]
            actual = sha256(path) if path.is_file() else None
            details["weight_files"].append({"repo": repo_name, "file": item["name"], "actual_sha256": actual,
                                            "match": entry["revision"] == revision and actual == item["sha256"] and
                                            path.stat().st_size == item["size"] if path.is_file() else False})
    checks["six_weight_shards_exact"] = len(details["weight_files"]) == 6 and all(x["match"] for x in details["weight_files"])
    details["gpu"] = command("nvidia-smi", "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader,nounits")
    try:
        first_gpu = details["gpu"]["stdout"].splitlines()[0].split(",")
        free_mib = int(first_gpu[-1].strip())
    except (KeyError, IndexError, ValueError):
        free_mib = 0
    details["gpu_free_mib"] = free_mib
    checks["gpu_approximately_24gib_free"] = free_mib >= 21000
    details["disk_free_bytes"] = shutil.disk_usage(base).free if base.is_dir() else None
    checks["disk_at_least_5gib"] = details["disk_free_bytes"] is not None and details["disk_free_bytes"] >= 5 * 1024**3
    details["python8_deps"] = command(str(args.python8), "-c", "import cv2,torch,transformers,PIL;print(torch.__version__,torch.cuda.is_available())") if args.python8.is_file() else {}
    details["python4_deps"] = command(str(args.python4), "-c", "import cv2,torch,numpy,transformers;print(torch.__version__,torch.cuda.is_available())") if args.python4.is_file() else {}
    checks["python8_deps_cuda"] = details["python8_deps"].get("returncode") == 0 and "True" in details["python8_deps"].get("stdout", "")
    checks["python4_deps_cuda"] = details["python4_deps"].get("returncode") == 0 and "True" in details["python4_deps"].get("stdout", "")
    checks["offline_env"] = all(os.environ.get(key) == value for key, value in
                                 (("HF_HUB_OFFLINE", "1"), ("TRANSFORMERS_OFFLINE", "1"), ("WANDB_MODE", "disabled")))
    return {"status": "pass" if all(checks.values()) else "fail", "checks": checks, "details": details,
            "note": "read-only gate; actual rental end time is checked separately"}


def main() -> None:
    parser = argparse.ArgumentParser()
    for name in ("base", "access_zip", "support_zip", "code_zip", "model8", "model4", "python8", "python4", "weight_manifest"):
        parser.add_argument("--" + name.replace("_", "-"), required=True, type=Path)
    parser.add_argument("--code-sha", required=True)
    args = parser.parse_args()
    report = preflight(args)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "pass":
        raise SystemExit(2)


if __name__ == "__main__":
    main()

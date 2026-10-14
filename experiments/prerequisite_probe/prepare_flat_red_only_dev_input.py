"""Promote a reviewed flat red-only candidate to isolated development input.

This command does not call a model. It refuses to overwrite existing input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path


FRAME_INDICES = list(range(0, 450, 30))
EXPECTED_CONDITIONS = {"B+", "B0", "U0", "H-", "G+", "N0"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def prepare(candidate: Path, review_receipt: Path) -> dict:
    candidate = candidate.resolve()
    review_receipt = review_receipt.resolve()
    source = candidate / "candidate_input"
    truth = candidate / "truth"
    destination = candidate / "model_input"
    zip_path = candidate / "flat_red_only_development_model_input.zip"
    ready_path = candidate / "FLAT_DEV_READY.json"
    alias_path = truth / "server_alias_map.json"
    for path in (destination, zip_path, ready_path, alias_path):
        if path.exists():
            raise FileExistsError(path)
    if not review_receipt.is_file():
        raise FileNotFoundError(review_receipt)
    audit = json.loads((truth / "input_audit.json").read_text(encoding="utf-8"))
    if audit["status"] != "pass" or audit["issues"]:
        raise ValueError("source input audit did not pass")
    media = json.loads((source / "media_hashes.json").read_text(encoding="utf-8"))
    mapping = json.loads((truth / "mapping_and_trajectories.json").read_text(encoding="utf-8"))
    instruction = (source / "instruction.txt").read_text(encoding="utf-8").strip()
    clips = sorted(media["clips"], key=lambda row: row["video"])
    by_video = {record["video"]: record for record in mapping["records"]}
    if len(clips) != 6 or len(by_video) != 6 or {r["condition"] for r in by_video.values()} != EXPECTED_CONDITIONS:
        raise ValueError("expected exactly six distinct conditions")
    if {clip["video"] for clip in clips} != set(by_video):
        raise ValueError("media and truth video sets differ")
    if set(source.iterdir()) != {source / "instruction.txt", source / "media_hashes.json", *(source / clip["video"] for clip in clips)}:
        raise ValueError("unexpected source input file")
    if media["instruction"] != instruction:
        raise ValueError("instruction mismatch")

    destination.mkdir()
    aliases = []
    manifest = []
    adapted_clips = []
    for number, clip in enumerate(clips, 1):
        old_name = clip["video"]
        new_name = f"{number:04d}.mp4"
        old_path = source / old_name
        new_path = destination / new_name
        if sha256(old_path) != clip["video_sha256"]:
            raise ValueError(f"source video hash mismatch: {old_name}")
        if clip["sample_indices_30fps"] != FRAME_INDICES or len(clip["decoded_rgb_sha256"]) != 15:
            raise ValueError(f"source frame protocol mismatch: {old_name}")
        shutil.copyfile(old_path, new_path)
        if sha256(new_path) != clip["video_sha256"]:
            raise ValueError(f"copied video hash mismatch: {new_name}")
        adapted_clips.append({**clip, "video": new_name})
        manifest.append({
            "video": new_name,
            "instruction": instruction,
            "sha256": clip["video_sha256"],
            "fps": 1,
            "frame_indices_from_30fps": FRAME_INDICES,
        })
        aliases.append({
            "server_video": new_name,
            "source_video": old_name,
            "condition": by_video[old_name]["condition"],
        })
    shutil.copyfile(source / "instruction.txt", destination / "instruction.txt")
    write_json(destination / "media_hashes.json", {**media, "clips": adapted_clips})
    (destination / "manifest.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in manifest), encoding="utf-8"
    )
    write_json(alias_path, {"aliases": aliases})
    input_files = sorted(destination.iterdir(), key=lambda path: path.name)
    if len(input_files) != 9 or any(not path.is_file() for path in input_files):
        raise ValueError("development input must contain exactly nine files")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in input_files:
            info = zipfile.ZipInfo(path.name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    with zipfile.ZipFile(zip_path) as archive:
        if sorted(archive.namelist()) != [path.name for path in input_files]:
            raise ValueError("ZIP member set mismatch")
        for path in input_files:
            if archive.read(path.name) != path.read_bytes():
                raise ValueError(f"ZIP member mismatch: {path.name}")
    ready = {
        "status": "pending_supplemental_goal_review_and_final_verification",
        "scene_protocol": "flat_square_dev_v2",
        "video_protocol": "15s_1fps_640x480_15_decoded_frames",
        "scope": "development_only",
        "model_input": destination.as_posix(),
        "input_only_zip": zip_path.as_posix(),
        "input_only_zip_sha256": sha256(zip_path),
        "model_input_file_count": len(input_files),
        "anonymous_video_count": len(clips),
        "runner_manifest": "model_input/manifest.jsonl",
        "media_manifest": "model_input/media_hashes.json",
        "independent_six_clip_review": review_receipt.as_posix(),
        "independent_six_clip_review_raw_sha256": sha256(review_receipt.parent / "flat_red_only_six_reader_raw.md"),
        "input_audit_status": "pass",
        "existing_runner_input_and_decode_status": "pending",
        "existing_runner_dry_run_status": "pending",
        "known_limits": [
            "The six-clip reviewer described the distinguishing object motion in all six clips, but explicitly judged whole-goal completion only for B0.",
            "B0 has a longer round-trip motion than the one-way conditions.",
            "This is one development mechanism; the original two-mechanism SCENE_READY.json gate is not met.",
            "The method is not frozen and this package is not a fresh blind test.",
            "Independent human discrimination does not guarantee Monitor model discrimination.",
        ],
    }
    write_json(ready_path, ready)
    return ready


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("review_receipt", type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.candidate, args.review_receipt), indent=2, ensure_ascii=False))

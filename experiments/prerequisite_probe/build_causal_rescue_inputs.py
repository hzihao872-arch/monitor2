"""Build anonymous, deterministic L1/L2 model inputs from the sealed R0 clips."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

from .run_relation_endpoint_pilot import inspect_inputs


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "research/prerequisite_monitor/development/scene_video_next/flat_red_only_six_candidate_v1/model_input"
DESIGN = ROOT / "research/prerequisite_monitor/development/architecture_next/causal_rescue_20261006/design.json"
OUTPUT = ROOT / "research/prerequisite_monitor/development/architecture_next/causal_rescue_20261006/first_batch"
VIDEOS = tuple(f"{i:04}.mp4" for i in range(1, 7))
ALLOWED = set(VIDEOS) | {"instruction.txt", "manifest.jsonl", "media_hashes.json"}


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def require_exact_files(directory: Path) -> None:
    if directory.name != "model_input" or not directory.is_dir():
        raise ValueError("source must be a model_input directory")
    found = {path.name for path in directory.iterdir() if path.is_file()}
    if found != ALLOWED or any(path.is_dir() for path in directory.iterdir()):
        raise ValueError(f"model_input must contain only nine allowed files: {sorted(found)}")


def load_instruction(design_path: Path, arm: str) -> str:
    design = json.loads(design_path.read_text(encoding="utf-8"))
    if arm not in ("L1", "L2") or design["arms"][arm]["batch"] != "first":
        raise ValueError("only frozen first-batch L1/L2 arms are supported")
    return design["arms"][arm]["instruction"]


def write_zip(input_dir: Path, output: Path) -> None:
    with zipfile.ZipFile(output, "w") as archive:
        for name in sorted(ALLOWED):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, (input_dir / name).read_bytes())


def build_arm(source: Path, design_path: Path, output_dir: Path, arm: str) -> dict:
    source, design_path, output_dir = source.resolve(), design_path.resolve(), output_dir.resolve()
    if output_dir.exists():
        raise FileExistsError(output_dir)
    require_exact_files(source)
    if not design_path.is_file():
        raise FileNotFoundError(design_path)
    instruction = load_instruction(design_path, arm)
    rows = inspect_inputs(source)
    if len(rows) != 6 or {row["video"] for row in rows} != set(VIDEOS):
        raise ValueError("source must have six anonymous videos")
    source_instruction = (source / "instruction.txt").read_text(encoding="utf-8").strip()
    design = json.loads(design_path.read_text(encoding="utf-8"))
    if source_instruction != design["arms"]["R0"]["instruction"]:
        raise ValueError("source instruction does not match frozen R0")
    output_dir.mkdir(parents=True)
    input_dir = output_dir / "model_input"
    input_dir.mkdir()
    for name in VIDEOS:
        shutil.copyfile(source / name, input_dir / name)
    (input_dir / "instruction.txt").write_text(instruction + "\n", encoding="utf-8")
    manifest_rows = []
    for row in rows:
        manifest_rows.append({key: (instruction if key == "instruction" else row[key])
                              for key in ("video", "instruction", "sha256", "fps", "frame_indices_from_30fps")})
    (input_dir / "manifest.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in manifest_rows), encoding="utf-8")
    media = json.loads((source / "media_hashes.json").read_text(encoding="utf-8"))
    media["instruction"] = instruction
    (input_dir / "media_hashes.json").write_text(
        json.dumps(media, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    zip_path = output_dir / "model_input.zip"
    write_zip(input_dir, zip_path)
    report = verify_arm(source, design_path, output_dir, arm)
    (output_dir / "package_manifest.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def verify_arm(source: Path, design_path: Path, output_dir: Path, arm: str) -> dict:
    source, design_path, output_dir = source.resolve(), design_path.resolve(), output_dir.resolve()
    input_dir = output_dir / "model_input"
    require_exact_files(source)
    require_exact_files(input_dir)
    instruction = load_instruction(design_path, arm)
    if (input_dir / "instruction.txt").read_text(encoding="utf-8").strip() != instruction:
        raise ValueError("instruction.txt differs from frozen design")
    source_rows = inspect_inputs(source)
    target_rows = inspect_inputs(input_dir)
    if len(source_rows) != 6 or len(target_rows) != 6:
        raise ValueError("expected six rows")
    source_by_video = {row["video"]: row for row in source_rows}
    for row in target_rows:
        name = row["video"]
        if row["instruction"] != instruction or row["sha256"] != source_by_video[name]["sha256"]:
            raise ValueError(f"instruction or video hash differs: {name}")
        if row["decoded_pixel_sha256"] != source_by_video[name]["decoded_pixel_sha256"]:
            raise ValueError(f"decoded pixels differ: {name}")
        if (source / name).read_bytes() != (input_dir / name).read_bytes():
            raise ValueError(f"video bytes differ: {name}")
    media = json.loads((input_dir / "media_hashes.json").read_text(encoding="utf-8"))
    if media["instruction"] != instruction:
        raise ValueError("media instruction differs")
    zip_path = output_dir / "model_input.zip"
    with zipfile.ZipFile(zip_path) as archive:
        if set(archive.namelist()) != ALLOWED or archive.testzip() is not None:
            raise ValueError("ZIP file list or CRC differs")
        for name in ALLOWED:
            if archive.read(name) != (input_dir / name).read_bytes():
                raise ValueError(f"ZIP member differs: {name}")
    return {
        "status": "pass", "arm": arm, "design_sha256": sha256(design_path),
        "source_video_bytes_preserved": True, "source_pixels_preserved": True,
        "video_count": 6, "decoded_pixel_count": 90,
        "instruction": instruction, "zip_sha256": sha256(zip_path),
        "zip_size_bytes": zip_path.stat().st_size,
        "files": [{"name": name, "sha256": sha256(input_dir / name),
                   "size_bytes": (input_dir / name).stat().st_size} for name in sorted(ALLOWED)],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--design", type=Path, default=DESIGN)
    parser.add_argument("--output-root", type=Path, default=OUTPUT)
    parser.add_argument("--arms", nargs="+", choices=("L1", "L2"), default=("L1", "L2"))
    args = parser.parse_args()
    for arm in args.arms:
        print(json.dumps(build_arm(args.source, args.design, args.output_root / arm, arm)))


if __name__ == "__main__":
    main()

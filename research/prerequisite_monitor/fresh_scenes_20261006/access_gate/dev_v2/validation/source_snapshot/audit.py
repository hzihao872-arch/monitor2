"""No-model audit of fresh scene media, truth separation, and protocol timing."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

import cv2
from PIL import Image
import numpy as np

from experiments.prerequisite_probe.run_relation_endpoint_pilot import inspect_inputs
from experiments.prerequisite_probe.produce import sha256

from .generate import GOALS, MANIFEST_FIELDS, validate_model_manifest_row
from .routes import CASES
from .scenes import GATE_OPEN, PANEL_DEPLOYED


def model_input_name_issues(folder: Path):
    expected = {f"{number:04d}.mp4" for number in range(1, 10)} | {
        "manifest.jsonl", "media_hashes.json", "instruction.txt",
    }
    names = {item.name for item in folder.iterdir()}
    return sorted(f"unexpected model_input name: {name}" for name in names - expected) + sorted(
        f"missing model_input name: {name}" for name in expected - names)


def public_manifest_row(inspected_row):
    """Remove decoder proof attached by the local native input inspector."""
    return {key: inspected_row[key] for key in MANIFEST_FIELDS}


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _color_counts(frame):
    rgb = frame.astype(np.int16)
    red, green, blue = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    blue_count = int(np.count_nonzero((blue > 30) & (blue > red * 1.35) & (blue > green * 1.15)))
    orange_count = int(np.count_nonzero((red > 145) & (green > 45) & (green < red * .8) & (blue < green * .85)))
    yellow_count = int(np.count_nonzero((red > 145) & (green > 120) & (blue < 110) & (red > blue * 1.5)))
    return {"blue_pixels": blue_count, "orange_pixels": orange_count,
            "yellow_pixels": yellow_count}


def _decode(path):
    capture = cv2.VideoCapture(str(path))
    frames = []
    try:
        while True:
            okay, bgr = capture.read()
            if not okay:
                break
            frames.append(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    finally:
        capture.release()
    return frames


def audit_package(package: Path, mechanism: str):
    issues = []
    input_dir = package / "model_input"
    issues.extend(model_input_name_issues(input_dir))
    rows = []
    try:
        rows = inspect_inputs(input_dir)
    except Exception as error:
        issues.append(f"native input inspector: {type(error).__name__}: {error}")
    if len(rows) != 9:
        issues.append(f"expected nine model videos, found {len(rows)}")
    for row in rows:
        try:
            validate_model_manifest_row(public_manifest_row(row))
        except Exception as error:
            issues.append(f"manifest row {row.get('video')}: {error}")
        if row["instruction"] != GOALS[mechanism]:
            issues.append(f"instruction differs: {row['video']}")
    if (input_dir / "instruction.txt").read_text(encoding="utf-8").strip() != GOALS[mechanism]:
        issues.append("instruction.txt differs")
    media = _read_json(input_dir / "media_hashes.json")
    media_by_video = {clip["video"]: clip for clip in media.get("clips", [])}
    mapping = _read_json(package / "truth" / "condition_map.json")
    if set(mapping.values()) != set(CASES) or set(mapping) != {row["video"] for row in rows}:
        issues.append("condition map is incomplete or unaligned")
    generation_checks = _read_json(package / "validation" / "generation_checks.json")
    issues.extend(f"generation check failed: {key}" for key, okay in generation_checks.items() if not okay)
    visibility = {}
    sample_stability = {}
    for row in rows:
        alias = row["video"]
        name = Path(alias).stem
        summary = _read_json(package / "truth" / f"{name}.json")
        decoded = _decode(input_dir / alias)
        if len(decoded) != 15:
            issues.append(f"{alias}: expected 15 decoded frames, found {len(decoded)}")
            continue
        computed_hashes = [hashlib.sha256(frame.tobytes()).hexdigest() for frame in decoded]
        if computed_hashes != media_by_video[alias]["decoded_rgb_sha256"]:
            issues.append(f"{alias}: media decoded SHA mismatch")
        if computed_hashes != summary["decoded_rgb_sha256"]:
            issues.append(f"{alias}: truth decoded SHA mismatch")
        source_hashes = []
        for second in range(15):
            png = package / "truth" / "sampled_frames" / name / f"{second:02d}.png"
            source_hashes.append(hashlib.sha256(np.asarray(Image.open(png).convert("RGB")).tobytes()).hexdigest())
        if source_hashes != summary["sampled_source_rgb_sha256"]:
            issues.append(f"{alias}: source PNG RGB SHA mismatch")
        states = package / "truth" / "sim_states" / f"{name}.jsonl"
        with states.open(encoding="utf-8") as stream:
            state_count = sum(1 for _ in stream)
        if state_count != 450 or sha256(states) != summary["sim_states_sha256"]:
            issues.append(f"{alias}: raw state count or SHA mismatch")
        raw = package / "raw" / alias
        capture = cv2.VideoCapture(str(raw))
        raw_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        capture.release()
        if raw_count != 450 or sha256(raw) != summary["raw_video_sha256"]:
            issues.append(f"{alias}: raw video frame count or SHA mismatch")
        if sha256(package / "reviewer_only" / alias) != row["sha256"]:
            issues.append(f"{alias}: reviewer video differs")
        counts = [_color_counts(frame) for frame in decoded]
        visibility[alias] = counts
        if min(entry["blue_pixels"] for entry in counts) < 20:
            issues.append(f"{alias}: blue object absent or occluded in a sampled frame")
        color = "orange_pixels" if mechanism == "access_gate" else "yellow_pixels"
        if min(entry[color] for entry in counts) < 50:
            issues.append(f"{alias}: prerequisite object absent or occluded in a sampled frame")
        timeline = {item["frame"] // 30: item for item in summary["timeline"] if item["frame"] % 30 == 0}
        pre = [timeline[t]["prerequisite_xyz"] for t in (0, 1, 2)]
        post = [timeline[t]["prerequisite_xyz"] for t in (12, 13, 14)]
        sample_stability[alias] = {"pre_equal": pre[0] == pre[1] == pre[2],
                                   "post_equal": post[0] == post[1] == post[2]}
        if not all(sample_stability[alias].values()):
            issues.append(f"{alias}: prerequisite unstable in first/last three samples")
        if mapping[alias] == "R":
            opened = GATE_OPEN if mechanism == "access_gate" else PANEL_DEPLOYED
            for second in (7, 8):
                if np.linalg.norm(np.asarray(timeline[second]["prerequisite_xyz"]) - np.asarray(opened)) > .006:
                    issues.append(f"{alias}: R not fully open at sampled second {second}")
    zip_path = package / "model_input.zip"
    if sha256(zip_path) != _read_json(package / "validation" / "media_summary.json")["model_input_zip_sha256"]:
        issues.append("model_input ZIP SHA differs")
    with zipfile.ZipFile(zip_path) as archive:
        if set(archive.namelist()) != {item.name for item in input_dir.iterdir()}:
            issues.append("model_input ZIP contents differ")
        for name in archive.namelist():
            if hashlib.sha256(archive.read(name)).hexdigest() != sha256(input_dir / name):
                issues.append(f"ZIP content hash differs: {name}")
    allowed_reviewer = {f"{number:04d}.mp4" for number in range(1, 10)} | {
        "instruction.txt", "blank_answers.csv", "reader_instructions.md",
    }
    if {item.name for item in (package / "reviewer_only").iterdir()} != allowed_reviewer:
        issues.append("reviewer_only file set differs")
    if len((package / "reviewer_only" / "blank_answers.csv").read_text(encoding="utf-8").splitlines()) != 10:
        issues.append("reviewer blank sheet does not have nine rows")
    result = {"mechanism": mechanism, "version": package.name,
              "status": "pass" if not issues else "fail", "issues": issues,
              "video_count": len(rows), "visibility_pixel_counts": visibility,
              "sample_stability": sample_stability,
              "reviewer_first_answers_present": False,
              "native_model_called": False}
    (package / "validation" / "audit.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def audit_root(root: Path):
    results = []
    for mechanism in ("access_gate", "support_surface"):
        package = root / mechanism / "dev_v2"
        results.append(audit_package(package, mechanism))
    result = {"status": "pass" if all(item["status"] == "pass" for item in results) else "fail",
              "issues": [f"{item['mechanism']}: {issue}" for item in results for issue in item["issues"]],
              "packages": [{"mechanism": item["mechanism"], "version": item["version"],
                            "status": item["status"], "video_count": item["video_count"]}
                           for item in results]}
    (root / "audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    result = audit_root(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

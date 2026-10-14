"""Generate one complete, anonymous nine-condition local development package."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
import shutil
import zipfile

import cv2
from PIL import Image, ImageDraw
import numpy as np

from experiments.prerequisite_probe.probe import _jsonable, sample_indices, snapshot_signature
from experiments.prerequisite_probe.produce import ffmpeg_writer, sha256

from .geometry import challenge_access, challenge_support
from .routes import BLOCKED_CASES, CASES, run_continuation, simulate_condition
from .scenes import ACCESS, SUPPORT, make_env


GOALS = {
    "access_gate": "Put the blue cube completely inside the transparent box so it rests on the box floor. Release it and leave it still.",
    "support_surface": "Place the blue cube on the marked elevated landing, release it, and leave it stable.",
}
MANIFEST_FIELDS = {"video", "instruction", "sha256", "fps", "frame_indices_from_30fps"}


def require_empty_output(output: Path):
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"nonempty output; create a new version: {output}")


def validate_model_manifest_row(row):
    if set(row) != MANIFEST_FIELDS:
        raise ValueError(f"model manifest fields must be exactly {sorted(MANIFEST_FIELDS)}")
    if not isinstance(row["video"], str) or len(row["video"]) != 8 or not row["video"][:4].isdigit() or not row["video"].endswith(".mp4"):
        raise ValueError("video must have anonymous four-digit filename")
    if not isinstance(row["instruction"], str) or any(
        phrase in row["instruction"].lower() for phrase in
        ("open the door", "slide the lid", "deploy the panel", "unfold the support")
    ):
        raise ValueError("final-goal instruction cannot name a preparation action")
    if row["fps"] != 1 or row["frame_indices_from_30fps"] != sample_indices():
        raise ValueError("model sampling protocol differs")
    if not isinstance(row["sha256"], str) or len(row["sha256"]) != 64:
        raise ValueError("missing SHA-256")
    return row


def _write_json(path, payload):
    path.write_text(json.dumps(_jsonable(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _decode_model_video(path):
    capture = cv2.VideoCapture(str(path))
    frames = []
    try:
        while True:
            okay, frame = capture.read()
            if not okay:
                break
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    finally:
        capture.release()
    if len(frames) != 15 or any(frame.shape != (480, 640, 3) for frame in frames):
        raise RuntimeError(f"bad model decode: {path}, count={len(frames)}")
    return frames


def _close_encoder(process, label):
    process.stdin.close()
    stderr = process.stderr.read().decode(errors="replace")
    code = process.wait()
    if code:
        raise RuntimeError(f"{label}: ffmpeg exited {code}: {stderr[-2000:]}")


def _record_one(env, mechanism, condition, alias, snapshot, output):
    raw_path = output / "raw" / f"{alias}.mp4"
    model_path = output / "model_input" / f"{alias}.mp4"
    states_path = output / "truth" / "sim_states" / f"{alias}.jsonl"
    frames_dir = output / "truth" / "sampled_frames" / alias
    frames_dir.mkdir(parents=True)
    raw_encoder = ffmpeg_writer(raw_path, 30)
    model_encoder = ffmpeg_writer(model_path, 1)
    source_hashes = []
    try:
        with states_path.open("w", encoding="utf-8") as states:
            def on_frame(frame_index, active_env):
                state = {
                    "frame": frame_index,
                    "state": _jsonable(active_env.unwrapped.get_state_dict()),
                    "terminal_observation": active_env.unwrapped.terminal_sample(),
                }
                states.write(json.dumps(state, separators=(",", ":")) + "\n")
                rgb = np.ascontiguousarray(active_env.render().cpu().numpy()[0])
                raw_encoder.stdin.write(rgb.tobytes())
                if frame_index in sample_indices():
                    model_encoder.stdin.write(rgb.tobytes())
                    source_hashes.append(hashlib.sha256(rgb.tobytes()).hexdigest())
                    Image.fromarray(rgb).save(frames_dir / f"{frame_index // 30:02d}.png")

            result = simulate_condition(
                env, mechanism, condition, snapshot=snapshot, on_frame=on_frame,
            )
    finally:
        _close_encoder(raw_encoder, "raw")
        _close_encoder(model_encoder, "model")
    decoded = _decode_model_video(model_path)
    result["raw_video_sha256"] = sha256(raw_path)
    result["model_video_sha256"] = sha256(model_path)
    result["sim_states_sha256"] = sha256(states_path)
    result["sampled_source_rgb_sha256"] = source_hashes
    result["decoded_rgb_sha256"] = [hashlib.sha256(frame.tobytes()).hexdigest() for frame in decoded]
    result["pre_state_sha256"] = snapshot_signature(snapshot)
    result["sample_frame_indices_30fps"] = sample_indices()
    result["alias"] = f"{alias}.mp4"
    _write_json(output / "truth" / f"{alias}.json", result)
    return result, decoded


def _contact_sheet(output, decoded_by_alias):
    selected = (0, 3, 6, 9, 14)
    aliases = sorted(decoded_by_alias)
    width, height = 320, 240
    sheet = Image.new("RGB", (len(selected) * width, len(aliases) * (height + 20)), "white")
    draw = ImageDraw.Draw(sheet)
    for row, alias in enumerate(aliases):
        for column, second in enumerate(selected):
            frame = Image.fromarray(decoded_by_alias[alias][second]).resize((width, height))
            left, top = column * width, row * (height + 20)
            sheet.paste(frame, (left, top + 20))
            draw.text((left + 5, top + 3), f"{alias}  t={second}s", fill="black")
    path = output / "validation" / "decoded_contact_sheet.png"
    sheet.save(path)
    return path


def _continuation_challenge(mechanism, output):
    records = []
    for route in ("center", "offset"):
        for seed in (20261006, 20261007, 20261008):
            for start in ("blocked", "open"):
                records.append(run_continuation(mechanism, start, route=route, seed=seed))
    _write_json(output / "physics" / "paired_continuations.json", records)
    blocked_success = [r for r in records if r["start_state"] == "blocked" and r["success"]]
    open_failure = [r for r in records if r["start_state"] == "open" and not r["success"]]
    return records, blocked_success, open_failure


def generate(mechanism: str, output: Path):
    if mechanism not in GOALS:
        raise ValueError(mechanism)
    require_empty_output(output)
    for folder in ("physics", "model_input", "raw", "truth/sim_states",
                   "truth/sampled_frames", "reviewer_only", "reviews", "validation"):
        (output / folder).mkdir(parents=True, exist_ok=True)
    workspace = Path(__file__).resolve().parents[3]
    card = workspace / "research/prerequisite_monitor/fresh_scenes_20261006/scene_cards" / f"{mechanism}.md"
    shutil.copy2(card, output / "scene_card.md")
    try:
        return _generate_content(mechanism, output)
    except Exception as error:
        (output / "validation" / "generation_failure.txt").write_text(
            f"{type(error).__name__}: {error}\n", encoding="utf-8")
        raise


def _generate_content(mechanism, output):
    spec = ACCESS if mechanism == "access_gate" else SUPPORT
    necessity = challenge_access(spec) if mechanism == "access_gate" else challenge_support(spec)
    _write_json(output / "physics" / "necessity_report.json", necessity)
    continuations, blocked_success, open_failure = _continuation_challenge(mechanism, output)
    _write_json(output / "physics" / "challenge_summary.json", {
        "blocked_successes": len(blocked_success), "open_failures": len(open_failure),
        "paired_routes": 2, "paired_seeds": 3,
        "same_seed_and_offset_for_blocked_and_open": True,
    })
    (output / "physics" / "counterexample_log.md").write_text(
        "# 主动反例记录\n\n"
        + f"机制：`{mechanism}`；解析与有限搜索详见 `necessity_report.json`。\n\n"
        + f"阻挡态续行成功（潜在反例）：{len(blocked_success)}；开放态续行失败：{len(open_failure)}。"
        + "逐种子、目标末态及实际抓握记录在 `paired_continuations.json`。"
        + "有限搜索没有发现反例不能充当穷尽证明；同步运动学滑件不能证明自由动力学抓取能力。\n",
        encoding="utf-8",
    )
    rng = random.Random(20261006 + (1 if mechanism == "access_gate" else 2))
    shuffled = list(CASES)
    rng.shuffle(shuffled)
    case_to_alias = {condition: f"{number:04d}" for number, condition in enumerate(shuffled, 1)}
    summaries, decoded_by_alias = {}, {}
    snapshots = {}
    for start in ("blocked", "open"):
        env = make_env(mechanism, start)
        try:
            env.reset(seed=20261006)
            snapshot = copy.deepcopy(env.unwrapped.get_state_dict())
            snapshots[start] = snapshot
            _write_json(output / "truth" / f"initial_{start}.json", snapshot)
            for condition in CASES:
                if (condition in BLOCKED_CASES) != (start == "blocked"):
                    continue
                alias = case_to_alias[condition]
                result, decoded = _record_one(env, mechanism, condition, alias, snapshot, output)
                summaries[condition] = result
                decoded_by_alias[alias] = decoded
                print(f"RECORDED {mechanism} {condition} {alias}.mp4 {result['model_video_sha256'][:12]}", flush=True)
        finally:
            env.close()
    checks = {
        "nine_conditions": set(summaries) == set(CASES),
        "all_blocked_same_snapshot": len({summaries[c]["pre_state_sha256"] for c in BLOCKED_CASES}) == 1,
        "all_open_same_snapshot": len({summaries[c]["pre_state_sha256"] for c in CASES if c not in BLOCKED_CASES}) == 1,
        "goal_only_G": all(summaries[c]["goal_success"] == (c == "G") for c in CASES),
        "E_open": summaries["E"]["end_prerequisite_state"] == "open",
        "S_blocked": summaries["S"]["end_prerequisite_state"] == "blocked",
        "R_reopened_then_blocked": summaries["R"]["visited_open_state"] and summaries["R"]["end_prerequisite_state"] == "blocked",
        "H_blocked": summaries["H"]["end_prerequisite_state"] == "blocked",
        "G_actual_grasp": summaries["G"]["ever_grasped_cube"],
        "blocked_challenge_no_success": not blocked_success,
        "open_challenge_no_failure": not open_failure,
    }
    _write_json(output / "validation" / "generation_checks.json", checks)
    _write_json(output / "truth" / "condition_map.json", {
        f"{alias}.mp4": condition for condition, alias in case_to_alias.items()})
    _write_json(output / "truth" / "case_summaries.json", summaries)
    _contact_sheet(output, decoded_by_alias)
    manifest_rows = []
    media_rows = []
    for alias in sorted(decoded_by_alias):
        condition = next(case for case, code in case_to_alias.items() if code == alias)
        result = summaries[condition]
        row = validate_model_manifest_row({
            "video": f"{alias}.mp4", "instruction": GOALS[mechanism],
            "sha256": result["model_video_sha256"], "fps": 1,
            "frame_indices_from_30fps": sample_indices(),
        })
        manifest_rows.append(row)
        media_rows.append({
            "video": f"{alias}.mp4", "video_sha256": result["model_video_sha256"],
            "decoded_rgb_sha256": result["decoded_rgb_sha256"],
        })
        shutil.copy2(output / "model_input" / f"{alias}.mp4",
                     output / "reviewer_only" / f"{alias}.mp4")
    (output / "model_input" / "manifest.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in manifest_rows), encoding="utf-8")
    _write_json(output / "model_input" / "media_hashes.json", {"clips": media_rows})
    (output / "model_input" / "instruction.txt").write_text(GOALS[mechanism] + "\n", encoding="utf-8")
    (output / "reviewer_only" / "instruction.txt").write_text(GOALS[mechanism] + "\n", encoding="utf-8")
    (output / "reviewer_only" / "blank_answers.csv").write_text(
        "video,goal_complete_before,goal_complete_after,prerequisite_before,prerequisite_after,temporary_reversal,can_complete_holding_after_state,possible_alternative_route,evidence_seconds_or_unknown,uncertainty\n"
        + "".join(f"{alias}.mp4,,,,,,,,,\n" for alias in sorted(decoded_by_alias)), encoding="utf-8")
    (output / "reviewer_only" / "reader_instructions.md").write_text(
        "只看本目录的最终目标句和九个匿名视频；不要查看代码、尺寸、`truth/`、条件映射或任何模型分数。"
        "对每段分别填写空白表：目标初末是否完成、非目标结构初末状态、是否暂时撤销、"
        "保持末态且不主动处理该结构时能否合法完成、可能的替代路线、证据秒数或 unknown。"
        "允许提出反例；请在看到任何答案或解释前交回首次原答和接触声明。\n",
        encoding="utf-8",
    )
    (output / "reviews" / "README.md").write_text(
        "独立人类盲审待用户安排。此目录尚无读者首次原答、接触声明或揭盲比对；"
        "作者不能代替独立读者。\n", encoding="utf-8")
    with zipfile.ZipFile(output / "model_input.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((output / "model_input").iterdir()):
            archive.write(path, path.name)
    _write_json(output / "validation" / "media_summary.json", {
        "video_count": len(media_rows), "frames_per_video": 15,
        "model_input_zip_sha256": sha256(output / "model_input.zip"),
        "source_sample_indices": sample_indices(),
    })
    if not all(checks.values()):
        raise RuntimeError(f"generation checks failed: {[key for key, okay in checks.items() if not okay]}")
    return {"mechanism": mechanism, "status": "generated", "checks": checks,
            "zip_sha256": sha256(output / "model_input.zip")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mechanism", choices=tuple(GOALS), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(generate(args.mechanism, args.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

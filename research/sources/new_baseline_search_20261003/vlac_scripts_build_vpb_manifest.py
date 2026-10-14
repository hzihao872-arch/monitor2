#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from utils.vpb_io import absolute_frame_path_from_any
from utils.vpb_metrics import (
    TEST_BUCKETS,
    iter_benchmark_rows,
    main_view_for_row,
    selected_frames_for_row,
)

PROMPT_VARIANT = "chunk_all"
PROMPT_SOURCE = "task_description"


def build_vlac_cut_prompt(task_description: str) -> str:
    task_and_plan = str(task_description or "").strip()
    return (
        f"任务描述和具体规划: {task_and_plan}\n\n"
        "请根据任务描述和具体规划，找到并逐点生成视频中的关键动作点和相应的进度标注。"
        "输出格式要求：每个关键点一行，格式为：\n"
        "时间: X.Xs, 进度: Y%\n\n"
        "请严格按照上述格式输出，不要输出额外说明。"
    )


def parse_args() -> argparse.Namespace:
    repo_root = SCRIPT_DIR.parent
    parser = argparse.ArgumentParser(
        description="Build a VLAC-Cut evaluation manifest for the public Video-Progress Benchmark."
    )
    parser.add_argument(
        "--benchmark-root",
        type=Path,
        default=repo_root / "splits",
        help="Directory containing HF Dataset splits/*.json.",
    )
    parser.add_argument(
        "--frames-root",
        type=Path,
        default=repo_root / "_extracted_frames",
        help="Root directory produced by scripts/utils/extract_vpb_frames.py.",
    )
    parser.add_argument("--out", type=Path, required=True, help="Output JSONL manifest path.")
    parser.add_argument(
        "--record-format",
        choices=["trajectory", "point"],
        default="trajectory",
        help="Manifest row format. Use trajectory for video models and point for frame-level models.",
    )
    parser.add_argument(
        "--buckets",
        nargs="+",
        default=list(TEST_BUCKETS),
        choices=list(TEST_BUCKETS),
        help="Benchmark buckets to include.",
    )
    parser.add_argument(
        "--eval-points",
        choices=["time_hz", "dense", "semantic_anchors"],
        default="time_hz",
        help="Evaluation frame points. Default time_hz with --sample-hz 1.0 matches the public 1Hz evaluation protocol.",
    )
    parser.add_argument(
        "--sample-hz",
        type=float,
        default=1.0,
        help="Evaluation sampling rate used when --eval-points=time_hz.",
    )
    parser.add_argument(
        "--input-sample-hz",
        type=float,
        default=2.0,
        help="Trajectory-level video input sampling rate. The default is the 2Hz input setting used in our VLAC-Cut evaluation.",
    )
    parser.add_argument(
        "--view",
        default=None,
        help="Override the view for all rows. By default, the view is inferred from metadata.main_path.",
    )
    parser.add_argument(
        "--limit-trajectories",
        type=int,
        default=None,
        help="Optional smoke-test limit per full manifest, applied after bucket filtering.",
    )
    parser.add_argument(
        "--check-files",
        action="store_true",
        help="Check whether resolved frame files exist and report missing paths.",
    )
    return parser.parse_args()


def build_record(
    *,
    bucket: str,
    row_idx: int,
    row: dict[str, Any],
    frame: int,
    timestamp_sec: float | None,
    image_path: Path,
    view: str,
    is_terminal_point: bool,
    selected_count: int,
    eval_points: str,
    sample_hz: float,
) -> dict[str, Any]:
    meta = dict(row.get("metadata") or {})
    task_description = str(meta.get("task_description") or "")
    record: dict[str, Any] = {
        "bucket": bucket,
        "row_index": row_idx,
        "global_episode_id": str(row.get("global_episode_id") or ""),
        "frame": int(frame),
        "timestamp_sec": timestamp_sec,
        "image_path": str(image_path),
        "view": view,
        "task_instruction": str(meta.get("task_instruction") or ""),
        "task_description": task_description,
        "vlac_cut_prompt": build_vlac_cut_prompt(task_description),
        "prompt_variant": PROMPT_VARIANT,
        "prompt_source": PROMPT_SOURCE,
        "is_terminal_point": bool(is_terminal_point),
        "selected_frame_count": int(selected_count),
        "eval_points": eval_points,
    }
    if eval_points == "time_hz":
        record["sample_hz"] = float(sample_hz)
    if eval_points != "time_hz" or not math.isclose(float(sample_hz), 1.0):
        record["non_strict_eval_input"] = True
    return record


def build_trajectory_record(
    *,
    bucket: str,
    row_idx: int,
    row: dict[str, Any],
    input_frames: list[int],
    input_timestamps_sec: list[float | None],
    input_image_paths: list[Path],
    eval_frames: list[int],
    eval_timestamps_sec: list[float | None],
    view: str,
    eval_points: str,
    eval_sample_hz: float,
    input_sample_hz: float,
) -> dict[str, Any]:
    meta = dict(row.get("metadata") or {})
    task_description = str(meta.get("task_description") or "")
    record: dict[str, Any] = {
        "bucket": bucket,
        "row_index": row_idx,
        "global_episode_id": str(row.get("global_episode_id") or ""),
        "frames": [int(frame) for frame in input_frames],
        "timestamps_sec": input_timestamps_sec,
        "image_paths": [str(path) for path in input_image_paths],
        "input_frames": [int(frame) for frame in input_frames],
        "input_timestamps_sec": input_timestamps_sec,
        "input_image_paths": [str(path) for path in input_image_paths],
        "eval_frames": [int(frame) for frame in eval_frames],
        "eval_timestamps_sec": eval_timestamps_sec,
        "view": view,
        "task_instruction": str(meta.get("task_instruction") or ""),
        "task_description": task_description,
        "vlac_cut_prompt": build_vlac_cut_prompt(task_description),
        "prompt_variant": PROMPT_VARIANT,
        "prompt_source": PROMPT_SOURCE,
        "terminal_frame": int(eval_frames[-1]) if eval_frames else None,
        "selected_frame_count": len(input_frames),
        "input_frame_count": len(input_frames),
        "eval_frame_count": len(eval_frames),
        "eval_points": eval_points,
        "input_sample_hz": float(input_sample_hz),
    }
    if eval_points == "time_hz":
        record["sample_hz"] = float(eval_sample_hz)
        record["eval_sample_hz"] = float(eval_sample_hz)
    if eval_points != "time_hz" or not math.isclose(float(eval_sample_hz), 1.0):
        record["non_strict_eval_input"] = True
    return record


def main() -> None:
    args = parse_args()
    if args.sample_hz <= 0:
        raise SystemExit("--sample-hz must be positive")
    if args.input_sample_hz <= 0:
        raise SystemExit("--input-sample-hz must be positive")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    stats: Counter[str] = Counter()
    emitted_trajectories = 0

    with args.out.open("w", encoding="utf-8") as f:
        for bucket, row_idx, row in iter_benchmark_rows(args.benchmark_root, args.buckets):
            if args.limit_trajectories is not None and emitted_trajectories >= args.limit_trajectories:
                break

            eval_selected = selected_frames_for_row(
                row,
                eval_points=args.eval_points,
                sample_hz=float(args.sample_hz),
            )
            if not eval_selected.frames:
                stats["skipped_empty_selection"] += 1
                continue
            input_selected = selected_frames_for_row(
                row,
                eval_points="time_hz",
                sample_hz=float(args.input_sample_hz),
            )
            if args.record_format == "trajectory" and not input_selected.frames:
                stats["skipped_empty_input_selection"] += 1
                continue
            if eval_selected.frames[0] != 0:
                raise ValueError(
                    f"{bucket} row {row_idx}: official evaluation requires eval_frames to start at 0"
                )
            if input_selected.frames and input_selected.frames[0] != 0:
                raise ValueError(
                    f"{bucket} row {row_idx}: official evaluation requires input_frames to start at 0"
                )

            selected_view = str(args.view or main_view_for_row(row) or "").strip()
            if not selected_view:
                stats["skipped_missing_view"] += 1
                continue

            frame_index = dict(row.get("frame_index") or {})
            full_eval_frames = eval_selected.frames
            terminal_frame = full_eval_frames[-1]
            source_selection = input_selected if args.record_format == "trajectory" else eval_selected
            resolved_frames: list[int] = []
            resolved_timestamps: list[float | None] = []
            resolved_paths: list[Path] = []
            missing_view = False
            for frame, timestamp_sec in zip(source_selection.frames, source_selection.timestamps_sec):
                image_map = frame_index.get(str(frame))
                if not isinstance(image_map, dict) or selected_view not in image_map:
                    stats["missing_view_points"] += 1
                    missing_view = True
                    continue
                image_path = absolute_frame_path_from_any(str(image_map[selected_view]), args.frames_root)
                if args.check_files and not image_path.exists():
                    stats["missing_frame_files"] += 1
                resolved_frames.append(frame)
                resolved_timestamps.append(timestamp_sec)
                resolved_paths.append(image_path)

            if not resolved_frames:
                stats["skipped_no_resolved_frames"] += 1
                continue
            if args.record_format == "trajectory" and missing_view:
                stats["skipped_incomplete_trajectory"] += 1
                continue

            emitted_for_traj = 0
            if args.record_format == "trajectory":
                record = build_trajectory_record(
                    bucket=bucket,
                    row_idx=row_idx,
                    row=row,
                    input_frames=resolved_frames,
                    input_timestamps_sec=resolved_timestamps,
                    input_image_paths=resolved_paths,
                    eval_frames=eval_selected.frames,
                    eval_timestamps_sec=eval_selected.timestamps_sec,
                    view=selected_view,
                    eval_points=args.eval_points,
                    eval_sample_hz=float(args.sample_hz),
                    input_sample_hz=float(args.input_sample_hz),
                )
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                stats["records"] += 1
                stats["trajectory_records"] += 1
                emitted_for_traj = 1
            else:
                for frame, timestamp_sec, image_path in zip(
                    resolved_frames,
                    resolved_timestamps,
                    resolved_paths,
                ):
                    record = build_record(
                        bucket=bucket,
                        row_idx=row_idx,
                        row=row,
                        frame=frame,
                        timestamp_sec=timestamp_sec,
                        image_path=image_path,
                        view=selected_view,
                        is_terminal_point=(frame == terminal_frame),
                        selected_count=len(eval_selected.frames),
                        eval_points=args.eval_points,
                        sample_hz=float(args.sample_hz),
                    )
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    emitted_for_traj += 1
                    stats["records"] += 1
                    stats["point_records"] += 1
            if emitted_for_traj:
                emitted_trajectories += 1
                stats["trajectories"] += 1

    summary = {
        "out": str(args.out),
        "benchmark_root": str(args.benchmark_root),
        "frames_root": str(args.frames_root),
        "buckets": list(args.buckets),
        "eval_points": args.eval_points,
        "sample_hz": float(args.sample_hz) if args.eval_points == "time_hz" else None,
        "input_sample_hz": float(args.input_sample_hz),
        "record_format": args.record_format,
        "stats": dict(stats),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

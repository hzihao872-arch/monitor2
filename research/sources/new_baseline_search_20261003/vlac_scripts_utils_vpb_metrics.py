#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


TEST_BUCKETS = (
    "test_expert_seen",
    "test_expert_unseen",
    "test_nonexpert_seen",
    "test_nonexpert_unseen",
)
EXPERT_BUCKETS = {"test_expert_seen", "test_expert_unseen"}


@dataclass(frozen=True)
class SelectedFrames:
    frames: list[int]
    timestamps_sec: list[float | None]
    mode: str
    sample_hz: float | None


@dataclass(frozen=True)
class Trajectory:
    bucket: str
    global_episode_id: str
    frames: list[int]
    gt_progress: list[float]
    timestamps_sec: list[float | None]
    task_instruction: str
    task_description: str
    main_view: str | None
    fps: float | None
    semantic_anchor_frames: list[int]
    semantic_anchor_progress: list[float]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def split_json_path(benchmark_root: Path, bucket: str) -> Path:
    return benchmark_root / f"{bucket}.json"


def iter_benchmark_rows(
    benchmark_root: Path,
    buckets: Iterable[str] = TEST_BUCKETS,
) -> Iterable[tuple[str, int, dict[str, Any]]]:
    for bucket in buckets:
        path = split_json_path(benchmark_root, bucket)
        if not path.exists():
            raise FileNotFoundError(f"Missing benchmark split: {path}")
        rows = load_json(path)
        if not isinstance(rows, list):
            raise ValueError(f"Expected list in benchmark split: {path}")
        for idx, row in enumerate(rows):
            if not isinstance(row, dict):
                raise ValueError(f"Expected object row in {path} at index {idx}")
            yield bucket, idx, row


def finite_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def mean_or_none(values: Iterable[float | None]) -> float | None:
    clean = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    if not clean:
        return None
    return float(sum(clean) / len(clean))


def pearson_corr(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = sum((x - mean_x) ** 2 for x in xs)
    den_y = sum((y - mean_y) ** 2 for y in ys)
    if math.isclose(den_x, 0.0, rel_tol=0.0, abs_tol=1e-12):
        return None
    if math.isclose(den_y, 0.0, rel_tol=0.0, abs_tol=1e-12):
        return None
    value = num / math.sqrt(den_x * den_y)
    return value if math.isfinite(value) else None


def average_ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda idx: values[idx])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i + 1
        while (
            j < len(order)
            and math.isclose(values[order[j]], values[order[i]], rel_tol=0.0, abs_tol=1e-9)
        ):
            j += 1
        rank = (i + j - 1) / 2.0 + 1.0
        for pos in order[i:j]:
            ranks[pos] = rank
        i = j
    return ranks


def spearman_corr(xs: list[float], ys: list[float]) -> float | None:
    return pearson_corr(average_ranks(xs), average_ranks(ys))


def extract_view_from_main_path(main_path: str | None) -> str | None:
    raw = str(main_path or "").strip()
    if not raw:
        return None
    for part in Path(raw).parts:
        if part.startswith("observation.images."):
            view = part.split("observation.images.", 1)[1].strip()
            return view or None
    return None


def main_view_for_row(row: dict[str, Any]) -> str | None:
    meta = dict(row.get("metadata") or {})
    target_view = extract_view_from_main_path(meta.get("main_path"))
    available = [str(v) for v in meta.get("available_views", []) if str(v).strip()]
    if target_view:
        return target_view
    if available:
        return available[0]
    frame_index = row.get("frame_index")
    if isinstance(frame_index, dict):
        for image_map in frame_index.values():
            if isinstance(image_map, dict) and image_map:
                return sorted(str(k) for k in image_map.keys())[0]
    return None


def _nearest_frame(eligible: list[int], target_frame: float) -> int:
    best_idx = eligible[0]
    best_distance = abs(float(best_idx) - target_frame)
    for idx in eligible[1:]:
        distance = abs(float(idx) - target_frame)
        if distance < best_distance:
            best_idx = idx
            best_distance = distance
    return int(best_idx)


def sample_frame_indices_by_hz(
    frame_ids: list[int],
    *,
    fps: float,
    sample_hz: float,
) -> tuple[list[int], list[float]]:
    if not frame_ids or fps <= 0 or sample_hz <= 0:
        return [], []
    eligible = list(frame_ids)
    if eligible[0] != 0:
        raise ValueError("Frame-0 protocol requires the first valid frame to be 0")

    start_frame = 0
    end_frame = eligible[-1]
    duration_sec = max(0.0, end_frame / fps)
    step_sec = 1.0 / sample_hz

    target_times: list[float] = []
    current = 0.0
    eps = 1e-9
    while current <= duration_sec + eps:
        target_times.append(round(current, 6))
        current += step_sec
    if not target_times:
        target_times = [0.0]

    selected_indices: list[int] = []
    selected_times: list[float] = []
    seen: set[int] = set()
    for target_time in target_times:
        target_frame = target_time * fps
        idx = _nearest_frame(eligible, target_frame)
        if idx in seen:
            continue
        seen.add(idx)
        selected_indices.append(idx)
        selected_times.append(round(idx / fps, 6))

    if not selected_indices:
        selected_indices = [start_frame]
        selected_times = [0.0]
    return selected_indices, selected_times


def selected_frames_for_row(
    row: dict[str, Any],
    *,
    eval_points: str,
    sample_hz: float,
) -> SelectedFrames:
    frame_index = dict(row.get("frame_index") or {})
    dense_progress = dict(row.get("dense_kinematic_progress") or {})
    frame_ids = sorted(
        int(k)
        for k in frame_index.keys()
        if str(k) in dense_progress and finite_float(dense_progress.get(str(k))) is not None
    )
    if not frame_ids:
        raise ValueError("Frame-0 protocol requires at least one valid dense frame")
    if frame_ids[0] != 0:
        raise ValueError("Frame-0 protocol requires frame 0 with valid dense progress")

    if eval_points == "dense":
        return SelectedFrames(frame_ids, [None] * len(frame_ids), "dense", None)

    if eval_points == "semantic_anchors":
        anchor_frames: list[int] = []
        seen: set[int] = set()
        for anchor in row.get("semantic_anchors") or []:
            if not isinstance(anchor, dict):
                continue
            frame = finite_float(anchor.get("frame"))
            if frame is None:
                continue
            idx = int(frame)
            if idx in seen or idx not in frame_ids:
                continue
            seen.add(idx)
            anchor_frames.append(idx)
        anchor_frames.sort()
        if anchor_frames and anchor_frames[0] != 0:
            raise ValueError("Frame-0 protocol requires selected frames to start at frame 0")
        return SelectedFrames(anchor_frames, [None] * len(anchor_frames), "semantic_anchors", None)

    if eval_points != "time_hz":
        raise ValueError(f"Unsupported eval_points: {eval_points}")

    meta = dict(row.get("metadata") or {})
    fps = finite_float(meta.get("fps")) or 0.0
    frames, timestamps = sample_frame_indices_by_hz(
        frame_ids,
        fps=fps,
        sample_hz=sample_hz,
    )
    valid = [
        (frame, ts)
        for frame, ts in zip(frames, timestamps)
        if str(frame) in dense_progress and finite_float(dense_progress.get(str(frame))) is not None
    ]
    return SelectedFrames(
        [frame for frame, _ in valid],
        [ts for _, ts in valid],
        "time_hz",
        float(sample_hz),
    )


def semantic_anchor_points_for_row(row: dict[str, Any]) -> tuple[list[int], list[float]]:
    points_by_frame: dict[int, float] = {}
    for anchor in row.get("semantic_anchors") or []:
        if not isinstance(anchor, dict):
            continue
        frame = finite_float(anchor.get("frame"))
        progress = finite_float(anchor.get("human_annotated_progress"))
        if frame is None or progress is None:
            continue
        points_by_frame[int(frame)] = float(progress)
    frames = sorted(points_by_frame)
    return frames, [points_by_frame[frame] for frame in frames]


def build_trajectories(
    benchmark_root: Path,
    *,
    buckets: Iterable[str] = TEST_BUCKETS,
    eval_points: str = "time_hz",
    sample_hz: float = 1.0,
) -> list[Trajectory]:
    trajectories: list[Trajectory] = []
    seen_gids: set[str] = set()
    for bucket, row_idx, row in iter_benchmark_rows(benchmark_root, buckets):
        global_episode_id = str(row.get("global_episode_id") or "").strip()
        if not global_episode_id:
            raise ValueError(f"Missing global_episode_id in {bucket} row {row_idx}")
        if global_episode_id in seen_gids:
            raise ValueError(f"Duplicate global_episode_id across benchmark splits: {global_episode_id}")
        seen_gids.add(global_episode_id)

        selected = selected_frames_for_row(row, eval_points=eval_points, sample_hz=sample_hz)
        dense_progress = dict(row.get("dense_kinematic_progress") or {})
        gt_progress: list[float] = []
        frames: list[int] = []
        timestamps: list[float | None] = []
        for frame, timestamp in zip(selected.frames, selected.timestamps_sec):
            value = finite_float(dense_progress.get(str(frame)))
            if value is None:
                continue
            frames.append(int(frame))
            timestamps.append(timestamp)
            gt_progress.append(float(value))
        if not frames:
            continue

        meta = dict(row.get("metadata") or {})
        anchor_frames, anchor_progress = semantic_anchor_points_for_row(row)
        trajectories.append(
            Trajectory(
                bucket=bucket,
                global_episode_id=global_episode_id,
                frames=frames,
                gt_progress=gt_progress,
                timestamps_sec=timestamps,
                task_instruction=str(meta.get("task_instruction") or ""),
                task_description=str(meta.get("task_description") or ""),
                main_view=main_view_for_row(row),
                fps=finite_float(meta.get("fps")),
                semantic_anchor_frames=anchor_frames,
                semantic_anchor_progress=anchor_progress,
            )
        )
    return trajectories


def format_metric(value: Any, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        if not math.isfinite(value):
            return "n/a"
        return f"{value:.{digits}f}"
    return str(value)


def format_percent(value: Any, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "n/a"
    if not math.isfinite(number):
        return "n/a"
    return f"{number * 100.0:.{digits}f}%"


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)

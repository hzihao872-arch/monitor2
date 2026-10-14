#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from utils.vpb_metrics import (
    EXPERT_BUCKETS,
    TEST_BUCKETS,
    Trajectory,
    build_trajectories,
    dump_json,
    finite_float,
    format_metric,
    format_percent,
    markdown_table,
    mean_or_none,
    spearman_corr,
)


PredMap = dict[str, dict[int, float]]
SIGNED_NUM = r"([+-]?[0-9]+(?:\.[0-9]+)?)"
POINT_TIME_RE = re.compile(r"(?:Time|时间)[:：]?\s*([0-9]+(?:\.[0-9]+)?)\s*s?", re.IGNORECASE)
POINT_PROGRESS_LINE_RE = re.compile(rf"(?im)^\s*(?:Progress|进度)[:：]?\s*{SIGNED_NUM}\s*%")
INLINE_POINT_RE = re.compile(
    rf"(?:Time|时间)[:：]?\s*([0-9]+(?:\.[0-9]+)?)\s*s?\s*[,，]?\s*(?:Progress|进度)[:：]?\s*{SIGNED_NUM}\s*%",
    re.IGNORECASE,
)
SEEN_BUCKETS = ("test_expert_seen", "test_nonexpert_seen")
UNSEEN_BUCKETS = ("test_expert_unseen", "test_nonexpert_unseen")
LOCAL_DIRECTION_TAU_PERCENT = 0.0


def parse_args() -> argparse.Namespace:
    repo_root = SCRIPT_DIR.parent
    parser = argparse.ArgumentParser(
        description="Evaluate public Video-Progress Benchmark predictions."
    )
    parser.add_argument(
        "--benchmark-root",
        type=Path,
        default=repo_root / "splits",
        help="Directory containing HF Dataset splits/*.json.",
    )
    parser.add_argument(
        "--predictions",
        type=Path,
        help="VLAC-Cut batch prediction JSONL with global_episode_id, frames, and response.",
    )
    parser.add_argument("--out-json", type=Path, help="Output JSON report.")
    parser.add_argument("--out-md", type=Path, help="Output Markdown report.")
    parser.add_argument(
        "--buckets",
        nargs="+",
        default=list(TEST_BUCKETS),
        choices=list(TEST_BUCKETS),
        help="Benchmark buckets to evaluate.",
    )
    parser.add_argument(
        "--eval-points",
        choices=["time_hz", "dense", "semantic_anchors"],
        default="time_hz",
        help="Evaluation frame points. Default time_hz with --sample-hz 1.0 reconstructs the public 1Hz protocol.",
    )
    parser.add_argument(
        "--sample-hz",
        type=float,
        default=1.0,
        help="Sampling rate used when --eval-points=time_hz.",
    )
    parser.add_argument(
        "--success-threshold",
        type=float,
        default=90.0,
        help="Terminal success threshold in progress percent.",
    )
    parser.add_argument(
        "--clip-pred",
        nargs=2,
        type=float,
        metavar=("MIN", "MAX"),
        default=None,
        help="Optionally clip predictions before evaluation.",
    )
    parser.add_argument(
        "--interpolate-missing",
        action="store_true",
        help="Linearly interpolate missing prediction frames within each trajectory. This is not the strict default.",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Write a diagnostic report even when predictions do not cover every required evaluation point.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run a small synthetic self-test and exit.",
    )
    return parser.parse_args()


def load_prediction_rows(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        rows = []
        for line_no, line in enumerate(text.splitlines(), start=1):
            raw = line.strip()
            if not raw:
                continue
            item = json.loads(raw)
            if not isinstance(item, dict):
                raise ValueError(f"Prediction line {line_no} is not an object")
            rows.append(item)
        return rows

    if isinstance(payload, list):
        if not all(isinstance(item, dict) for item in payload):
            raise ValueError("Prediction JSON list must contain objects")
        return list(payload)
    if isinstance(payload, dict):
        for key in ("predictions", "results", "rows"):
            value = payload.get(key)
            if isinstance(value, list):
                if not all(isinstance(item, dict) for item in value):
                    raise ValueError(f"Prediction JSON field {key!r} must contain objects")
                return list(value)
        return [payload]
    raise ValueError("Prediction file must be JSONL, a JSON object, or a JSON list")


def strip_code_fence(text: str) -> str:
    cleaned = str(text or "").strip()
    if cleaned.startswith("```") and cleaned.endswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return cleaned


def dedupe_sorted_points(times: list[float], values: list[float]) -> tuple[list[float], list[float]]:
    if not times:
        return [], []
    pairs = sorted(zip(times, values), key=lambda item: (item[0], item[1]))
    out_times: list[float] = []
    out_values: list[float] = []
    cur_time = pairs[0][0]
    bucket: list[float] = []
    for time_val, progress_val in pairs:
        if time_val != cur_time:
            out_times.append(float(cur_time))
            out_values.append(float(sum(bucket) / len(bucket)))
            cur_time = time_val
            bucket = [float(progress_val)]
        else:
            bucket.append(float(progress_val))
    out_times.append(float(cur_time))
    out_values.append(float(sum(bucket) / len(bucket)))
    return out_times, out_values


def parse_point_blocks(text: str) -> tuple[list[float], list[float]]:
    cleaned = strip_code_fence(text)
    if not cleaned:
        return [], []
    inline_matches = INLINE_POINT_RE.findall(cleaned)
    if inline_matches:
        return dedupe_sorted_points(
            [float(time_val) for time_val, _ in inline_matches],
            [float(progress_val) for _, progress_val in inline_matches],
        )
    blocks = re.split(r"(?=(?:Time|时间)[:：]?\s*[0-9])", cleaned, flags=re.IGNORECASE)
    times: list[float] = []
    values: list[float] = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        time_match = POINT_TIME_RE.search(block)
        progress_match = POINT_PROGRESS_LINE_RE.search(block)
        if time_match and progress_match:
            times.append(float(time_match.group(1)))
            values.append(float(progress_match.group(1)))
    return dedupe_sorted_points(times, values)


def align_curve_to_length(raw_times: list[float], raw_values: list[float], target_len: int) -> list[float]:
    """Match the formal VLAC evaluator's index-normalized curve alignment."""
    if target_len <= 0 or not raw_values:
        return []
    if len(raw_values) == 1:
        return [float(raw_values[0])] * target_len
    times, values = dedupe_sorted_points(raw_times, raw_values)
    if len(values) == 1:
        return [float(values[0])] * target_len
    start = float(times[0])
    end = float(times[-1])
    if math.isclose(start, end):
        if len(values) == 1:
            positions = [0.0]
        else:
            positions = [idx * float(target_len - 1) / float(len(values) - 1) for idx in range(len(values))]
    else:
        positions = [(time_val - start) / (end - start) * float(target_len - 1) for time_val in times]

    aligned: list[float] = []
    for target in range(target_len):
        target_f = float(target)
        if target_f <= positions[0]:
            aligned.append(float(values[0]))
            continue
        if target_f >= positions[-1]:
            aligned.append(float(values[-1]))
            continue
        for idx in range(len(positions) - 1):
            if positions[idx] <= target_f <= positions[idx + 1]:
                if math.isclose(positions[idx], positions[idx + 1]):
                    value = float(values[idx])
                else:
                    alpha = (target_f - positions[idx]) / (positions[idx + 1] - positions[idx])
                    value = float(values[idx]) + alpha * (float(values[idx + 1]) - float(values[idx]))
                aligned.append(float(value))
                break
    return aligned


def maybe_clip(value: float, clip_range: tuple[float, float] | None, stats: Counter[str]) -> float:
    if clip_range is None:
        if value < 0.0 or value > 100.0:
            stats["outside_nominal_0_100_predictions"] += 1
        return value
    lo, hi = clip_range
    clipped = min(max(value, lo), hi)
    if clipped != value:
        stats["clipped_predictions"] += 1
    return clipped


def add_prediction(
    pred_map: PredMap,
    *,
    gid: str,
    frame: int,
    value: Any,
    clip_range: tuple[float, float] | None,
    stats: Counter[str],
) -> None:
    pred_value = finite_float(value)
    if pred_value is None:
        stats["invalid_prediction_values"] += 1
        return
    pred_value = maybe_clip(float(pred_value), clip_range, stats)
    frame_map = pred_map.setdefault(gid, {})
    if int(frame) in frame_map:
        stats["duplicate_frame_predictions"] += 1
    frame_map[int(frame)] = pred_value
    stats["valid_prediction_values"] += 1


def add_canonical_vlac_response_predictions(
    pred_map: PredMap,
    *,
    gid: str,
    row: dict[str, Any],
    clip_range: tuple[float, float] | None,
    stats: Counter[str],
) -> None:
    frame_sequence = row.get("frames")
    if not isinstance(frame_sequence, list) or not frame_sequence:
        stats["canonical_rows_missing_frames"] += 1
        return
    valid_frames: list[int] = []
    for raw_frame in frame_sequence:
        frame = finite_float(raw_frame)
        if frame is None:
            stats["canonical_rows_invalid_frames"] += 1
            return
        valid_frames.append(int(frame))
    if valid_frames[0] != 0:
        raise ValueError(
            f"Prediction row for {gid} starts at frame {valid_frames[0]}, but evaluation requires frame 0"
        )

    response = row.get("response")
    if not isinstance(response, str) or not response.strip():
        stats["canonical_rows_missing_response"] += 1
        return

    raw_times, raw_values = parse_point_blocks(response)

    if not raw_values:
        stats["canonical_response_parse_failed"] += 1
        return

    aligned = align_curve_to_length(raw_times, raw_values, len(valid_frames))
    if not aligned:
        stats["canonical_response_align_failed"] += 1
        return

    for frame, value in zip(valid_frames, aligned):
        add_prediction(
            pred_map,
            gid=gid,
            frame=frame,
            value=value,
            clip_range=clip_range,
            stats=stats,
        )
    stats["canonical_response_rows_aligned_by_index"] += 1


def load_predictions(
    path: Path,
    *,
    trajectories: list[Trajectory],
    clip_range: tuple[float, float] | None,
) -> tuple[PredMap, dict[str, Any]]:
    traj_by_gid = {traj.global_episode_id: traj for traj in trajectories}
    pred_map: PredMap = {}
    stats: Counter[str] = Counter()
    unknown_examples: list[str] = []

    rows = load_prediction_rows(path)
    stats["rows"] = len(rows)
    for row in rows:
        gid = str(row.get("global_episode_id") or "").strip()
        if not gid:
            stats["rows_missing_global_episode_id"] += 1
            continue
        traj = traj_by_gid.get(gid)
        if traj is None:
            stats["unknown_global_episode_id"] += 1
            if len(unknown_examples) < 10:
                unknown_examples.append(gid)
            continue

        add_canonical_vlac_response_predictions(
            pred_map,
            gid=gid,
            row=row,
            clip_range=clip_range,
            stats=stats,
        )

    known_frames = {traj.global_episode_id: set(traj.frames) for traj in trajectories}
    extra_frame_count = 0
    for gid, frame_map in pred_map.items():
        eval_frames = known_frames.get(gid, set())
        for frame in frame_map:
            if frame not in eval_frames:
                extra_frame_count += 1
    stats["prediction_frames_outside_eval_points"] = extra_frame_count

    return pred_map, {"stats": dict(stats), "unknown_global_episode_id_examples": unknown_examples}


def interpolated_value(frame_map: dict[int, float], frame: int) -> float | None:
    if frame in frame_map:
        return frame_map[frame]
    if not frame_map:
        return None
    points = sorted(frame_map.items())
    if frame <= points[0][0]:
        return points[0][1]
    if frame >= points[-1][0]:
        return points[-1][1]
    for (left_frame, left_value), (right_frame, right_value) in zip(points, points[1:]):
        if left_frame <= frame <= right_frame:
            if right_frame == left_frame:
                return left_value
            alpha = (frame - left_frame) / float(right_frame - left_frame)
            return left_value + alpha * (right_value - left_value)
    return None


def interpolated_prediction_for_frame(pred_map: PredMap, gid: str, frame: int) -> float | None:
    frame_map = pred_map.get(gid)
    if not frame_map:
        return None
    return interpolated_value(frame_map, int(frame))


def prediction_at(
    pred_map: PredMap,
    gid: str,
    frame: int,
    *,
    interpolate_missing: bool,
) -> float | None:
    frame_map = pred_map.get(gid)
    if not frame_map:
        return None
    if frame in frame_map:
        return frame_map[frame]
    if interpolate_missing:
        return interpolated_value(frame_map, frame)
    return None


def summarize_curve(
    trajectories: list[Trajectory],
    pred_map: PredMap,
    *,
    interpolate_missing: bool,
    include_voc: bool,
) -> dict[str, Any]:
    base_points = sum(len(traj.frames) for traj in trajectories)
    matched_trajs = 0
    matched_points = 0
    valid_points = 0
    traj_with_valid_pred = 0
    mae_values: list[float] = []
    prc_values: list[float] = []
    voc_values: list[float] = []

    for traj in trajectories:
        has_predictions = traj.global_episode_id in pred_map
        if has_predictions:
            matched_trajs += 1
            matched_points += len(traj.frames)

        gt_curve: list[float] = []
        pred_curve: list[float] = []
        for frame, gt in zip(traj.frames, traj.gt_progress):
            pred = prediction_at(
                pred_map,
                traj.global_episode_id,
                frame,
                interpolate_missing=interpolate_missing,
            )
            if pred is None or not math.isfinite(float(pred)):
                continue
            valid_points += 1
            gt_curve.append(float(gt))
            pred_curve.append(float(pred))

        if gt_curve:
            traj_with_valid_pred += 1
            mae_values.append(
                sum(abs(gt - pred) for gt, pred in zip(gt_curve, pred_curve))
                / len(gt_curve)
            )

        prc = spearman_corr(gt_curve, pred_curve)
        if prc is not None:
            prc_values.append(prc)
        if include_voc:
            voc = spearman_corr(pred_curve, [float(i) for i in range(1, len(pred_curve) + 1)])
            if voc is not None:
                voc_values.append(voc)

    return {
        "traj_base_total": len(trajectories),
        "traj_matched": matched_trajs,
        "traj_with_valid_pred": traj_with_valid_pred,
        "point_base_total": base_points,
        "point_total_on_matched": matched_points,
        "point_valid": valid_points,
        "point_coverage_to_base": (valid_points / base_points) if base_points else None,
        "point_coverage_on_matched": (valid_points / matched_points) if matched_points else None,
        "mae": mean_or_none(mae_values),
        "mae_valid_traj": len(mae_values),
        "prc": mean_or_none(prc_values),
        "prc_valid_traj": len(prc_values),
        "voc": mean_or_none(voc_values) if include_voc else None,
        "voc_valid_traj": len(voc_values) if include_voc else 0,
    }


def average_precision_ranked(items: list[tuple[int, float]]) -> float | None:
    positive_total = int(sum(label for label, _ in items))
    if not items or positive_total == 0:
        return None
    ranked = sorted(enumerate(items), key=lambda item: (-float(item[1][1]), item[0]))
    hits = 0
    precision_sum = 0.0
    for rank, (_, (label, _score)) in enumerate(ranked, start=1):
        if int(label) == 1:
            hits += 1
            precision_sum += hits / rank
    return precision_sum / positive_total


def classify_delta(delta: float, tau_percent: float) -> str:
    if delta > tau_percent:
        return "positive"
    if delta < -tau_percent:
        return "negative"
    return "neutral"


def summarize_local_direction_ap(
    trajectories: list[Trajectory],
    pred_map: PredMap,
    *,
    tau_percent: float,
) -> dict[str, Any]:
    transition_total = 0
    valid = 0
    missing = 0
    gt_counts: Counter[str] = Counter()
    valid_gt_counts: Counter[str] = Counter()
    positive_items: list[tuple[int, float]] = []
    negative_items: list[tuple[int, float]] = []

    for traj in trajectories:
        frames = traj.semantic_anchor_frames
        progress = traj.semantic_anchor_progress
        for idx in range(max(0, len(frames) - 1)):
            transition_total += 1
            gt_delta = float(progress[idx + 1]) - float(progress[idx])
            gt_class = classify_delta(gt_delta, tau_percent)
            gt_counts[gt_class] += 1

            left = interpolated_prediction_for_frame(pred_map, traj.global_episode_id, frames[idx])
            right = interpolated_prediction_for_frame(pred_map, traj.global_episode_id, frames[idx + 1])
            if left is None or right is None or not math.isfinite(float(left)) or not math.isfinite(float(right)):
                missing += 1
                continue

            valid += 1
            valid_gt_counts[gt_class] += 1
            pred_delta = float(right) - float(left)
            positive_items.append((1 if gt_delta > tau_percent else 0, pred_delta))
            negative_items.append((1 if gt_delta < -tau_percent else 0, -pred_delta))

    ap_positive = average_precision_ranked(positive_items)
    ap_negative = average_precision_ranked(negative_items)
    macro_ap = (
        0.5 * (ap_positive + ap_negative)
        if ap_positive is not None and ap_negative is not None
        else None
    )
    return {
        "tau_percent": float(tau_percent),
        "transition_total": int(transition_total),
        "valid": int(valid),
        "missing": int(missing),
        "gt_counts": {key: int(gt_counts.get(key, 0)) for key in ("positive", "neutral", "negative")},
        "valid_gt_counts": {key: int(valid_gt_counts.get(key, 0)) for key in ("positive", "neutral", "negative")},
        "ap_positive_support": int(sum(label for label, _ in positive_items)),
        "ap_negative_support": int(sum(label for label, _ in negative_items)),
        "ap_positive": ap_positive,
        "ap_negative": ap_negative,
        "macro_ap_d": macro_ap,
    }


def finalize_terminal_counter(counter: Counter[str]) -> dict[str, Any]:
    support = int(counter.get("support", 0))
    valid_final = int(counter.get("valid_final", 0))
    tp = int(counter.get("tp", 0))
    fn = int(counter.get("fn", 0))
    fp = int(counter.get("fp", 0))
    tn = int(counter.get("tn", 0))
    gt_success = int(counter.get("gt_success", 0))
    gt_failure = int(counter.get("gt_failure", 0))
    pred_success = int(counter.get("pred_success", 0))
    pred_failure = int(counter.get("pred_failure", 0))
    missing_final = int(counter.get("missing_final", 0))
    valid_binary = tp + fn + fp + tn

    f1_success = (2 * tp / (2 * tp + fp + fn)) if (2 * tp + fp + fn) else None
    f1_failure = (2 * tn / (2 * tn + fp + fn)) if (2 * tn + fp + fn) else None
    macro_f1_terminal = (
        (f1_success + f1_failure) / 2.0
        if f1_success is not None and f1_failure is not None
        else None
    )
    return {
        "support": support,
        "gt_success": gt_success,
        "gt_failure": gt_failure,
        "valid_final": valid_final,
        "missing_final": missing_final,
        "pred_success": pred_success,
        "pred_failure": pred_failure,
        "tp": tp,
        "fn": fn,
        "fp": fp,
        "tn": tn,
        "tsa": ((tp + tn) / valid_binary) if valid_binary else None,
        "f1_success": f1_success,
        "f1_failure": f1_failure,
        "macro_f1_terminal": macro_f1_terminal,
    }


def summarize_terminal(
    trajectories: list[Trajectory],
    pred_map: PredMap,
    *,
    success_threshold: float,
    interpolate_missing: bool,
) -> dict[str, Any]:
    counter: Counter[str] = Counter()
    for traj in trajectories:
        counter["support"] += 1
        gt_final = float(traj.gt_progress[-1])
        gt_success = gt_final >= success_threshold
        if gt_success:
            counter["gt_success"] += 1
        else:
            counter["gt_failure"] += 1

        pred_final = prediction_at(
            pred_map,
            traj.global_episode_id,
            traj.frames[-1],
            interpolate_missing=interpolate_missing,
        )
        if pred_final is None or not math.isfinite(float(pred_final)):
            counter["missing_final"] += 1
            continue
        counter["valid_final"] += 1
        pred_success = float(pred_final) >= success_threshold
        if pred_success:
            counter["pred_success"] += 1
        else:
            counter["pred_failure"] += 1

        if gt_success and pred_success:
            counter["tp"] += 1
        elif gt_success and not pred_success:
            counter["fn"] += 1
        elif (not gt_success) and pred_success:
            counter["fp"] += 1
        else:
            counter["tn"] += 1
    return finalize_terminal_counter(counter)


def build_report(
    *,
    trajectories: list[Trajectory],
    pred_map: PredMap,
    prediction_info: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    selected_buckets = list(config["buckets"])
    by_bucket = {bucket: [traj for traj in trajectories if traj.bucket == bucket] for bucket in selected_buckets}
    interpolate_missing = bool(config["interpolate_missing"])
    success_threshold = float(config["success_threshold_percent"])
    seen_trajs = [
        traj for bucket in SEEN_BUCKETS for traj in by_bucket.get(bucket, [])
    ]
    unseen_trajs = [
        traj for bucket in UNSEEN_BUCKETS for traj in by_bucket.get(bucket, [])
    ]

    curve_per_bucket = {
        bucket: summarize_curve(
            bucket_trajs,
            pred_map,
            interpolate_missing=interpolate_missing,
            include_voc=(bucket in EXPERT_BUCKETS),
        )
        for bucket, bucket_trajs in by_bucket.items()
    }
    terminal_per_bucket = {
        bucket: summarize_terminal(
            bucket_trajs,
            pred_map,
            success_threshold=success_threshold,
            interpolate_missing=interpolate_missing,
        )
        for bucket, bucket_trajs in by_bucket.items()
    }
    local_direction_per_bucket = {
        bucket: summarize_local_direction_ap(
            bucket_trajs,
            pred_map,
            tau_percent=LOCAL_DIRECTION_TAU_PERCENT,
        )
        for bucket, bucket_trajs in by_bucket.items()
    }

    return {
        "config": config,
        "benchmark": {
            "traj_total": len(trajectories),
            "point_total": sum(len(traj.frames) for traj in trajectories),
            "buckets": {
                bucket: {
                    "traj_total": len(bucket_trajs),
                    "point_total": sum(len(traj.frames) for traj in bucket_trajs),
                }
                for bucket, bucket_trajs in by_bucket.items()
            },
        },
        "prediction_input": prediction_info,
        "curve": {
            "overall_4bucket": summarize_curve(
                trajectories,
                pred_map,
                interpolate_missing=interpolate_missing,
                include_voc=False,
            ),
            "per_bucket": curve_per_bucket,
        },
        "terminal": {
            "overall_4bucket": summarize_terminal(
                trajectories,
                pred_map,
                success_threshold=success_threshold,
                interpolate_missing=interpolate_missing,
            ),
            "seen_merged": summarize_terminal(
                seen_trajs,
                pred_map,
                success_threshold=success_threshold,
                interpolate_missing=interpolate_missing,
            ),
            "unseen_merged": summarize_terminal(
                unseen_trajs,
                pred_map,
                success_threshold=success_threshold,
                interpolate_missing=interpolate_missing,
            ),
            "per_bucket": terminal_per_bucket,
        },
        "local_direction_ap": {
            "tau_percent": LOCAL_DIRECTION_TAU_PERCENT,
            "overall_4bucket": summarize_local_direction_ap(
                trajectories,
                pred_map,
                tau_percent=LOCAL_DIRECTION_TAU_PERCENT,
            ),
            "seen_merged": summarize_local_direction_ap(
                seen_trajs,
                pred_map,
                tau_percent=LOCAL_DIRECTION_TAU_PERCENT,
            ),
            "unseen_merged": summarize_local_direction_ap(
                unseen_trajs,
                pred_map,
                tau_percent=LOCAL_DIRECTION_TAU_PERCENT,
            ),
            "per_bucket": local_direction_per_bucket,
        },
    }


def validate_no_missing(report: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []

    curve_sources = [("overall_4bucket", report["curve"]["overall_4bucket"])]
    curve_sources.extend(
        (bucket, item)
        for bucket, item in report["curve"]["per_bucket"].items()
    )
    for scope, item in curve_sources:
        if int(item.get("point_valid", 0)) != int(item.get("point_base_total", 0)):
            errors.append(
                f"curve.{scope}: point_valid={item.get('point_valid')} "
                f"point_base_total={item.get('point_base_total')}"
            )
        if int(item.get("traj_with_valid_pred", 0)) != int(item.get("traj_base_total", 0)):
            errors.append(
                f"curve.{scope}: traj_with_valid_pred={item.get('traj_with_valid_pred')} "
                f"traj_base_total={item.get('traj_base_total')}"
            )

    terminal_sources = [
        ("overall_4bucket", report["terminal"]["overall_4bucket"]),
        ("seen_merged", report["terminal"]["seen_merged"]),
        ("unseen_merged", report["terminal"]["unseen_merged"]),
    ]
    terminal_sources.extend(
        (bucket, item)
        for bucket, item in report["terminal"]["per_bucket"].items()
    )
    for scope, item in terminal_sources:
        if int(item.get("valid_final", 0)) != int(item.get("support", 0)) or int(item.get("missing_final", 0)) != 0:
            errors.append(
                f"terminal.{scope}: valid_final={item.get('valid_final')} "
                f"support={item.get('support')} missing_final={item.get('missing_final')}"
            )

    direction_sources = [
        ("overall_4bucket", report["local_direction_ap"]["overall_4bucket"]),
        ("seen_merged", report["local_direction_ap"]["seen_merged"]),
        ("unseen_merged", report["local_direction_ap"]["unseen_merged"]),
    ]
    direction_sources.extend(
        (bucket, item)
        for bucket, item in report["local_direction_ap"]["per_bucket"].items()
    )
    for scope, item in direction_sources:
        if int(item.get("valid", 0)) != int(item.get("transition_total", 0)) or int(item.get("missing", 0)) != 0:
            errors.append(
                f"local_direction_ap.{scope}: valid={item.get('valid')} "
                f"transition_total={item.get('transition_total')} missing={item.get('missing')}"
            )

    return {
        "no_missing_check": not errors,
        "error_count": len(errors),
        "errors": errors,
    }


def point_ratio(item: dict[str, Any]) -> str:
    return f"{int(item.get('point_valid', 0))}/{int(item.get('point_base_total', 0))}"


def traj_ratio(item: dict[str, Any]) -> str:
    return f"{int(item.get('traj_with_valid_pred', 0))}/{int(item.get('traj_base_total', 0))}"


def terminal_ratio(item: dict[str, Any]) -> str:
    return f"{int(item.get('valid_final', 0))}/{int(item.get('support', 0))}"


def build_markdown(report: dict[str, Any]) -> str:
    config = report["config"]
    selected_buckets = list(config["buckets"])
    lines: list[str] = []
    lines.append("# Video-Progress Benchmark Evaluation")
    lines.append("")
    lines.append("## Protocol")
    lines.append("")
    lines.append(f"- eval_points: `{config['eval_points']}`")
    lines.append(f"- sample_hz: `{config['sample_hz']}`")
    lines.append(f"- success_threshold: `{config['success_threshold_percent']}`")
    lines.append(f"- interpolate_missing: `{config['interpolate_missing']}`")
    lines.append(f"- allow_missing: `{config['allow_missing']}`")
    lines.append(f"- no_missing_check: `{report['validation']['no_missing_check']}`")
    lines.append("- Curve metrics are trajectory-equal means over metric-valid trajectories.")
    lines.append("- VOC is reported only for expert bucket rows.")
    lines.append("- Local Direction AP uses adjacent released `semantic_anchors`; predictions are linearly interpolated at anchor frames.")
    lines.append("- By default, missing curve, terminal, or local-direction predictions stop evaluation; use `--allow-missing` only for diagnostics.")
    lines.append("")

    curve_rows: list[list[Any]] = []
    curve_sources = [("overall_4bucket", report["curve"]["overall_4bucket"])]
    for bucket in selected_buckets:
        curve_sources.append((bucket, report["curve"]["per_bucket"][bucket]))
    for scope, item in curve_sources:
        include_voc = scope in EXPERT_BUCKETS
        row = [
            scope,
            format_percent(item.get("point_coverage_to_base")),
            point_ratio(item),
            traj_ratio(item),
            format_metric(item.get("mae")),
            format_metric(item.get("prc")),
        ]
        if include_voc:
            row.append(format_metric(item.get("voc")))
        else:
            row.append("n/a")
        curve_rows.append(
            row
        )
    lines.append("## Curve Metrics")
    lines.append("")
    lines.append(
        markdown_table(
            ["scope", "coverage", "point_valid/base", "traj_valid/base", "MAE", "PRC", "VOC"],
            curve_rows,
        )
    )
    lines.append("")

    terminal_rows: list[list[Any]] = []
    terminal_sources = [
        ("overall_4bucket", report["terminal"]["overall_4bucket"]),
        ("seen_merged", report["terminal"]["seen_merged"]),
        ("unseen_merged", report["terminal"]["unseen_merged"]),
    ]
    for scope, item in terminal_sources:
        terminal_rows.append(
            [
                scope,
                terminal_ratio(item),
                format_metric(item.get("tsa")),
                format_metric(item.get("f1_success")),
                format_metric(item.get("f1_failure")),
                format_metric(item.get("macro_f1_terminal")),
                int(item.get("tp", 0)),
                int(item.get("fn", 0)),
                int(item.get("fp", 0)),
                int(item.get("tn", 0)),
                int(item.get("missing_final", 0)),
            ]
        )
    lines.append("## Terminal Metrics")
    lines.append("")
    lines.append(
        markdown_table(
            [
                "scope",
                "valid_final/support",
                "TSA",
                "F1_S",
                "F1_F",
                "MacroF1_T",
                "TP",
                "FN",
                "FP",
                "TN",
                "missing_final",
            ],
            terminal_rows,
        )
    )
    lines.append("")

    local_direction_rows: list[list[Any]] = []
    local_direction_sources = [
        ("overall_4bucket", report["local_direction_ap"]["overall_4bucket"]),
        ("seen_merged", report["local_direction_ap"]["seen_merged"]),
        ("unseen_merged", report["local_direction_ap"]["unseen_merged"]),
    ]
    for scope, item in local_direction_sources:
        gt_counts = item.get("gt_counts") or {}
        local_direction_rows.append(
            [
                scope,
                f"{int(item.get('valid', 0))}/{int(item.get('transition_total', 0))}",
                f"{int(gt_counts.get('positive', 0))}/{int(gt_counts.get('neutral', 0))}/{int(gt_counts.get('negative', 0))}",
                f"{int(item.get('ap_positive_support', 0))}/{int(item.get('ap_negative_support', 0))}",
                format_percent(item.get("ap_positive")),
                format_percent(item.get("ap_negative")),
                format_percent(item.get("macro_ap_d")),
            ]
        )
    lines.append("## Local Direction AP")
    lines.append("")
    tau_text = f"{float(report['local_direction_ap']['tau_percent']):g}%"
    lines.append(
        f"`tau={tau_text}`. "
        "`AP+ = AP(y=Delta_gt>tau, score=Delta_pred)`, "
        "`AP- = AP(y=Delta_gt<-tau, score=-Delta_pred)`, "
        "`MacroAP_D = (AP+ + AP-) / 2`."
    )
    lines.append("")
    lines.append(
        markdown_table(
            ["scope", "valid/trans", "GT +/0/-", "support +/-", "AP+", "AP-", "MacroAP_D"],
            local_direction_rows,
        )
    )
    lines.append("")

    lines.append("## Prediction Diagnostics")
    lines.append("")
    stats = report["prediction_input"]["stats"]
    diagnostic_rows = [[key, value] for key, value in sorted(stats.items())]
    lines.append(markdown_table(["key", "value"], diagnostic_rows))
    lines.append("")
    return "\n".join(lines)


def run_self_test() -> None:
    def row(gid: str, gt_values: list[float], *, success: bool = True) -> dict[str, Any]:
        frames = [0, 30, 60]
        if not success:
            gt_values = [0.0, 20.0, 50.0]
        return {
            "global_episode_id": gid,
            "metadata": {
                "fps": 30.0,
                "main_path": f"ARX-data/mock/videos/chunk-000/observation.images.front/{gid}",
                "available_views": ["front"],
                "task_instruction": "mock task",
                "task_description": "mock task",
            },
            "frame_index": {
                str(frame): {"front": f"__VLAC2_FRAMES_ROOT__/mock/{gid}/{frame}-90.jpg"}
                for frame in frames
            },
            "dense_kinematic_progress": {
                str(frame): value for frame, value in zip(frames, gt_values)
            },
            "semantic_anchors": [
                {"frame": frame, "human_annotated_progress": value}
                for frame, value in zip(frames, gt_values)
            ],
        }

    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir) / "splits"
        root.mkdir(parents=True)
        rows_by_bucket = {
            "test_expert_seen": [row("traj_success_a", [0.0, 50.0, 100.0])],
            "test_expert_unseen": [row("traj_success_b", [0.0, 40.0, 100.0])],
            "test_nonexpert_seen": [row("traj_failure_a", [0.0, 20.0, 50.0], success=False)],
            "test_nonexpert_unseen": [row("traj_failure_b", [0.0, 10.0, 40.0], success=False)],
        }
        for bucket, rows in rows_by_bucket.items():
            (root / f"{bucket}.json").write_text(
                json.dumps(rows),
                encoding="utf-8",
            )
        pred_path = Path(tmp_dir) / "predictions.jsonl"
        with pred_path.open("w", encoding="utf-8") as f:
            for rows in rows_by_bucket.values():
                for item in rows:
                    points = sorted(
                        (int(frame), float(value))
                        for frame, value in item["dense_kinematic_progress"].items()
                    )
                    f.write(
                        json.dumps(
                            {
                                "global_episode_id": item["global_episode_id"],
                                "frames": [frame for frame, _value in points],
                                "response": "\n".join(
                                    f"时间: {idx:.1f}s, 进度: {value:g}%"
                                    for idx, (_frame, value) in enumerate(points)
                                ),
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
        trajectories = build_trajectories(root, eval_points="time_hz", sample_hz=1.0)
        pred_map, prediction_info = load_predictions(
            pred_path,
            trajectories=trajectories,
            clip_range=None,
        )
        report = build_report(
            trajectories=trajectories,
            pred_map=pred_map,
            prediction_info=prediction_info,
            config={
                "benchmark_root": str(root),
                "predictions": str(pred_path),
                "buckets": list(TEST_BUCKETS),
                "eval_points": "time_hz",
                "sample_hz": 1.0,
                "success_threshold_percent": 90.0,
                "interpolate_missing": False,
                "clip_pred": None,
            },
        )
        assert report["benchmark"]["traj_total"] == 4
        assert report["curve"]["overall_4bucket"]["mae"] == 0.0
        assert report["terminal"]["overall_4bucket"]["tsa"] == 1.0
        assert report["local_direction_ap"]["overall_4bucket"]["ap_positive"] == 1.0
        assert validate_no_missing(report)["no_missing_check"] is True

        bad_root = Path(tmp_dir) / "bad_splits"
        bad_root.mkdir()
        bad_row = row("bad_start", [0.0, 50.0, 100.0])
        bad_row["frame_index"].pop("0")
        bad_row["dense_kinematic_progress"].pop("0")
        (bad_root / "test_expert_seen.json").write_text(json.dumps([bad_row]), encoding="utf-8")
        try:
            build_trajectories(
                bad_root,
                buckets=["test_expert_seen"],
                eval_points="time_hz",
                sample_hz=1.0,
            )
        except ValueError as exc:
            assert "Frame-0 protocol" in str(exc)
        else:
            raise AssertionError("Frame-0 benchmark validation did not fail")

        bad_pred_path = Path(tmp_dir) / "bad_predictions.jsonl"
        bad_pred_path.write_text(
            json.dumps(
                {
                    "global_episode_id": "traj_success_a",
                    "frames": [30, 60],
                    "response": "时间: 0.0s, 进度: 0%\n时间: 1.0s, 进度: 100%",
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        try:
            load_predictions(bad_pred_path, trajectories=trajectories, clip_range=None)
        except ValueError as exc:
            assert "frame 0" in str(exc)
        else:
            raise AssertionError("Frame-0 prediction validation did not fail")
    print("[self-test] ok")


def main() -> None:
    args = parse_args()
    if args.self_test:
        run_self_test()
        return
    if args.predictions is None:
        raise SystemExit("--predictions is required unless --self-test is set")
    if args.out_json is None and args.out_md is None:
        raise SystemExit("At least one of --out-json or --out-md is required")
    if args.sample_hz <= 0:
        raise SystemExit("--sample-hz must be positive")

    clip_range = None
    if args.clip_pred is not None:
        lo, hi = args.clip_pred
        if lo > hi:
            raise SystemExit("--clip-pred MIN must be <= MAX")
        clip_range = (float(lo), float(hi))

    trajectories = build_trajectories(
        args.benchmark_root,
        buckets=args.buckets,
        eval_points=args.eval_points,
        sample_hz=float(args.sample_hz),
    )
    pred_map, prediction_info = load_predictions(
        args.predictions,
        trajectories=trajectories,
        clip_range=clip_range,
    )
    config = {
        "benchmark_root": str(args.benchmark_root),
        "predictions": str(args.predictions),
        "buckets": list(args.buckets),
        "eval_points": args.eval_points,
        "sample_hz": float(args.sample_hz) if args.eval_points == "time_hz" else None,
        "success_threshold_percent": float(args.success_threshold),
        "interpolate_missing": bool(args.interpolate_missing),
        "allow_missing": bool(args.allow_missing),
        "clip_pred": list(clip_range) if clip_range is not None else None,
    }
    report = build_report(
        trajectories=trajectories,
        pred_map=pred_map,
        prediction_info=prediction_info,
        config=config,
    )
    report["validation"] = validate_no_missing(report)
    if not args.allow_missing and not report["validation"]["no_missing_check"]:
        preview = "\n".join(report["validation"]["errors"][:20])
        raise SystemExit(
            "Predictions do not cover every required evaluation item. "
            "Use --allow-missing only for a diagnostic report.\n"
            f"{preview}"
        )
    if args.out_json is not None:
        dump_json(args.out_json, report)
    if args.out_md is not None:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(build_markdown(report), encoding="utf-8")

    print(
        json.dumps(
            {
                "traj_total": report["benchmark"]["traj_total"],
                "point_total": report["benchmark"]["point_total"],
                "curve_overall": report["curve"]["overall_4bucket"],
                "terminal_overall": report["terminal"]["overall_4bucket"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

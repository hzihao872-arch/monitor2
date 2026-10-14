#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import re
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

THIS_DIR = Path(__file__).resolve().parent
MODEL_ROOT = THIS_DIR.parent
EXAMPLES_ROOT = MODEL_ROOT / "examples"
MANIFEST_PATH = EXAMPLES_ROOT / "examples_manifest.json"
CHUNK_ALL_SAMPLE_HZ = 2.0

SIGNED_NUM = r"([+-]?[0-9]+(?:\.[0-9]+)?)"
POINT_TIME_RE = re.compile(r"(?:Time|时间)[:：]?\s*([0-9]+(?:\.[0-9]+)?)\s*s?", re.IGNORECASE)
POINT_PROGRESS_LINE_RE = re.compile(rf"(?im)^\s*(?:Progress|进度)[:：]?\s*{SIGNED_NUM}\s*%")
INLINE_POINT_RE = re.compile(
    rf"(?:Time|时间)[:：]?\s*([0-9]+(?:\.[0-9]+)?)\s*s?\s*[,，]?\s*(?:Progress|进度)[:：]?\s*{SIGNED_NUM}\s*%",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the released VLAC model on one bundled example with chunk_all prompt and fixed 2hz video input."
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        default=MODEL_ROOT,
        help="Path to the released VLAC model directory.",
    )
    parser.add_argument(
        "--example-id",
        type=str,
        required=True,
        help="Bundled example id, for example: example_01",
    )
    parser.add_argument(
        "--output-jsonl",
        type=Path,
        default=None,
        help="Optional output path. Defaults to quick_start/outputs/<example_id>.jsonl",
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=1024,
        help="Generation cap for the response.",
    )
    return parser.parse_args()


def load_manifest() -> dict[str, dict]:
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {item["example_id"]: item for item in payload.get("examples", [])}


def strip_code_fence(text: str) -> str:
    cleaned = str(text or "").strip()
    if cleaned.startswith("```") and cleaned.endswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return cleaned


def extract_plan_text(task_instruction: str, task_description: str) -> str:
    lines = [line.strip() for line in str(task_description or "").splitlines() if line.strip()]
    if not lines:
        return ""
    first_line = lines[0].rstrip("：:")
    normalized_instruction = str(task_instruction or "").strip().rstrip("：:")
    if normalized_instruction and first_line == normalized_instruction:
        lines = lines[1:]
    return "\n".join(lines).strip()


def build_chunk_all_prompt(metadata: dict[str, Any]) -> str:
    task_instruction = str(metadata.get("task_instruction") or "").strip()
    task_description = str(metadata.get("task_description") or "").strip()
    plan_text = extract_plan_text(task_instruction, task_description)
    task_and_plan = task_instruction if not plan_text else f"{task_instruction}\n{plan_text}"
    return (
        f"任务描述和具体规划: {task_and_plan}\n\n"
        "请根据任务描述和具体规划，找到并逐点生成视频中的关键动作点和相应的进度标注。"
        "输出格式要求：每个关键点一行，格式为：\n"
        "时间: X.Xs, 进度: Y%\n\n"
        "请严格按照上述格式输出，不要输出额外说明。"
    )


def compute_sampled_indices_2hz(num_frames: int, fps: float, sample_hz: float) -> tuple[list[int], list[float]]:
    if num_frames <= 0 or fps <= 0 or sample_hz <= 0:
        return [], []
    frame_ids = list(range(num_frames))
    eligible_arr = np.array(frame_ids, dtype=float)
    start_frame = frame_ids[0]
    end_frame = frame_ids[-1]
    duration_sec = max(0.0, (end_frame - start_frame) / fps)
    step_sec = 1.0 / sample_hz

    target_times: list[float] = []
    current = 0.0
    eps = 1e-9
    while current <= duration_sec + eps:
        target_times.append(round(current, 6))
        current += step_sec
    if not target_times:
        target_times = [0.0]

    sampled_indices: list[int] = []
    sampled_timestamps_sec: list[float] = []
    seen = set()
    for target_time in target_times:
        target_frame = start_frame + target_time * fps
        pos = int(np.argmin(np.abs(eligible_arr - target_frame)))
        idx = int(eligible_arr[pos])
        if idx in seen:
            continue
        seen.add(idx)
        sampled_indices.append(idx)
        sampled_timestamps_sec.append(round((idx - start_frame) / fps, 6))
    if not sampled_indices:
        sampled_indices = [0]
        sampled_timestamps_sec = [0.0]
    return sampled_indices, sampled_timestamps_sec


def extract_sampled_frame_paths(
    video_path: Path,
    sampled_indices: list[int],
    *,
    temp_dir: Path,
) -> tuple[list[str], dict[str, float]]:
    try:
        from decord import VideoReader, cpu
    except ImportError as exc:
        raise SystemExit("Missing dependency: decord is required for 2hz frame sampling in quick_start.") from exc

    vr = VideoReader(str(video_path), ctx=cpu(0), num_threads=1)
    actual_frame_count = len(vr)
    if not sampled_indices:
        raise SystemExit("No sampled frame indices were generated.")
    if sampled_indices[-1] >= actual_frame_count:
        raise SystemExit(
            f"Bundled video is shorter than expected. Need frame index {sampled_indices[-1]}, got {actual_frame_count} frames."
        )

    batch = vr.get_batch(sampled_indices).asnumpy()
    frame_paths: list[str] = []
    for idx, frame in zip(sampled_indices, batch, strict=True):
        frame_path = temp_dir / f"frame_{idx:06d}.jpg"
        Image.fromarray(frame).save(frame_path, quality=95)
        frame_paths.append(str(frame_path.resolve()))

    video_stats = {
        "decoded_frame_count": float(actual_frame_count),
        "decoded_avg_fps": float(vr.get_avg_fps()),
    }
    return frame_paths, video_stats


def load_swift_runtime():
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
    os.environ.setdefault("IMAGE_MAX_TOKEN_NUM", "256")
    os.environ.setdefault("VIDEO_MAX_TOKEN_NUM", "256")
    os.environ.setdefault("VIDEO_MIN_TOKEN_NUM", "4")
    os.environ.setdefault("QWEN_VL_UTILS_MAX_FRAME_LIST", "0")
    import torch
    try:
        from swift.llm import InferRequest, PtEngine, RequestConfig
    except ImportError:
        from swift.infer_engine import InferRequest, RequestConfig, TransformersEngine as PtEngine  # type: ignore
    return torch, InferRequest, PtEngine, RequestConfig


def dedupe_sorted_points(times: list[float], values: list[float]) -> tuple[list[float], list[float]]:
    if not times:
        return [], []
    pairs = sorted(zip(times, values), key=lambda item: (item[0], item[1]))
    out_times: list[float] = []
    out_values: list[float] = []
    cur_time = pairs[0][0]
    bucket: list[float] = []
    for time_val, progress_val in pairs:
        if not math.isclose(time_val, cur_time, rel_tol=0.0, abs_tol=1e-9):
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


def align_curve_to_gt_dense(
    point_times_sec: list[float],
    point_values: list[float],
    gt_times_sec: list[float],
) -> list[float]:
    if not gt_times_sec or not point_values:
        return []
    if len(point_values) == 1:
        return [float(point_values[0])] * len(gt_times_sec)
    times, values = dedupe_sorted_points(point_times_sec, point_values)
    if len(values) == 1:
        return [float(values[0])] * len(gt_times_sec)
    aligned = np.interp(
        np.array(gt_times_sec, dtype=float),
        np.array(times, dtype=float),
        np.array(values, dtype=float),
        left=float(values[0]),
        right=float(values[-1]),
    )
    return [float(x) for x in aligned.tolist()]


def pearson_corr(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    x = np.array(xs, dtype=float)
    y = np.array(ys, dtype=float)
    if np.allclose(x, x[0]) or np.allclose(y, y[0]):
        return None
    value = float(np.corrcoef(x, y)[0, 1])
    if math.isnan(value) or not math.isfinite(value):
        return None
    return value


def average_ranks(values: list[float]) -> list[float]:
    arr = np.array(values, dtype=float)
    order = np.argsort(arr, kind="mergesort")
    ranks = np.zeros(arr.shape[0], dtype=float)
    idx = 0
    while idx < len(order):
        next_idx = idx + 1
        while next_idx < len(order) and math.isclose(
            arr[order[next_idx]],
            arr[order[idx]],
            rel_tol=0.0,
            abs_tol=1e-9,
        ):
            next_idx += 1
        ranks[order[idx:next_idx]] = (idx + next_idx - 1) / 2.0 + 1.0
        idx = next_idx
    return ranks.tolist()


def spearman_corr(xs: list[float], ys: list[float]) -> float | None:
    return pearson_corr(average_ranks(xs), average_ranks(ys))


def compute_curve_metrics(gt_dense_progress: list[float], pred_dense_progress: list[float]) -> dict[str, float | int | None]:
    if not gt_dense_progress or len(gt_dense_progress) != len(pred_dense_progress):
        return {
            "point_count": 0,
            "mae": None,
            "rmse": None,
            "pearson": None,
            "spearman": None,
        }
    gt_arr = np.array(gt_dense_progress, dtype=float)
    pred_arr = np.array(pred_dense_progress, dtype=float)
    diff = pred_arr - gt_arr
    return {
        "point_count": int(len(gt_dense_progress)),
        "mae": float(np.mean(np.abs(diff))),
        "rmse": float(np.sqrt(np.mean(diff ** 2))),
        "pearson": pearson_corr(pred_arr.tolist(), gt_arr.tolist()),
        "spearman": spearman_corr(pred_arr.tolist(), gt_arr.tolist()),
    }


def maybe_write_curve_plot(
    *,
    output_path: Path,
    gt_times_sec: list[float],
    gt_dense_progress: list[float],
    pred_dense_progress: list[float],
    pred_point_times_sec: list[float],
    pred_point_progress: list[float],
) -> str | None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return None

    plot_path = output_path.with_name(f"{output_path.stem}_curve_compare.png")
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(gt_times_sec, gt_dense_progress, color="#2563eb", linewidth=2.2, label="GT dense progress")
    if pred_dense_progress:
        ax.plot(gt_times_sec, pred_dense_progress, color="#f97316", linewidth=2.2, label="Pred aligned curve")
    if pred_point_progress:
        ax.scatter(
            pred_point_times_sec,
            pred_point_progress,
            color="#111827",
            s=28,
            zorder=3,
            label="Pred chunk_all points",
        )
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Progress (%)")
    ax.grid(alpha=0.2, linewidth=0.8)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(plot_path, dpi=180)
    plt.close(fig)
    return str(plot_path.resolve())


def format_metric(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.4f}"


def main() -> int:
    args = parse_args()
    manifest = load_manifest()
    if args.example_id not in manifest:
        raise SystemExit(f"Unknown example id: {args.example_id}")

    example_info = manifest[args.example_id]
    metadata_path = MODEL_ROOT / example_info["metadata_path"]
    video_path = MODEL_ROOT / example_info["video_path"]
    if not metadata_path.exists():
        raise SystemExit(f"Missing metadata: {metadata_path}")
    if not video_path.exists():
        raise SystemExit(f"Missing video: {video_path}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    gt_dense_progress = [float(x) for x in list(metadata.get("benchmark_dense_progress") or [])]
    fps = float(metadata.get("fps") or 0.0)
    num_frames = int(metadata.get("num_frames") or len(gt_dense_progress))
    if not gt_dense_progress:
        raise SystemExit("Missing benchmark_dense_progress in example metadata.")
    if fps <= 0 or num_frames <= 0:
        raise SystemExit(f"Invalid metadata fps/num_frames: fps={fps}, num_frames={num_frames}")

    prompt = build_chunk_all_prompt(metadata)
    output_path = args.output_jsonl or (THIS_DIR / "outputs" / f"{args.example_id}.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    sampled_indices_2hz, sampled_timestamps_sec_2hz = compute_sampled_indices_2hz(
        num_frames=num_frames,
        fps=fps,
        sample_hz=CHUNK_ALL_SAMPLE_HZ,
    )
    gt_times_sec = [round(frame_idx / fps, 6) for frame_idx in range(len(gt_dense_progress))]

    torch, InferRequest, PtEngine, RequestConfig = load_swift_runtime()
    device_map = "auto"
    engine = PtEngine(
        str(args.model_path.resolve()),
        model_type="qwen3_moe_vl",
        max_batch_size=1,
        device_map=device_map,
    )

    with tempfile.TemporaryDirectory(prefix=f"{args.example_id}_2hz_frames_") as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        frame_paths, video_stats = extract_sampled_frame_paths(
            video_path,
            sampled_indices_2hz,
            temp_dir=temp_dir,
        )
        request = InferRequest(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "video", "video": frame_paths},
                        {"type": "text", "text": prompt},
                    ],
                }
            ]
        )
        response = engine.infer(
            [request],
            RequestConfig(max_tokens=args.max_new_tokens, temperature=0.0, top_k=1, top_p=1.0),
        )[0].choices[0].message.content

    pred_point_times_sec, pred_point_progress = parse_point_blocks(response)
    pred_dense_progress = align_curve_to_gt_dense(
        point_times_sec=pred_point_times_sec,
        point_values=pred_point_progress,
        gt_times_sec=gt_times_sec,
    )
    curve_metrics = compute_curve_metrics(gt_dense_progress, pred_dense_progress)
    plot_path = maybe_write_curve_plot(
        output_path=output_path,
        gt_times_sec=gt_times_sec,
        gt_dense_progress=gt_dense_progress,
        pred_dense_progress=pred_dense_progress,
        pred_point_times_sec=pred_point_times_sec,
        pred_point_progress=pred_point_progress,
    )

    output_row = {
        "example_id": args.example_id,
        "bucket": metadata.get("bucket"),
        "global_episode_id": metadata.get("global_episode_id"),
        "task_instruction": metadata.get("task_instruction"),
        "task_description": metadata.get("task_description"),
        "video_path": str(video_path.resolve()),
        "prompt_variant": "chunk_all",
        "input_sample_hz": CHUNK_ALL_SAMPLE_HZ,
        "input_frame_indices_2hz": sampled_indices_2hz,
        "input_timestamps_sec_2hz": sampled_timestamps_sec_2hz,
        "input_frame_count_2hz": len(sampled_indices_2hz),
        "decoded_video_stats": video_stats,
        "prompt": prompt,
        "response": response,
        "benchmark_progress_type": metadata.get("benchmark_progress_type"),
        "benchmark_progress_source": metadata.get("benchmark_progress_source"),
        "benchmark_semantic_anchors": metadata.get("benchmark_semantic_anchors"),
        "gt_dense_progress": gt_dense_progress,
        "gt_dense_timestamps_sec": gt_times_sec,
        "pred_curve_parse_ok": bool(pred_point_progress),
        "pred_curve_point_times_sec": pred_point_times_sec,
        "pred_curve_point_progress": pred_point_progress,
        "pred_dense_progress_aligned_to_gt": pred_dense_progress,
        "curve_compare_metrics": curve_metrics,
        "curve_compare_plot": plot_path,
    }
    output_path.write_text(json.dumps(output_row, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"example_id={args.example_id}")
    print(f"video_path={video_path.resolve()}")
    print(f"output_jsonl={output_path.resolve()}")
    print(f"input_sample_hz={CHUNK_ALL_SAMPLE_HZ}")
    print(f"input_frame_count_2hz={len(sampled_indices_2hz)}")
    print(f"pred_keypoint_count={len(pred_point_progress)}")
    print(f"gt_dense_point_count={len(gt_dense_progress)}")
    print(f"curve_mae={format_metric(curve_metrics['mae'])}")
    print(f"curve_rmse={format_metric(curve_metrics['rmse'])}")
    print(f"curve_pearson={format_metric(curve_metrics['pearson'])}")
    print(f"curve_spearman={format_metric(curve_metrics['spearman'])}")
    if plot_path is not None:
        print(f"curve_compare_plot={plot_path}")
    print()
    print(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

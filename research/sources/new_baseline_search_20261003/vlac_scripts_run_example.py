#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parent
DEFAULT_MODEL_ID = "InternRobotics/VLAC-Cut"
DEFAULT_SAMPLE_HZ = 2.0
MODEL_ASSUMED_SAMPLE_HZ = 2.0

SIGNED_NUM = r"([+-]?[0-9]+(?:\.[0-9]+)?)"
POINT_TIME_RE = re.compile(r"(?:Time|时间)[:：]?\s*([0-9]+(?:\.[0-9]+)?)\s*s?", re.IGNORECASE)
POINT_PROGRESS_LINE_RE = re.compile(rf"(?im)^\s*(?:Progress|进度)[:：]?\s*{SIGNED_NUM}\s*%")
INLINE_POINT_RE = re.compile(
    rf"(?:Time|时间)[:：]?\s*([0-9]+(?:\.[0-9]+)?)\s*s?\s*[,，]?\s*(?:Progress|进度)[:：]?\s*{SIGNED_NUM}\s*%",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run VLAC progress inference on an arbitrary input video.",
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default=DEFAULT_MODEL_ID,
        help="Hugging Face model id or local path to the released VLAC-Cut model.",
    )
    parser.add_argument(
        "--video-path",
        type=Path,
        required=True,
        help="Path to the input video.",
    )
    parser.add_argument(
        "--task-instruction",
        type=str,
        default=None,
        help="Task instruction used to build the default chunk_all prompt.",
    )
    parser.add_argument(
        "--task-plan",
        type=str,
        default=None,
        help="Optional task plan text appended after the task instruction.",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=None,
        help="Optional full prompt override. If set, task instruction and plan are ignored.",
    )
    parser.add_argument(
        "--sample-hz",
        type=float,
        default=DEFAULT_SAMPLE_HZ,
        help="Video sampling rate in Hz. Defaults to 2.0.",
    )
    parser.add_argument(
        "--output-jsonl",
        type=Path,
        default=None,
        help="Optional output path. If omitted, print the response only and do not save a JSONL file.",
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=1024,
        help="Generation cap for the response.",
    )
    return parser.parse_args()


def build_chunk_all_prompt(task_instruction: str, task_plan: str | None) -> str:
    task_instruction = task_instruction.strip()
    task_plan = (task_plan or "").strip()
    task_and_plan = task_instruction if not task_plan else f"{task_instruction}\n{task_plan}"
    return (
        f"任务描述和具体规划: {task_and_plan}\n\n"
        "请根据任务描述和具体规划，找到并逐点生成视频中的关键动作点和相应的进度标注。"
        "输出格式要求：每个关键点一行，格式为：\n"
        "时间: X.Xs, 进度: Y%\n\n"
        "请严格按照上述格式输出，不要输出额外说明。"
    )


def resolve_prompt(args: argparse.Namespace) -> tuple[str, str, str | None, str | None]:
    prompt = args.prompt.strip() if args.prompt else None
    task_plan = args.task_plan.strip() if args.task_plan else None
    task_instruction = args.task_instruction.strip() if args.task_instruction else None

    if prompt:
        return prompt, "raw_prompt", task_instruction, task_plan

    if not task_instruction:
        raise SystemExit(
            "Either provide --prompt, or provide --task-instruction with optional --task-plan."
        )

    return build_chunk_all_prompt(task_instruction, task_plan), "task_instruction_plus_plan", task_instruction, task_plan


def resolve_video_path(video_path_arg: Path) -> Path:
    video_path = video_path_arg.resolve()
    if not video_path.exists():
        raise SystemExit(f"Missing video: {video_path}")
    return video_path


def resolve_model_path(raw_model_path: str) -> str:
    raw = str(raw_model_path or "").strip()
    if not raw:
        raise SystemExit("--model-path must not be empty")
    expanded = Path(raw).expanduser()
    if expanded.exists():
        return str(expanded.resolve())
    if raw.startswith(("/", ".", "~")):
        raise SystemExit(f"Missing model path: {expanded}")
    return raw


def maybe_relativize_to_repo_root(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def compute_sampled_indices(num_frames: int, fps: float, sample_hz: float) -> tuple[list[int], list[float]]:
    try:
        import numpy as np
    except ImportError as exc:
        raise SystemExit("Missing dependency: numpy is required for video sampling.") from exc

    if num_frames <= 0:
        raise SystemExit(f"Invalid decoded frame count: {num_frames}")
    if fps <= 0:
        raise SystemExit(f"Invalid decoded fps: {fps}")
    if sample_hz <= 0:
        raise SystemExit(f"sample_hz must be positive, got {sample_hz}")

    frame_ids = list(range(num_frames))
    eligible_arr = np.array(frame_ids, dtype=float)
    duration_sec = max(0.0, (num_frames - 1) / fps)
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
        target_frame = target_time * fps
        pos = int(np.argmin(np.abs(eligible_arr - target_frame)))
        idx = int(eligible_arr[pos])
        if idx in seen:
            continue
        seen.add(idx)
        sampled_indices.append(idx)
        sampled_timestamps_sec.append(round(idx / fps, 6))
    return sampled_indices, sampled_timestamps_sec


def extract_sampled_frame_paths(
    video_path: Path,
    sample_hz: float,
    *,
    temp_dir: Path,
) -> tuple[list[str], dict[str, float], list[int], list[float]]:
    try:
        from decord import VideoReader, cpu
    except ImportError as exc:
        raise SystemExit("Missing dependency: decord is required for video sampling.") from exc
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit("Missing dependency: Pillow is required for video sampling.") from exc

    vr = VideoReader(str(video_path), ctx=cpu(0), num_threads=1)
    actual_frame_count = len(vr)
    actual_fps = float(vr.get_avg_fps())
    sampled_indices, sampled_timestamps_sec = compute_sampled_indices(actual_frame_count, actual_fps, sample_hz)
    if not sampled_indices:
        raise SystemExit("No sampled frame indices were generated.")
    if sampled_indices[-1] >= actual_frame_count:
        raise SystemExit(
            f"Decoded video is shorter than expected. Need frame index {sampled_indices[-1]}, "
            f"got {actual_frame_count} frames."
        )

    batch = vr.get_batch(sampled_indices).asnumpy()
    frame_paths: list[str] = []
    for idx, frame in zip(sampled_indices, batch, strict=True):
        frame_path = temp_dir / f"frame_{idx:06d}.jpg"
        Image.fromarray(frame).save(frame_path, quality=95)
        frame_paths.append(str(frame_path.resolve()))

    video_stats = {
        "decoded_frame_count": float(actual_frame_count),
        "decoded_avg_fps": actual_fps,
        "decoded_duration_sec": round(max(0.0, (actual_frame_count - 1) / actual_fps), 6),
    }
    return frame_paths, video_stats, sampled_indices, sampled_timestamps_sec


def load_swift_runtime():
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
    os.environ.setdefault("IMAGE_MAX_TOKEN_NUM", "256")
    os.environ.setdefault("VIDEO_MAX_TOKEN_NUM", "256")
    os.environ.setdefault("VIDEO_MIN_TOKEN_NUM", "4")
    os.environ.setdefault("QWEN_VL_UTILS_MAX_FRAME_LIST", "0")

    try:
        import torch  # noqa: F401
    except ImportError as exc:
        raise SystemExit("Missing dependency: torch is required for VLAC-Cut inference.") from exc

    try:
        from swift.llm import InferRequest, PtEngine, RequestConfig
    except ImportError:
        from swift.infer_engine import InferRequest, RequestConfig, TransformersEngine as PtEngine  # type: ignore
    return InferRequest, PtEngine, RequestConfig


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
        if abs(time_val - cur_time) > 1e-9:
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


def scale_times(times_sec: list[float], *, from_hz: float, to_hz: float) -> list[float]:
    if from_hz <= 0 or to_hz <= 0:
        return list(times_sec)
    scale = float(from_hz) / float(to_hz)
    return [round(float(time_val) * scale, 6) for time_val in times_sec]


def main() -> int:
    args = parse_args()
    model_path = resolve_model_path(args.model_path)

    prompt, prompt_source, task_instruction, task_plan = resolve_prompt(args)
    video_path = resolve_video_path(args.video_path)
    video_path_for_output = maybe_relativize_to_repo_root(video_path)
    output_path = args.output_jsonl.resolve() if args.output_jsonl is not None else None
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    InferRequest, PtEngine, RequestConfig = load_swift_runtime()
    engine = PtEngine(
        model_path,
        model_type="qwen3_moe_vl",
        max_batch_size=1,
        device_map="auto",
    )

    with tempfile.TemporaryDirectory(prefix="vlac_cut_frames_") as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        frame_paths, video_stats, sampled_indices, sampled_timestamps_sec = extract_sampled_frame_paths(
            video_path,
            args.sample_hz,
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

    pred_point_times_model_sec, pred_point_progress = parse_point_blocks(response)
    pred_point_times_sec = scale_times(
        pred_point_times_model_sec,
        from_hz=MODEL_ASSUMED_SAMPLE_HZ,
        to_hz=float(args.sample_hz),
    )

    output_row: dict[str, object] = {}
    if task_instruction is not None:
        output_row["task_instruction"] = task_instruction
    if task_plan:
        output_row["task_plan"] = task_plan

    output_row.update(
        {
            "video_path": video_path_for_output,
            "prompt_source": prompt_source,
            "prompt_variant": "chunk_all" if prompt_source != "raw_prompt" else "custom",
            "input_sample_hz": float(args.sample_hz),
            "model_assumed_sample_hz": MODEL_ASSUMED_SAMPLE_HZ,
            "output_time_scale_to_video_sec": MODEL_ASSUMED_SAMPLE_HZ / float(args.sample_hz),
            "input_frame_indices": sampled_indices,
            "input_timestamps_sec": sampled_timestamps_sec,
            "input_frame_count": len(sampled_indices),
            "decoded_video_stats": video_stats,
            "prompt": prompt,
            "response": response,
            "pred_curve_parse_ok": bool(pred_point_progress),
            "pred_curve_point_times_model_sec": pred_point_times_model_sec,
            "pred_curve_point_times_sec": pred_point_times_sec,
            "pred_curve_point_progress": pred_point_progress,
        }
    )
    if output_path is not None:
        output_path.write_text(json.dumps(output_row, ensure_ascii=False) + "\n", encoding="utf-8")

    if output_path is not None:
        print(f"video_path={video_path}")
        print(f"output_jsonl={output_path}")
        print(f"input_sample_hz={float(args.sample_hz):.4f}")
        print(f"output_time_scale_to_video_sec={MODEL_ASSUMED_SAMPLE_HZ / float(args.sample_hz):.6f}")
        print(f"input_frame_count={len(sampled_indices)}")
        print(f"pred_keypoint_count={len(pred_point_progress)}")
        print()
    if abs(float(args.sample_hz) - MODEL_ASSUMED_SAMPLE_HZ) > 1e-9:
        print(
            "Warning: --sample-hz is not 2.0. The raw response printed below uses the model's "
            "2Hz time axis; scaled video-time points are saved in pred_curve_point_times_sec "
            "when --output-jsonl is provided."
        )
        print()
    print(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

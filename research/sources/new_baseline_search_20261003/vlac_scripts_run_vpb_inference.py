#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run VLAC-Cut batch inference from a public VPB evaluation manifest."
    )
    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="Hugging Face model id or local path to the released VLAC-Cut model.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="JSONL file produced by build_vpb_manifest.py.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output prediction JSONL path.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of manifest rows to run.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Append to --out and skip global_episode_id values already present in it.",
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=1024,
        help="Generation cap for each response.",
    )
    parser.add_argument(
        "--device-map",
        default="auto",
        help="Device map passed to Transformers from_pretrained.",
    )
    parser.add_argument(
        "--dtype",
        default=None,
        help="Torch dtype passed to Transformers. Defaults to auto.",
    )
    parser.add_argument(
        "--attn-implementation",
        default=None,
        help="Optional attention implementation passed to Transformers, for example flash_attention_2 or sdpa.",
    )
    parser.add_argument(
        "--check-files",
        action="store_true",
        help="Fail before inference if any manifest image path is missing.",
    )
    return parser.parse_args()


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


def load_transformers_runtime():
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
    os.environ.setdefault("IMAGE_MAX_TOKEN_NUM", "256")
    os.environ.setdefault("VIDEO_MAX_TOKEN_NUM", "256")
    os.environ.setdefault("VIDEO_MIN_TOKEN_NUM", "4")
    os.environ.setdefault("QWEN_VL_UTILS_MAX_FRAME_LIST", "0")

    try:
        import torch
    except ImportError as exc:
        raise SystemExit("Missing dependency: torch is required for VLAC-Cut inference.") from exc

    try:
        from transformers import AutoModelForImageTextToText, AutoProcessor
    except ImportError as exc:
        raise SystemExit("Missing dependency: transformers is required for VLAC-Cut inference.") from exc

    return torch, AutoModelForImageTextToText, AutoProcessor


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            raw = line.strip()
            if not raw:
                continue
            item = json.loads(raw)
            if not isinstance(item, dict):
                raise ValueError(f"{path}:{line_no} is not a JSON object")
            yield line_no, item


def existing_global_episode_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    done: set[str] = set()
    for _line_no, row in iter_jsonl(path):
        gid = str(row.get("global_episode_id") or "").strip()
        if gid:
            done.add(gid)
    return done


def require_manifest_row(row: dict[str, Any], line_no: int, *, check_files: bool) -> tuple[str, list[int], list[str], str, float]:
    gid = str(row.get("global_episode_id") or "").strip()
    if not gid:
        raise ValueError(f"manifest line {line_no}: missing global_episode_id")

    frames_raw = row.get("frames")
    if not isinstance(frames_raw, list) or not frames_raw:
        raise ValueError(f"manifest line {line_no}: missing non-empty frames")
    try:
        frames = [int(frame) for frame in frames_raw]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"manifest line {line_no}: frames must be integers") from exc
    if frames[0] != 0:
        raise ValueError(f"manifest line {line_no}: expected official VPB frames to start at 0")

    image_paths_raw = row.get("image_paths")
    if not isinstance(image_paths_raw, list) or len(image_paths_raw) != len(frames):
        raise ValueError(f"manifest line {line_no}: image_paths must align with frames")
    image_paths = [str(path) for path in image_paths_raw]
    if check_files:
        missing = [path for path in image_paths if not Path(path).exists()]
        if missing:
            preview = ", ".join(missing[:3])
            raise FileNotFoundError(f"manifest line {line_no}: missing image files: {preview}")

    prompt = str(row.get("vlac_cut_prompt") or "").strip()
    if not prompt:
        raise ValueError(f"manifest line {line_no}: missing vlac_cut_prompt")

    sample_hz_raw = row.get("input_sample_hz", row.get("sample_hz", 2.0))
    try:
        sample_hz = float(sample_hz_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"manifest line {line_no}: invalid input_sample_hz") from exc
    if sample_hz <= 0:
        raise ValueError(f"manifest line {line_no}: input_sample_hz must be positive")
    return gid, frames, image_paths, prompt, sample_hz


def load_model_and_processor(
    *,
    model_path: str,
    device_map: str,
    dtype: str | None,
    attn_implementation: str | None,
):
    _torch, AutoModelForImageTextToText, AutoProcessor = load_transformers_runtime()
    processor = AutoProcessor.from_pretrained(model_path)

    model_kwargs: dict[str, Any] = {
        "device_map": device_map,
        "dtype": dtype or "auto",
    }
    if attn_implementation:
        model_kwargs["attn_implementation"] = attn_implementation

    try:
        model = AutoModelForImageTextToText.from_pretrained(model_path, **model_kwargs)
    except TypeError as exc:
        if "dtype" not in str(exc):
            raise
        model_kwargs["torch_dtype"] = model_kwargs.pop("dtype")
        model = AutoModelForImageTextToText.from_pretrained(model_path, **model_kwargs)
    if getattr(model, "generation_config", None) is not None:
        for key in ("temperature", "top_p", "top_k"):
            if hasattr(model.generation_config, key):
                setattr(model.generation_config, key, None)
    model.eval()
    return model, processor


def infer_one(
    *,
    model,
    processor,
    image_paths: list[str],
    prompt: str,
    sample_hz: float,
    max_new_tokens: int,
) -> str:
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "video", "video": image_paths},
                {"type": "text", "text": prompt},
            ],
        }
    ]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    video_metadata = {
        "total_num_frames": len(image_paths),
        "fps": float(sample_hz),
        "frames_indices": list(range(len(image_paths))),
    }
    inputs = processor(
        text=[text],
        videos=[[image_paths]],
        padding=True,
        return_tensors="pt",
        return_metadata=True,
        do_sample_frames=False,
        video_metadata=video_metadata,
    )
    normalize_qwen3_video_grid(inputs)
    inputs = inputs.to(model.device)
    inputs.pop("video_metadata", None)

    generated_ids = model.generate(
        **inputs,
        max_new_tokens=int(max_new_tokens),
        do_sample=False,
    )
    generated_ids_trimmed = [
        output_ids[len(input_ids) :] for input_ids, output_ids in zip(inputs.input_ids, generated_ids, strict=True)
    ]
    return str(
        processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0]
    )


def count_token_type_spans(token_type_ids, token_type: int) -> int:
    values = token_type_ids.tolist()
    count = 0
    previous = None
    for value in values:
        if value == token_type and previous != token_type:
            count += 1
        previous = value
    return count


def normalize_qwen3_video_grid(inputs) -> None:
    mm_token_type_ids = inputs.get("mm_token_type_ids")
    video_grid_thw = inputs.get("video_grid_thw")
    if mm_token_type_ids is None or video_grid_thw is None:
        return
    if len(mm_token_type_ids) != 1 or len(video_grid_thw) != 1:
        return

    video_span_count = count_token_type_spans(mm_token_type_ids[0], 2)
    if video_span_count <= 1:
        return

    grid = video_grid_thw[0]
    temporal = int(grid[0].item())
    if temporal % video_span_count != 0:
        return

    split_temporal = temporal // video_span_count
    expanded = grid.repeat(video_span_count, 1)
    expanded[:, 0] = split_temporal
    inputs["video_grid_thw"] = expanded


def main() -> int:
    args = parse_args()
    model_path = resolve_model_path(args.model_path)
    manifest_path = args.manifest.resolve()
    out_path = args.out.resolve()

    if not manifest_path.exists():
        raise SystemExit(f"Missing manifest: {manifest_path}")
    if args.limit is not None and args.limit <= 0:
        raise SystemExit("--limit must be positive when provided")

    done = existing_global_episode_ids(out_path) if args.resume else set()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if args.resume else "w"

    model, processor = load_model_and_processor(
        model_path=model_path,
        device_map=str(args.device_map),
        dtype=args.dtype,
        attn_implementation=args.attn_implementation,
    )

    processed = 0
    skipped = 0
    with out_path.open(mode, encoding="utf-8") as out_f:
        for line_no, row in iter_jsonl(manifest_path):
            gid, frames, image_paths, prompt, sample_hz = require_manifest_row(
                row,
                line_no,
                check_files=bool(args.check_files),
            )
            if gid in done:
                skipped += 1
                continue
            if args.limit is not None and processed >= args.limit:
                break

            response = infer_one(
                model=model,
                processor=processor,
                image_paths=image_paths,
                prompt=prompt,
                sample_hz=sample_hz,
                max_new_tokens=int(args.max_new_tokens),
            )
            out_f.write(
                json.dumps(
                    {
                        "global_episode_id": gid,
                        "frames": frames,
                        "response": str(response or ""),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            out_f.flush()
            processed += 1
            print(f"processed={processed} global_episode_id={gid}", flush=True)

    print(
        json.dumps(
            {
                "manifest": str(manifest_path),
                "out": str(out_path),
                "backend": "transformers",
                "processed": processed,
                "skipped_existing": skipped,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

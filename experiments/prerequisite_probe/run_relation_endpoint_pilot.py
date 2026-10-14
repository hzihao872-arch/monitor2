"""Development-only paired D2/relation-endpoint runner. Reads model_input only.

Never import truth, mappings, old scores, or continuation videos here. Each raw
visual call is flushed before the next call. Scoring is a separate local step.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .monitor_relation_endpoint_v1 import pair_result, parse_record, prompt_for
from .run_monitor_qwen import (FRAME_SECONDS, IMAGE_SIZE, append_jsonl,
                               collect_inputs, decode_selected, model_call, sha256)


def checked_paths(input_dir: Path, output: Path) -> tuple[Path, Path]:
    input_dir, output = input_dir.resolve(), output.resolve()
    if input_dir.name != "model_input":
        raise ValueError("only model_input is permitted")
    if output == input_dir or input_dir in output.parents:
        raise ValueError("output must be outside model_input")
    if output.exists():
        raise FileExistsError(output)
    return input_dir, output


def inspect_inputs(input_dir: Path) -> list[dict]:
    """Verify the anonymous videos and every decoded pixel hash before inference."""
    rows = collect_inputs(input_dir)
    media_path = input_dir / "media_hashes.json"
    media = json.loads(media_path.read_text(encoding="utf-8"))
    clips = {entry["video"]: entry for entry in media["clips"]}
    if set(clips) != {row["video"] for row in rows}:
        raise ValueError("media manifest video set differs")
    verified = []
    for row in rows:
        entry = clips[row["video"]]
        if entry["video_sha256"] != row["sha256"]:
            raise ValueError("media manifest video SHA differs")
        _, hashes = decode_selected(input_dir / row["video"])
        if [hashes[str(t)] for t in range(15)] != entry["decoded_rgb_sha256"]:
            raise ValueError(f"decoded pixel SHA differs: {row['video']}")
        verified.append({**row, "decoded_pixel_sha256": hashes})
    return verified


def run(args: argparse.Namespace) -> None:
    input_dir, output = checked_paths(args.input_dir, args.output)
    if args.max_new_tokens != 512:
        raise ValueError("pilot budget fixes max_new_tokens=512")
    if args.limit < 0:
        raise ValueError("limit must be nonnegative")
    rows = inspect_inputs(input_dir)
    if args.limit:
        rows = rows[:args.limit]
    output.parent.mkdir(parents=True, exist_ok=True)
    model_path = args.model_path.resolve()
    header = {
        "kind": "configuration", "utc": datetime.now(timezone.utc).isoformat(),
        "scope": "single_scene_development_pilot", "input_dir": str(input_dir),
        "manifest_sha256": sha256(input_dir / "manifest.jsonl"),
        "media_manifest_sha256": sha256(input_dir / "media_hashes.json"),
        "model_path": str(model_path), "model_config_sha256":
            sha256(model_path / "config.json") if (model_path / "config.json").is_file() else None,
        "frame_seconds": FRAME_SECONDS, "image_size": IMAGE_SIZE,
        "max_new_tokens_per_call": args.max_new_tokens, "attention": args.attention,
        "dry_run": args.dry_run, "limit": args.limit,
    }
    append_jsonl(output, header)
    for row in rows:
        append_jsonl(output, {"kind": "video_input", "video": row["video"],
                              "sha256": row["sha256"],
                              "decoded_pixel_sha256": row["decoded_pixel_sha256"]})
    if args.dry_run:
        return

    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    import torch
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

    if not torch.cuda.is_available() or not (model_path / "config.json").is_file():
        raise RuntimeError("existing CUDA checkpoint required; no download allowed")
    processor = AutoProcessor.from_pretrained(model_path, local_files_only=True)
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        model_path, dtype=torch.bfloat16, attn_implementation=args.attention,
        local_files_only=True).to("cuda").eval()
    for index, row in enumerate(rows):
        video = row["video"]
        try:
            images, hashes = decode_selected(input_dir / video)
            if hashes != row["decoded_pixel_sha256"]:
                raise ValueError("pixels changed after preflight")
        except Exception as exc:
            append_jsonl(output, {"kind": "input_failure", "video": video,
                                  "error": f"{type(exc).__name__}: {exc}"})
            continue
        arms = ("D2", "candidate") if index % 2 == 0 else ("candidate", "D2")
        for arm in arms:
            calls = []
            for pass_number in (1, 2):
                prompt = prompt_for(arm, pass_number, row["instruction"],
                                    prior=calls[0]["raw"] if calls else "")
                try:
                    result = model_call(model, processor, images, prompt, 512)
                    parsed = parse_record(result["raw"])
                    result.update(parsed)
                except Exception as exc:
                    result = {"raw": "", "record": None, "validity": "invalid",
                              "errors": [f"runtime:{type(exc).__name__}: {exc}"],
                              "direction": "invalid"}
                    torch.cuda.empty_cache()
                calls.append(result)
                append_jsonl(output, {"kind": "visual_call", "video": video,
                                      "arm": arm, "pass": pass_number, **result})
            decision = pair_result(arm, calls[0]["raw"], calls[1]["raw"])
            append_jsonl(output, {"kind": "pair_decision", "video": video,
                                  "arm": arm, "direction": decision["direction"],
                                  "reason": decision["reason"]})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--model-path", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--attention", choices=("sdpa", "flash_attention_2"),
                        default="flash_attention_2")
    run(parser.parse_args())


if __name__ == "__main__":
    main()

"""Optional post-seal video-fact probe for existing base VLM checkpoints.

This is NOT a TOPReward or Robometer intermediate output. It tests whether a
separately prompted base VLM can describe relations from the same legal input.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .run_monitor_qwen import (FRAME_SECONDS, IMAGE_SIZE, append_jsonl,
                               decode_selected, model_call, sha256)
from .run_relation_endpoint_pilot import checked_paths, inspect_inputs


PROMPT = """Final goal: {instruction}
Inspect only this preparation video's frames at seconds 0,2,4,6,8,10,12,14.
Describe visible facts, not progress or future success. Identify the goal object,
the most salient other non-goal object (whether moved or not), and the goal region.
For each object, state its relation to the goal region at seconds 0 and 14.
State whether the other object ever left and returned. Judge whether the complete final goal is visibly
met at second 14; name any requirement not visible. Cite seconds 0 and 14.
Return one compact JSON object with keys goal_object, other_object, goal_region,
other_at_0, other_at_14, returned, goal_at_0, goal_at_14,
complete_at_14, missing_visual_evidence, evidence. For other_at_0,
other_at_14, goal_at_0, goal_at_14 use inside/outside/unknown; for returned and
complete_at_14 use true/false/unknown. Use unknown if uncertain.
Do not use scene labels, condition names, simulator state, or continuation.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--model-path", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model-label", required=True)
    parser.add_argument("--attention", choices=("sdpa", "flash_attention_2"),
                        default="flash_attention_2")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    input_dir, output = checked_paths(args.input_dir, args.output)
    rows = inspect_inputs(input_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    append_jsonl(output, {"kind": "configuration", "utc": datetime.now(timezone.utc).isoformat(),
                          "scope": "optional_post_seal_base_vlm_fact_probe",
                          "not_native_semantic_trace": True, "model_label": args.model_label,
                          "model_path": str(args.model_path.resolve()),
                          "manifest_sha256": sha256(input_dir / "manifest.jsonl"),
                          "frame_seconds": FRAME_SECONDS, "image_size": IMAGE_SIZE,
                          "max_new_tokens": 384, "dry_run": args.dry_run,
                          "prompt_template": PROMPT})
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

    model_path = args.model_path.resolve()
    if not torch.cuda.is_available() or not (model_path / "config.json").is_file():
        raise RuntimeError("existing local CUDA model required; no download")
    processor = AutoProcessor.from_pretrained(model_path, local_files_only=True)
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        model_path, dtype=torch.bfloat16, attn_implementation=args.attention,
        local_files_only=True).to("cuda").eval()
    for row in rows:
        images, hashes = decode_selected(input_dir / row["video"])
        if hashes != row["decoded_pixel_sha256"]:
            raise ValueError("decoded pixels changed after preflight")
        prompt = PROMPT.format(instruction=row["instruction"])
        try:
            call = model_call(model, processor, images, prompt, 384)
            # model_call's event-record parser does not apply to this fact schema.
            keep = {key: call.get(key) for key in ("raw", "input_tokens", "output_tokens",
                                                   "elapsed_ms", "peak_vram_bytes", "prompt_sha256")}
            append_jsonl(output, {"kind": "fact_probe", "video": row["video"], **keep})
        except Exception as exc:
            append_jsonl(output, {"kind": "probe_failure", "video": row["video"],
                                  "error": f"{type(exc).__name__}: {exc}"})


if __name__ == "__main__":
    main()

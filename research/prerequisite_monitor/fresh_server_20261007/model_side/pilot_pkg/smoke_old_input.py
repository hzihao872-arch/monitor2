"""One-video old-input format smoke through the unchanged native runner functions."""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone
from pathlib import Path

from .run_monitor_qwen import append_jsonl, sha256
from .run_relation_endpoint_pilot import checked_paths, inspect_inputs
from .run_native_single_scene_pilot import run_robometer, run_topreward


def run(args: argparse.Namespace) -> None:
    input_dir, output = checked_paths(args.input_dir, args.output_dir)
    rows = inspect_inputs(input_dir)
    if not rows:
        raise ValueError("old input format contains no video")
    row = rows[0]
    output.mkdir(parents=True)
    journal = output / "native_calls.jsonl"
    append_jsonl(journal, {"kind": "configuration", "scope": "old_input_format_smoke_one_video",
                           "utc": datetime.now(timezone.utc).isoformat(), "method": args.method,
                           "manifest_sha256": sha256(input_dir / "manifest.jsonl"),
                           "media_manifest_sha256": sha256(input_dir / "media_hashes.json"),
                           "dry_run": args.dry_run})
    append_jsonl(journal, {"kind": "video_input", "video": row["video"], "sha256": row["sha256"],
                           "decoded_pixel_sha256": row["decoded_pixel_sha256"]})
    if args.dry_run:
        return
    if not (args.model_path / "config.json").is_file():
        raise FileNotFoundError("existing checkpoint required")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", WANDB_MODE="disabled")
    if args.method == "TOPReward":
        run_topreward([row], input_dir, output, journal, args.repo.resolve(), args.model_path.resolve())
    else:
        run_robometer([row], input_dir, output, journal, args.repo.resolve(), args.model_path.resolve())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", required=True, choices=("TOPReward", "Robometer"))
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--model-path", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    run(parser.parse_args())


if __name__ == "__main__":
    main()

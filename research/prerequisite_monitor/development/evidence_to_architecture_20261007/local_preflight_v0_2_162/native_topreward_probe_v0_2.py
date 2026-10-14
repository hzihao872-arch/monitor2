"""Call the unchanged official TOPReward Qwen client on altered task text.

This wrapper only validates anonymous RGB inputs and logs native 15-prefix
outputs. It contains no case labels, expected directions, or scene answers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import types
from datetime import datetime, timezone
from pathlib import Path


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def append(path: Path, row: dict) -> None:
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def inputs(path: Path) -> tuple[list[dict], dict]:
    if path.name != "model_input":
        raise ValueError("input directory must be named model_input")
    rows = [json.loads(line) for line in (path / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    media = json.loads((path / "media_hashes.json").read_text(encoding="utf-8"))
    clips = {row["video"]: row for row in media["clips"]}
    if len(rows) != 9 or len(clips) != 9 or {row["video"] for row in rows} != {f"{i:04d}.mp4" for i in range(1, 10)}:
        raise ValueError("expected nine anonymous videos")
    for row in rows:
        if row["video"] not in clips or row["sha256"] != clips[row["video"]]["video_sha256"] or sha(path / row["video"]) != row["sha256"]:
            raise ValueError("source video SHA mismatch")
        if not isinstance(row.get("instruction"), str) or not row["instruction"].strip():
            raise ValueError("missing task text")
    return rows, clips


def decode(path: Path, expected_hashes: list[str]):
    import cv2

    cap = cv2.VideoCapture(str(path))
    frames = []
    try:
        while True:
            okay, frame = cap.read()
            if not okay:
                break
            if frame.shape[:2] != (480, 640) or len(frames) >= 15:
                raise ValueError("decoded frame count or shape mismatch")
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            if hashlib.sha256(rgb.tobytes()).hexdigest() != expected_hashes[len(frames)]:
                raise ValueError("decoded RGB frame SHA mismatch")
            frames.append(rgb)
    finally:
        cap.release()
    if len(frames) != 15:
        raise ValueError("expected 15 decoded frames")
    return frames


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--model-path", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="pilot only; 0 means all nine")
    args = parser.parse_args()
    if args.output_dir.exists() or args.input_dir.resolve() in args.output_dir.resolve().parents:
        raise ValueError("output must be new and outside input")
    rows, clips = inputs(args.input_dir)
    if args.limit < 0 or args.limit > 9:
        parser.error("limit must be 0..9")
    if args.limit:
        rows = rows[:args.limit]
    args.output_dir.mkdir(parents=True)
    journal = args.output_dir / "native_calls.jsonl"
    append(journal, {"kind": "configuration", "utc": datetime.now(timezone.utc).isoformat(),
                     "method": "TOPReward", "dry_run": args.dry_run,
                     "limit": args.limit,
                     "manifest_sha256": sha(args.input_dir / "manifest.jsonl"),
                     "media_manifest_sha256": sha(args.input_dir / "media_hashes.json"),
                     "model_path": str(args.model_path), "repo": str(args.repo),
                     "native_settings": {"num_samples": 15, "reduction": "mean", "fps": 1.0,
                                         "use_video_description": False, "add_chat_template": False}})
    for row in rows:
        append(journal, {"kind": "video_input", "video": row["video"],
                         "video_sha256": row["sha256"],
                         "instruction_sha256": hashlib.sha256(row["instruction"].encode()).hexdigest()})
    if args.dry_run:
        for row in rows:
            decode(args.input_dir / row["video"], clips[row["video"]]["decoded_rgb_sha256"])
        return
    if not (args.repo / "topreward/clients/qwen.py").is_file() or not (args.model_path / "config.json").is_file():
        raise RuntimeError("existing official TOPReward checkout and checkpoint required")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", WANDB_MODE="disabled")
    sys.path.insert(0, str(args.repo))
    package = types.ModuleType("topreward.clients")
    package.__path__ = [str(args.repo / "topreward/clients")]
    sys.modules["topreward.clients"] = package
    from topreward.clients.qwen import QwenClient

    client = QwenClient(model_name=str(args.model_path))
    for row in rows:
        video = row["video"]
        try:
            frames = decode(args.input_dir / video, clips[video]["decoded_rgb_sha256"])
            prefix_ms, token_counts = [], []
            original = client.compute_instruction_reward

            def observed(*a, **kw):
                start = time.perf_counter()
                result = original(*a, **kw)
                prefix_ms.append(round((time.perf_counter() - start) * 1000))
                token_counts.append(int(result.token_count))
                return result

            client.compute_instruction_reward = observed
            started = time.perf_counter()
            try:
                result = client.compute_instruction_rewards_for_prefixes(
                    frames=frames, instruction=row["instruction"], num_samples=15,
                    reduction="mean", fps=1.0, use_video_description=False,
                    add_chat_template=False)
            finally:
                client.compute_instruction_reward = original
            if result.prefix_lengths != list(range(1, 16)) or len(token_counts) != 15:
                raise ValueError("unexpected native prefix output")
            payload = {"kind": "native_result", "method": "TOPReward", "video": video,
                       "instruction": row["instruction"], "video_sha256": row["sha256"],
                       "prefix_lengths": result.prefix_lengths, "prefix_rewards": result.prefix_rewards,
                       "normalized_prefix_rewards_diagnostic_only": result.normalized_prefix_rewards,
                       "prefix_token_counts": token_counts, "prefix_elapsed_ms": prefix_ms,
                       "elapsed_ms": round((time.perf_counter() - started) * 1000),
                       "reduction": "mean", "fps": 1.0,
                       "use_video_description": False, "add_chat_template": False}
            file = args.output_dir / f"{Path(video).stem}.json"
            file.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            append(journal, {**payload, "result_sha256": sha(file)})
        except Exception as exc:
            append(journal, {"kind": "native_failure", "method": "TOPReward", "video": video,
                             "error": f"{type(exc).__name__}: {exc}"})
    print(json.dumps({"output_dir": str(args.output_dir), "videos": len(rows)}))


if __name__ == "__main__":
    main()

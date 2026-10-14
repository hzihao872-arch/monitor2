"""Direct goal-conditioned preparation benefit question on frozen anonymous videos."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

SECONDS = (0, 2, 4, 6, 7, 8, 10, 12, 14)
SIZE = (512, 384)
LABELS = ("beneficial", "harmful", "unchanged", "completed", "unknown")
MAX_NEW_TOKENS = 384
DIRECT_PROMPT = (
    "Final goal: {goal}\n"
    "This preparation video runs from second 0 to second 14. Compare the visible scene at "
    "second 0 and second 14. Did the visible changes make it possible to complete the final "
    "goal when it was previously blocked (beneficial), make a previously possible goal "
    "blocked (harmful), leave that possibility unchanged (unchanged), or already complete "
    "the goal (completed)? Use unknown if the video does not show enough. A goal object "
    "that has not yet been moved may still be possible to place after the video. At each "
    "point, consider any legal route for continuing with the goal object while leaving "
    "other scene structures in their visible state at that point. A temporary improvement "
    "that is undone by second 14 is unchanged overall. Identify the visible relation or "
    "change that determines your answer; consider an alternative route. Return one JSON "
    "object with keys label (beneficial, harmful, unchanged, completed, or unknown), "
    "reason (short string), evidence_seconds (list of supplied seconds), and uncertainty "
    "(short string)."
)


def prompt_for(goal: str) -> str:
    return DIRECT_PROMPT.format(goal=goal)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def append(path: Path, row: dict) -> None:
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
        stream.flush()


def input_rows(path: Path) -> tuple[list[dict], dict]:
    if path.name != "model_input":
        raise ValueError("only frozen model_input directory is allowed")
    rows = [json.loads(line) for line in (path / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    media = json.loads((path / "media_hashes.json").read_text(encoding="utf-8"))
    clips = {entry["video"]: entry for entry in media["clips"]}
    expected = {f"{index:04}.mp4" for index in range(1, 10)}
    if len(rows) != 9 or len(clips) != 9 or {row["video"] for row in rows} != expected:
        raise ValueError("nine unique anonymous videos required")
    goal = (path / "instruction.txt").read_text(encoding="utf-8").strip()
    for row in rows:
        name = row["video"]
        if row["instruction"] != goal or sha256(path / name) != row["sha256"] or clips[name]["video_sha256"] != row["sha256"]:
            raise ValueError("frozen instruction or video SHA differs: " + name)
    return rows, clips


def sample_frames(path: Path, expected_hashes: list[str]):
    import cv2
    from PIL import Image

    capture = cv2.VideoCapture(str(path))
    images, source_hashes, resized_hashes = [], [], []
    try:
        index = 0
        while True:
            valid, frame = capture.read()
            if not valid:
                break
            if frame.shape[:2] != (480, 640) or index >= 15:
                raise ValueError("frozen frame dimensions or count differ")
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            digest = hashlib.sha256(rgb.tobytes()).hexdigest()
            if digest != expected_hashes[index]:
                raise ValueError("frozen decoded RGB frame SHA differs")
            if index in SECONDS:
                image = Image.fromarray(rgb).resize(SIZE, Image.Resampling.BICUBIC)
                images.append(image)
                source_hashes.append(digest)
                resized_hashes.append(hashlib.sha256(image.tobytes()).hexdigest())
            index += 1
    finally:
        capture.release()
    if index != 15 or len(images) != len(SECONDS):
        raise ValueError("expected 15 decoded frames and nine samples")
    return images, source_hashes, resized_hashes


def parse(raw: str) -> dict:
    try:
        value = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
        if (not isinstance(value, dict) or value.get("label") not in LABELS or
            not isinstance(value.get("reason"), str) or not isinstance(value.get("uncertainty"), str) or
            not isinstance(value.get("evidence_seconds"), list) or
            any(type(t) is not int or t not in SECONDS for t in value["evidence_seconds"])):
            raise ValueError("invalid direct-answer JSON shape")
        return {"parse_status": "valid", "parsed": value}
    except (ValueError, TypeError) as exc:
        return {"parse_status": "invalid", "parse_error": str(exc)}


def run(args: argparse.Namespace) -> None:
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    jobs = []
    for arm, path in (("access_gate", args.access_input), ("support_surface", args.support_input)):
        rows, clips = input_rows(path)
        if args.limit_per_arm:
            rows = rows[:args.limit_per_arm]
        for row in rows:
            images, frame_hashes, resized_hashes = sample_frames(path / row["video"], clips[row["video"]]["decoded_rgb_sha256"])
            jobs.append((arm, row, images, frame_hashes, resized_hashes, prompt_for(row["instruction"])))
    append(args.output, {"kind": "configuration", "utc": datetime.now(timezone.utc).isoformat(),
                         "scope": "P6_direct_Qwen3VL8B_development", "dry_run": args.dry_run,
                         "pilot": args.pilot, "frame_seconds": SECONDS, "resize": SIZE,
                         "max_new_tokens": MAX_NEW_TOKENS,
                         "prompt_template_sha256": hashlib.sha256(DIRECT_PROMPT.encode()).hexdigest(),
                         "model_path": str(args.model_path)})
    for arm, row, images, frame_hashes, resized_hashes, prompt in jobs:
        append(args.output, {"kind": "video_input", "arm": arm, "video": row["video"],
                             "video_sha256": row["sha256"], "frame_seconds": SECONDS,
                             "frame_sha256": frame_hashes, "resized_frame_sha256": resized_hashes,
                             "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()})
    if args.dry_run:
        return
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", WANDB_MODE="disabled")
    import torch
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

    if not torch.cuda.is_available() or not (args.model_path / "config.json").is_file():
        raise RuntimeError("existing CUDA checkpoint required")
    processor = AutoProcessor.from_pretrained(args.model_path, local_files_only=True)
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        args.model_path, dtype=torch.bfloat16, attn_implementation="flash_attention_2",
        local_files_only=True).to("cuda").eval()
    for arm, row, images, frame_hashes, resized_hashes, prompt in jobs:
        content = [{"type": "text", "text": prompt}]
        for second, image in zip(SECONDS, images):
            content.extend(({"type": "text", "text": f"Second {second}:"}, {"type": "image", "image": image}))
        started = time.perf_counter()
        try:
            model_inputs = processor.apply_chat_template([{"role": "user", "content": content}], tokenize=True,
                                                   add_generation_prompt=True, return_dict=True, return_tensors="pt")
            input_tokens = int(model_inputs["input_ids"].shape[-1])
            model_inputs = model_inputs.to("cuda")
            torch.cuda.reset_peak_memory_stats()
            with torch.inference_mode():
                output = model.generate(**model_inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=False)
            completion = output[:, input_tokens:]
            raw = processor.batch_decode(completion, skip_special_tokens=True)[0]
            torch.cuda.synchronize()
            result = {"kind": "model_output", "arm": arm, "video": row["video"], "raw": raw,
                      **parse(raw), "input_tokens": input_tokens,
                      "output_tokens": int(completion.shape[-1]),
                      "elapsed_ms": round((time.perf_counter() - started) * 1000),
                      "peak_vram_bytes": int(torch.cuda.max_memory_allocated())}
        except Exception as exc:
            result = {"kind": "model_failure", "arm": arm, "video": row["video"],
                      "error": f"{type(exc).__name__}: {exc}",
                      "elapsed_ms": round((time.perf_counter() - started) * 1000)}
            torch.cuda.empty_cache()
        append(args.output, result)
        if result["kind"] == "model_failure" and "out of memory" in result["error"].lower():
            raise RuntimeError("P6 OOM; stop diagnostic")
        if args.pilot and (result["kind"] != "model_output" or result["parse_status"] != "valid"):
            raise RuntimeError("P6 pilot invalid; stop diagnostic")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--access-input", required=True, type=Path)
    parser.add_argument("--support-input", required=True, type=Path)
    parser.add_argument("--model-path", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--limit-per-arm", type=int, default=0)
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    run(parser.parse_args())


if __name__ == "__main__":
    main()

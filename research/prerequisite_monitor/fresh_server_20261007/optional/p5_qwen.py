"""Independent targeted visual and future-route development questions; no truth."""

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
MAX_NEW_TOKENS = 384
PROMPTS = {
    "visual": {
        "access_gate": ("Final goal: {goal}\nFocus only on the top entrance of the transparent box. "
                        "At seconds 0, 7/8, and 14, is it fully open for the blue cube, partly open, blocked, or unknown? "
                        "Use only visible lid geometry. Ignore whether the blue cube moved or the goal was completed. "
                        "For state_initial, state_middle, state_final use exactly ready, partial, blocked, or unknown; "
                        "ready means a fully unobstructed top entrance. Return one JSON object with keys "
                        "state_initial, state_middle, state_final, facts (list of short visible observations), "
                        "evidence_seconds (list of supplied seconds), uncertainty (string)."),
        "support_surface": ("Final goal: {goal}\nFocus only on the yellow sliding board under the marked elevated landing. "
                            "At seconds 0, 7/8, and 14, is it fully deployed beneath the landing, partly deployed, "
                            "parked away, or unknown? Use only visible geometry. Ignore whether the blue cube moved "
                            "or the goal was completed. For state_initial, state_middle, state_final use exactly "
                            "ready, partial, blocked, or unknown; ready means fully deployed under the landing, "
                            "blocked means parked away. Return one JSON object with keys state_initial, "
                            "state_middle, state_final, facts (list of short visible observations), "
                            "evidence_seconds (list of supplied seconds), uncertainty (string)."),
    },
    "necessity": {
        arm: ("Final goal: {goal}\nBegin a NEW attempt only AFTER second 14. Ignore whether the blue cube "
              "moved during the recorded video. From the visible state at second 14, the robot may pick up, move "
              "and release the blue cube, but may not move the lid, yellow board, box or landing. Can the final "
              "goal be completed and left stable? Answer yes, no, already_done, or unknown. Give the visible "
              "route or blocker, consider alternative routes, and cite supplied seconds. If visibility is "
              "insufficient, use unknown. Return one JSON object with keys answer, route (short explanation), "
              "evidence_seconds (list of supplied seconds), uncertainty (string).")
        for arm in ("access_gate", "support_surface")
    },
}


def prompt_for(stage: str, arm: str, goal: str) -> str:
    return PROMPTS[stage][arm].format(goal=goal)


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


def inputs(path: Path) -> list[dict]:
    if path.name != "model_input":
        raise ValueError("only model_input is allowed")
    rows = [json.loads(line) for line in (path / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    media = json.loads((path / "media_hashes.json").read_text(encoding="utf-8"))
    clips = {entry["video"]: entry for entry in media["clips"]}
    if len(rows) != 9 or len(clips) != 9 or {row["video"] for row in rows} != {f"{i:04}.mp4" for i in range(1, 10)}:
        raise ValueError("nine anonymous videos required")
    for row in rows:
        if sha256(path / row["video"]) != row["sha256"] or clips[row["video"]]["video_sha256"] != row["sha256"]:
            raise ValueError("video SHA differs")
    return rows


def frames(path: Path, expected: list[str]):
    import cv2
    from PIL import Image

    capture = cv2.VideoCapture(str(path))
    images, hashes, resized_hashes = [], [], []
    try:
        index = 0
        while True:
            okay, frame = capture.read()
            if not okay:
                break
            if frame.shape[:2] != (480, 640):
                raise ValueError("frame dimensions differ")
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            digest = hashlib.sha256(rgb.tobytes()).hexdigest()
            if index >= 15 or digest != expected[index]:
                raise ValueError("decoded RGB frame SHA differs")
            if index in SECONDS:
                image = Image.fromarray(rgb).resize(SIZE, Image.Resampling.BICUBIC)
                images.append(image)
                hashes.append(digest)
                resized_hashes.append(hashlib.sha256(image.tobytes()).hexdigest())
            index += 1
    finally:
        capture.release()
    if index != 15 or len(images) != 9:
        raise ValueError("expected 15 video frames and nine sampled frames")
    return images, hashes, resized_hashes


def parse(raw: str, stage: str) -> dict:
    try:
        value = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
        if not isinstance(value, dict) or not isinstance(value.get("evidence_seconds"), list):
            raise ValueError("JSON shape")
        if not all(isinstance(t, int) and t in SECONDS for t in value["evidence_seconds"]):
            raise ValueError("evidence seconds")
        if stage == "necessity" and value.get("answer") not in ("yes", "no", "already_done", "unknown"):
            raise ValueError("answer enum")
        if stage == "visual":
            if not isinstance(value.get("facts"), list) or any(
                value.get(key) not in ("ready", "partial", "blocked", "unknown")
                for key in ("state_initial", "state_middle", "state_final")
            ):
                raise ValueError("visual state enum or facts list")
        return {"parse_status": "valid", "parsed": value}
    except (ValueError, TypeError) as exc:
        return {"parse_status": "invalid", "parse_error": str(exc)}


def run(args: argparse.Namespace) -> None:
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    jobs = []
    for arm, path in (("access_gate", args.access_input), ("support_surface", args.support_input)):
        rows = inputs(path)
        if args.limit_per_arm:
            rows = rows[:args.limit_per_arm]
        media = json.loads((path / "media_hashes.json").read_text(encoding="utf-8"))
        clip_map = {entry["video"]: entry for entry in media["clips"]}
        for row in rows:
            images, raw_hashes, resized_hashes = frames(path / row["video"], clip_map[row["video"]]["decoded_rgb_sha256"])
            prompt = prompt_for(args.stage, arm, row["instruction"])
            jobs.append((arm, row, images, raw_hashes, resized_hashes, prompt))
    append(args.output, {"kind": "configuration", "utc": datetime.now(timezone.utc).isoformat(),
                         "stage": args.stage, "scope": "P5_targeted_Qwen3VL8B_diagnostic", "dry_run": args.dry_run,
                         "pilot": args.pilot, "frame_seconds": SECONDS, "resize": SIZE,
                         "max_new_tokens": MAX_NEW_TOKENS, "prompt_template_sha256": hashlib.sha256(json.dumps(PROMPTS[args.stage], sort_keys=True).encode()).hexdigest(),
                         "model_path": str(args.model_path)})
    for arm, row, images, raw_hashes, resized_hashes, prompt in jobs:
        append(args.output, {"kind": "video_input", "arm": arm, "video": row["video"],
                             "video_sha256": row["sha256"], "frame_seconds": SECONDS,
                             "frame_sha256": raw_hashes, "resized_frame_sha256": resized_hashes,
                             "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()})
    if args.dry_run:
        return
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", WANDB_MODE="disabled")
    import torch
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

    if not torch.cuda.is_available() or not (args.model_path / "config.json").is_file():
        raise RuntimeError("existing local CUDA checkpoint required")
    processor = AutoProcessor.from_pretrained(args.model_path, local_files_only=True)
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        args.model_path, dtype=torch.bfloat16, attn_implementation="flash_attention_2",
        local_files_only=True).to("cuda").eval()
    for arm, row, images, raw_hashes, resized_hashes, prompt in jobs:
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
                      **parse(raw, args.stage), "input_tokens": input_tokens,
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
            raise RuntimeError("P1 OOM; stop this diagnostic")
        if args.pilot and (result["kind"] != "model_output" or result["parse_status"] != "valid"):
            raise RuntimeError("P1 pilot failed; stop this diagnostic")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--access-input", required=True, type=Path)
    parser.add_argument("--support-input", required=True, type=Path)
    parser.add_argument("--model-path", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--stage", required=True, choices=tuple(PROMPTS))
    parser.add_argument("--limit-per-arm", type=int, default=0)
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    run(parser.parse_args())


if __name__ == "__main__":
    main()

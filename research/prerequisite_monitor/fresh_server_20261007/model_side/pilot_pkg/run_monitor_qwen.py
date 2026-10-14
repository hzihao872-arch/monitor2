"""Offline D/P/F/H probe with a locally present Qwen3-VL checkpoint.

The runner reads only a numbered model_input directory and a checkpoint. It
does not import or open simulation truth, continuation videos, old scores, or
condition mappings. Each model call is flushed to JSONL before the next call.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from .monitor_contract import combine_hybrid, hybrid_progress, parse_and_validate, render_progress, unknown_progress


FRAME_SECONDS = (0, 2, 4, 6, 8, 10, 12, 14)
IMAGE_SIZE = (512, 384)
MANIFEST_FIELDS = {"video", "instruction", "sha256", "fps", "frame_indices_from_30fps"}

COMMON = """You are reviewing an offline preparation video for a fixed tabletop robot task.
The only task information is the final goal: {instruction}
Use only the supplied frames from this video. Do not claim to have seen a
continuation, a simulator state, or an exact future success probability.
"Satisfied" means a visible condition needed for the final goal appears to
hold, not merely that an object moved. Cite only supplied frame seconds.
Set goal_before_complete from the first frame and goal_observed_complete from
the last frame. Use "true" only when the final goal fully visibly achieved its
described end state at that time. If a required end-state relation is visibly
false, use "false"; do not mark a preparatory condition as goal completion.
Keep goal completion separate from the chosen prerequisite relation.
For goal_before_complete, goal_observed_complete, before_satisfied and
after_satisfied, write exactly "true", "false", or "unknown".
Never put descriptions in these enum fields; put explanations in relation or evidence.
If the view cannot resolve object identity, occupancy, or an alternative route,
use "unknown" and say what is missing.
Return exactly one JSON object, no markdown and no per-frame number list.
Keep it compact: cite exactly two evidence entries, one before and one after
the event interval; each supports value must be one short string, not a list.
Each evidence entry MUST be a JSON object, never a string. Use an inspected
second (0,2,4,6,8,10,12,14) as an integer. For an interval spanning the video,
cite second 0 and second 14. Write a visible image region and what it supports.
The alternative_route and disconfirming_observation fields MUST be nonempty
strings; write "unknown" or "none visible" if appropriate, never null.
The comparison MUST agree with before_satisfied and after_satisfied:
false->true is better, true->false is worse, and equal values are same.
If either satisfaction value is unknown, comparison MUST be unknown.
Use no extra keys and keep every free-text value below 20 words.
Required keys: goal_before_complete and goal_observed_complete
(true/false/unknown strings for the first and last frames), relation
(one concrete goal-relevant visible condition), before_satisfied and
after_satisfied (true/false/unknown strings), comparison
(better/same/worse/unknown string), event_interval_s (two integer seconds 0..14),
evidence (list of objects with second, region, supports), alternative_route,
disconfirming_observation, uncertainty_reason (text or null).
Exact output shape (replace the example values with observations from this video):
{{"goal_before_complete":"false","goal_observed_complete":"false",
"relation":"access to target area","before_satisfied":"false",
"after_satisfied":"true","comparison":"better","event_interval_s":[0,14],
"evidence":[{{"second":0,"region":"target area","supports":"access visibly blocked"}},
{{"second":14,"region":"target area","supports":"access visibly clear"}}],
"alternative_route":"unknown","disconfirming_observation":"none visible",
"uncertainty_reason":null}}
"""
TASKS = {
    "D": "Directly assess whether the observed action made progress toward the final goal, had no supported effect, or hindered it. Fill the event record with visible before/after evidence and any uncertainty.",
    "P": "Convert the final goal into physical feasibility checks for a single arm: grasp access at the source, transfer clearance, and usable placement space at the destination. Identify what object or clearance actually changed. Ground the relation at the changed object's location: if it was inside or above the destination, assess destination usability; if it was at the source, assess grasp access; assess a transfer-path block only if the video shows the object crossing that path. An unnamed object can matter physically. Compare this one relation at the first and last frame even if the final goal remains incomplete. Do not substitute the unchanged final goal relation. If geometry is unclear, report unknown.",
    "F": "Imagine attempting the final goal immediately from the first frame and then from the last frame, holding other visible conditions fixed. First identify the changed object's location. If it was inside or above the destination, test usable placement space there; if it was at the source, test grasp access; infer transfer-path obstruction only from visible path geometry. An unnamed object can matter physically. State the most decisive changed condition in relation, not the unchanged final goal relation. Try to disprove improvement with a visible alternative route or a blocker that remains. If feasibility cannot be resolved, use unknown and name missing evidence.",
    "D2_review": "Review the previous direct event record below against the same supplied frames. Correct any visual or logical mistake; preserve uncertainty where evidence is insufficient. Return the same event schema. Previous record (untrusted draft, not extra visual evidence):\n{prior}",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def collect_inputs(input_dir: Path) -> list[dict]:
    input_dir = input_dir.resolve()
    if input_dir.name != "model_input":
        raise ValueError("input directory must be named model_input")
    manifest = input_dir / "manifest.jsonl"
    if not manifest.is_file():
        raise FileNotFoundError(manifest)
    rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError("empty manifest")
    seen = set()
    for row in rows:
        extra = set(row) - MANIFEST_FIELDS
        if extra:
            raise ValueError("unexpected manifest fields: " + ",".join(sorted(extra)))
        if set(row) != MANIFEST_FIELDS:
            raise ValueError("missing manifest fields")
        video = row["video"]
        if not isinstance(video, str) or not re.fullmatch(r"\d{4}\.mp4", video):
            raise ValueError("video name must be four digits .mp4")
        if video in seen:
            raise ValueError("duplicate video in manifest")
        seen.add(video)
        if not isinstance(row["instruction"], str) or not row["instruction"].strip():
            raise ValueError("missing goal instruction")
        if row["fps"] != 1 or row["frame_indices_from_30fps"] != list(range(0, 450, 30)):
            raise ValueError("unexpected frame sampling protocol")
        path = input_dir / video
        if not path.is_file():
            raise FileNotFoundError(path)
        if sha256(path) != row["sha256"]:
            raise ValueError(f"sha256 mismatch for {video}")
    if {path.name for path in input_dir.glob("*.mp4")} != seen:
        raise ValueError("unmanifested or missing mp4")
    return rows


def decode_selected(path: Path):
    import cv2
    from PIL import Image

    capture = cv2.VideoCapture(str(path))
    frames = []
    try:
        while True:
            okay, frame = capture.read()
            if not okay:
                break
            if frame.shape[:2] != (480, 640):
                raise ValueError(f"bad decoded frame dimensions: {frame.shape}")
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    finally:
        capture.release()
    if len(frames) != 15:
        raise ValueError(f"expected 15 decoded frames, got {len(frames)}")
    images = [Image.fromarray(frames[t]).resize(IMAGE_SIZE, Image.Resampling.BICUBIC) for t in FRAME_SECONDS]
    hashes = {str(t): hashlib.sha256(frames[t].tobytes()).hexdigest() for t in range(15)}
    return images, hashes


def prompt_for(method: str, instruction: str, prior: str = "") -> str:
    task = TASKS[method].format(prior=prior)
    return COMMON.format(instruction=instruction) + "\n" + task


def model_call(model, processor, images, prompt: str, max_new_tokens: int) -> dict:
    import torch

    content = [{"type": "text", "text": prompt}]
    for t, image in zip(FRAME_SECONDS, images):
        content.extend(({"type": "text", "text": f"Second {t}:"}, {"type": "image", "image": image}))
    started = time.perf_counter()
    inputs = processor.apply_chat_template([{"role": "user", "content": content}],
                                           tokenize=True, add_generation_prompt=True,
                                           return_dict=True, return_tensors="pt")
    input_tokens = int(inputs["input_ids"].shape[-1])
    inputs = inputs.to("cuda")
    torch.cuda.reset_peak_memory_stats()
    with torch.inference_mode():
        output = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
    completion = output[:, input_tokens:]
    raw = processor.batch_decode(completion, skip_special_tokens=True)[0]
    torch.cuda.synchronize()
    checked = parse_and_validate(raw, set(FRAME_SECONDS))
    return {**checked, "input_tokens": input_tokens, "output_tokens": int(completion.shape[-1]),
            "elapsed_ms": round((time.perf_counter() - started) * 1000),
            "peak_vram_bytes": int(torch.cuda.max_memory_allocated()),
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest()}


def append_jsonl(path: Path, obj: dict):
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(obj, ensure_ascii=False) + "\n")
        stream.flush()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--model-path", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true", help="decode and hash inputs; do not load a model")
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--attention", choices=("sdpa", "flash_attention_2"), default="flash_attention_2")
    parser.add_argument("--limit", type=int, default=0, help="development smoke only; 0 means all")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    input_dir = args.input_dir.resolve()
    if input_dir in args.output.resolve().parents:
        raise ValueError("output must be outside model_input")
    rows = collect_inputs(input_dir)
    if args.limit:
        rows = rows[:args.limit]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    header = {"kind": "configuration", "utc": datetime.now(timezone.utc).isoformat(),
              "input_dir": str(input_dir), "model_path": str(args.model_path.resolve()),
              "frame_seconds": FRAME_SECONDS, "image_size": IMAGE_SIZE,
              "max_new_tokens_per_call": args.max_new_tokens, "attention": args.attention,
              "dry_run": args.dry_run, "prompt_templates": {"common": COMMON, **TASKS}}
    append_jsonl(args.output, header)
    model = processor = None
    if not args.dry_run:
        import torch
        from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is required for model inference")
        model_path = args.model_path.resolve()
        if not (model_path / "config.json").is_file():
            raise FileNotFoundError(model_path / "config.json")
        processor = AutoProcessor.from_pretrained(model_path, local_files_only=True)
        model = Qwen3VLForConditionalGeneration.from_pretrained(
            model_path, dtype=torch.bfloat16, attn_implementation=args.attention,
            local_files_only=True).to("cuda").eval()
    for row in rows:
        video = row["video"]
        try:
            images, hashes = decode_selected(input_dir / video)
        except Exception as exc:
            append_jsonl(args.output, {"kind": "input_failure", "video": video,
                                       "error": f"{type(exc).__name__}: {exc}"})
            continue
        append_jsonl(args.output, {"kind": "video_input", "video": video, "sha256": row["sha256"],
                                   "instruction": row["instruction"], "decoded_pixel_sha256": hashes})
        if args.dry_run:
            continue
        calls = {}
        for method in ("D", "P", "F", "D2_review"):
            prompt = prompt_for(method, row["instruction"], calls.get("D", {}).get("raw", ""))
            try:
                call = model_call(model, processor, images, prompt, args.max_new_tokens)
            except Exception as exc:
                call = {"validity": "invalid", "errors": [f"runtime:{type(exc).__name__}: {exc}"],
                        "record": None, "raw": ""}
                import torch
                torch.cuda.empty_cache()
            calls[method] = call
            append_jsonl(args.output, {"kind": "model_call", "video": video, "method": method, **call})
        hybrid = combine_hybrid(calls["P"], calls["F"])
        append_jsonl(args.output, {"kind": "hybrid", "video": video, **hybrid})
        h_points = hybrid_progress(hybrid)
        append_jsonl(args.output, {"kind": "progress", "video": video,
                                   "method": "H0", "requires_evidence_audit": True,
                                   "status": "provisional" if "progress_record" in hybrid else "abstain",
                                   "points": h_points})
        for method, call in calls.items():
            if call["validity"] == "valid":
                append_jsonl(args.output, {"kind": "progress", "video": video, "method": method,
                                           "status": "provisional", "requires_evidence_audit": True,
                                           "points": render_progress(call["record"])})
            else:
                append_jsonl(args.output, {"kind": "progress", "video": video, "method": method,
                                           "status": "invalid", "requires_evidence_audit": True,
                                           "points": unknown_progress()})
    print(json.dumps({"output": str(args.output.resolve()), "videos": len(rows), "dry_run": args.dry_run}))


if __name__ == "__main__":
    main()

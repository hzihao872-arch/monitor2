"""Small, label-isolated D/P/F/H interface diagnostic on numbered input videos.

Reads only the requested video and fixed goal. Never imports the simulation oracle,
condition mapping, later continuation videos, or prior model scores. Outputs raw
responses before any truth-side analysis. This is a five-frame 2B development
probe, not a blinded method evaluation or an ARS implementation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration


GOAL = "Put the blue cube in the green tray."
FRAME_IDS = (0, 3, 6, 9, 14)
IMAGE_SIZE = (256, 256)
STATUSES = {"supported_positive", "supported_zero", "supported_negative", "uncertain"}
SCHEMA = (
    'Return one compact JSON object with keys: "status" (supported_positive, '
    'supported_zero, supported_negative, or uncertain), "before" and "after" '
    '(true, false, or unknown as strings), "candidate_prerequisite" (short text), '
    '"evidence_frames" (list of inspected second indices), "alternative_explanation" '
    '(short text), "uncertainty_reason" (short text or null), and "progress" '
    '(15 numbers or nulls for seconds 0 through 14, relative progress 0 to 100). '
    'Use null progress where the scene does not support a value. No markdown.'
)
BASE = (
    f'Final goal: {GOAL}\nOnly the five labeled frames from this preparation video are available. '
    'Do not assume you saw any later success or physical counterfactual. '
    'If a decisive relation or route is hidden, say uncertain. Cite only supplied seconds. '
)
PROMPTS = {
    "D": BASE + "Directly judge task progress and whether the observed action helped, did nothing, or hindered the final goal. " + SCHEMA,
    "P": BASE + "First identify one goal-relevant visible prerequisite, if any. Check whether its relation is satisfied before and after the action from the frames. Credit only a verified relation change. " + SCHEMA,
    "F": BASE + "Compare how feasible it appears to continue the final goal from before versus after this action. Challenge your own claim: could another route achieve the goal before, or might the apparent move still leave a blocker? Do not predict an exact success probability. " + SCHEMA,
}


def decode_video(path: Path):
    capture = cv2.VideoCapture(str(path))
    frames = []
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    finally:
        capture.release()
    if len(frames) != 15:
        raise ValueError(f"expected 15 decoded frames, got {len(frames)}")
    selected = [Image.fromarray(frames[i]).resize(IMAGE_SIZE, Image.Resampling.BICUBIC) for i in FRAME_IDS]
    hashes = [hashlib.sha256(frames[i].tobytes()).hexdigest() for i in FRAME_IDS]
    return selected, hashes


def file_sha256(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_response(raw: str):
    try:
        left, right = raw.index("{"), raw.rindex("}") + 1
        obj = json.loads(raw[left:right])
        if obj.get("status") not in STATUSES:
            raise ValueError("invalid status")
        if obj.get("before") not in ("true", "false", "unknown") or obj.get("after") not in ("true", "false", "unknown"):
            raise ValueError("invalid before/after")
        evid = obj.get("evidence_frames")
        if not isinstance(evid, list) or not all(isinstance(x, int) and x in FRAME_IDS for x in evid):
            raise ValueError("invalid evidence_frames")
        prog = obj.get("progress")
        if not isinstance(prog, list) or len(prog) != 15 or not all(x is None or (isinstance(x, (float, int)) and 0 <= x <= 100) for x in prog):
            raise ValueError("invalid progress")
        return obj, None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def call(model, processor, images, prompt, max_new_tokens):
    content = [{"type": "text", "text": prompt}]
    for second, image in zip(FRAME_IDS, images):
        content.extend([{"type": "text", "text": f"Second {second}:"}, {"type": "image", "image": image}])
    t0 = time.perf_counter()
    inputs = processor.apply_chat_template([{"role": "user", "content": content}], tokenize=True, add_generation_prompt=True, return_dict=True, return_tensors="pt")
    n_input = int(inputs["input_ids"].shape[-1])
    inputs = inputs.to("cuda")
    torch.cuda.reset_peak_memory_stats()
    with torch.inference_mode():
        generated = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
    output_ids = generated[:, n_input:]
    raw = processor.batch_decode(output_ids, skip_special_tokens=True)[0]
    torch.cuda.synchronize()
    parsed, error = parse_response(raw)
    return {"raw": raw, "parsed": parsed, "parse_error": error, "input_tokens": n_input,
            "output_tokens": int(output_ids.shape[-1]), "elapsed_ms": round((time.perf_counter() - t0) * 1000),
            "peak_vram_bytes": int(torch.cuda.max_memory_allocated())}


def combine_h(p, f):
    a, b = p.get("parsed"), f.get("parsed")
    if a is None or b is None:
        return {"status": "invalid", "reason": "P or F failed parsing"}
    if a["status"] != b["status"] or a["status"] == "uncertain":
        return {"status": "uncertain", "reason": "P/F conflict or uncertain", "progress": [None] * 15}
    progress = [(x + y) / 2 if x is not None and y is not None else None for x, y in zip(a["progress"], b["progress"])]
    return {"status": a["status"], "reason": "P/F agreement", "progress": progress,
            "evidence_frames": sorted(set(a["evidence_frames"] + b["evidence_frames"]))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--videos", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, default=Path(".models/qwen3-vl-2b-instruct"))
    parser.add_argument("--max-new-tokens", type=int, default=360)
    parser.add_argument("--frame-ids", default="0,3,6,9,14", help="comma-separated decoded second indices; default reproduces first smoke")
    parser.add_argument("--image-size", default="256x256", help="resize width x height; default reproduces first smoke")
    args = parser.parse_args()
    global FRAME_IDS, IMAGE_SIZE
    FRAME_IDS = tuple(int(x) for x in args.frame_ids.split(","))
    if not FRAME_IDS or len(set(FRAME_IDS)) != len(FRAME_IDS) or any(x < 0 or x > 14 for x in FRAME_IDS):
        raise ValueError("frame ids must be unique integers from 0 to 14")
    IMAGE_SIZE = tuple(int(x) for x in args.image_size.lower().split("x"))
    if len(IMAGE_SIZE) != 2 or min(IMAGE_SIZE) < 32:
        raise ValueError("image size must be WIDTHxHEIGHT, both >=32")
    prompt_variants = {k: v.replace("five labeled frames", f"{len(FRAME_IDS)} labeled frames") for k, v in PROMPTS.items()}
    review_prompt = (BASE + "Review this direct judgment for visual mistakes; correct it only with visible frame evidence. Prior answer: {prior}\n" + SCHEMA).replace("five labeled frames", f"{len(FRAME_IDS)} labeled frames")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    model_path = args.model_dir.resolve()
    processor = AutoProcessor.from_pretrained(model_path, local_files_only=True)
    model = Qwen3VLForConditionalGeneration.from_pretrained(model_path, dtype=torch.bfloat16,
                                                             attn_implementation="sdpa", local_files_only=True).to("cuda").eval()
    header = {"kind": "configuration", "utc": datetime.now(timezone.utc).isoformat(), "model_dir": str(model_path),
              "model_sha256": file_sha256(model_path / "model.safetensors"),
              "python": platform.python_version(), "torch": torch.__version__, "transformers": __import__("transformers").__version__,
              "gpu": torch.cuda.get_device_name(0), "frame_ids": FRAME_IDS, "size": IMAGE_SIZE,
              "max_new_tokens": args.max_new_tokens, "goal": GOAL, "prompts": prompt_variants,
              "review_prompt": review_prompt}
    with args.output.open("a", encoding="utf-8") as sink:
        sink.write(json.dumps(header, ensure_ascii=False) + "\n"); sink.flush()
        for video in args.videos:
            item = {"kind": "video", "path": str(video.resolve()), "sha256": file_sha256(video),
                    "utc": datetime.now(timezone.utc).isoformat()}
            try:
                images, hashes = decode_video(video)
                item["decoded_pixel_hashes"] = hashes
                for method in ("D", "P", "F"):
                    try:
                        item[method] = call(model, processor, images, prompt_variants[method], args.max_new_tokens)
                    except Exception as exc:
                        item[method] = {"error": f"{type(exc).__name__}: {exc}"}
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()
                prior = item["D"].get("raw", "")
                try:
                    item["D2_review"] = call(model, processor, images, header["review_prompt"].format(prior=prior), args.max_new_tokens)
                except Exception as exc:
                    item["D2_review"] = {"error": f"{type(exc).__name__}: {exc}"}
                item["H"] = combine_h(item["P"], item["F"])
            except Exception as exc:
                item["video_error"] = f"{type(exc).__name__}: {exc}"
            sink.write(json.dumps(item, ensure_ascii=False) + "\n"); sink.flush()
            print(json.dumps({"video": video.name, "statuses": {k: item.get(k, {}).get("parsed", {}).get("status") if isinstance(item.get(k, {}).get("parsed"), dict) else item.get(k, {}).get("status", "invalid") for k in ("D", "P", "F", "D2_review", "H")}, "video_error": item.get("video_error")}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

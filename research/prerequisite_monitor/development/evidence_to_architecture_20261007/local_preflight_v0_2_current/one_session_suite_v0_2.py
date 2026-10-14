"""Frozen development comparison runner. Model side sees goal + anonymous RGB only.

No labels, simulator state, previous methods, or expected answers are imported.
Dry run decodes every input and writes the exact prompts and frame hashes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import time
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

from monitor_contract_v0 import evaluate


SUITE_VERSION = "0.2.0-preflight"
SECONDS = (0, 2, 4, 6, 7, 8, 10, 12, 14)
SIZE = (512, 384)
MAX_NEW_TOKENS = 896
STAGES = ("D1", "T1", "P1", "TP1", "D2", "TP2", "D3", "F3")
PRIOR = {"D2": "D1", "TP2": "TP1", "D3": "D2"}

COMMON = """Final goal: {goal}
You see nine labeled frames from one 0–14 second preparation video. Judge the visible state at the start, middle, and end. The goal object can remain unmoved while a necessary preparation improves. Completion of the final goal is separate from whether it can be continued. A temporary improvement undone by the end earns no final preparation credit. Consider a legal alternative route and residual blockers; if the single view cannot decide, say unknown. Do not assume a particular object, color, mechanism, or condition from this instruction. Use only visible frames and the final goal.
Return exactly one valid JSON object, without markdown. Required fields are:
- spec_version: the string "0.1.1"; mid_second: the integer 7 or the integer 8.
- goal_done: object with t0, t_mid, t14; each is one string chosen from true, false, unknown.
- candidate_relation: object with entity, region, predicate (short strings, or JSON null when absent), satisfied (t0, t_mid, t14, each true/false/unknown), goal_relevance (supported/refuted/unknown), alternative_route (t0 and t14, each supported/refuted/unknown), and alternative_route_reason (short string).
- continuation: object with t0, t_mid, t14; each possible/blocked/unknown.
- evidence: array of exactly three objects, each with integer second, region string, claim string. Cite second 0, the chosen mid_second, and second 14. Write only visible facts, not imagined future outcomes.
- decision_reason: short string. uncertainty_reason: JSON null or a specific missing-evidence string. direction: one of beneficial, unchanged, harmful, completed, unknown.
Use one enum word per value, never a slash-separated list. If frame 8 shows a transient more clearly than frame 7, set mid_second to 8 and cite second 8. Otherwise use integer 7 in both places. Do not write "7 or 8" as a value. Never invent a fact to fill a field. If a route or relevant relation cannot be established, use unknown with a reason. A direction must agree with the state fields.
"""

TASKS = {
    "D1": "Make the overall goal-conditioned judgment directly, then expose the visible evidence and route assessment that supports it. Do not start by inventing a prerequisite.",
    "T1": "First derive one candidate prerequisite from the final goal and the video itself. Challenge whether it is truly relevant and visually supported before judging progress. Do not treat the proposed relation as given truth.",
    "P1": "First record one goal-relevant visible relation at start, middle, and end, including a possible reversal. Bind the entity and region to the actual image. Then assess continuation and direction. Do not infer a route solely from motion.",
    "TP1": "Jointly propose a goal-relevant prerequisite and verify its visible start, middle, and end states. Check completion separately, test a legal alternative route or remaining blocker, then derive the net direction. Reject your own proposed relation if the frames do not support it.",
    "D2": "Independently review your previous direct answer below against the frames. Identify a possible visible counterexample or alternative route, correct any error, and return the same JSON schema. Previous answer is a draft, not new evidence:\n{prior}",
    "TP2": "Review your previous proposed relation and temporal evidence below against the frames. Try to falsify the entity binding, endpoint states, goal relevance, and legal continuation. Correct the full JSON; preserve unknown if needed. Previous answer is a draft, not new evidence:\n{prior}",
    "D3": "Make a final independent check of the previous direct review below. Look for a mistaken completion call, an alternative route, and a temporary reversal. Correct the full JSON. Previous answer is a draft, not new evidence:\n{prior}",
    "F3": "Assess legal continuation independently at the first and last frames while holding all other visible scene structures fixed. Seek a route that avoids the changed relation and a blocker that persists after it changes. Record the decisive visible relation, even if the answer is unknown. Do not assume the goal can be achieved merely because something moved. Return the full JSON schema.",
}


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def prompt_for(stage: str, goal: str, prior: str = "") -> str:
    if stage not in STAGES:
        raise ValueError(stage)
    return COMMON.format(goal=goal) + "\nSpecific task: " + TASKS[stage].format(prior=prior)


def read_input(path: Path) -> tuple[list[dict], dict]:
    if path.name != "model_input":
        raise ValueError("input directory must be named model_input")
    names = {item.name for item in path.iterdir() if item.is_file()}
    expected = {f"{i:04d}.mp4" for i in range(1, 10)} | {
        "instruction.txt", "manifest.jsonl", "media_hashes.json"}
    if names != expected:
        raise ValueError("model_input files differ")
    goal = (path / "instruction.txt").read_text(encoding="utf-8").strip()
    rows = [json.loads(line) for line in (path / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    media = json.loads((path / "media_hashes.json").read_text(encoding="utf-8"))
    clips = {row["video"]: row for row in media["clips"]}
    if len(rows) != 9 or len(clips) != 9 or {row["video"] for row in rows} != {f"{i:04d}.mp4" for i in range(1, 10)}:
        raise ValueError("expected nine anonymous videos")
    for row in rows:
        video = row["video"]
        if row["instruction"] != goal or row["sha256"] != clips[video]["video_sha256"] or sha_file(path / video) != row["sha256"]:
            raise ValueError("input video or goal hash mismatch")
    return rows, clips


def decode(path: Path, expected_hashes: list[str]):
    import cv2
    from PIL import Image

    cap = cv2.VideoCapture(str(path))
    images, source_hashes, resized_hashes = [], [], []
    index = 0
    try:
        while True:
            okay, frame = cap.read()
            if not okay:
                break
            if index >= 15 or frame.shape[:2] != (480, 640):
                raise ValueError("decoded frame count or shape differs")
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            digest = sha_bytes(rgb.tobytes())
            if digest != expected_hashes[index]:
                raise ValueError("decoded RGB hash mismatch")
            if index in SECONDS:
                image = Image.fromarray(rgb).resize(SIZE, Image.Resampling.BICUBIC)
                images.append(image)
                source_hashes.append(digest)
                resized_hashes.append(sha_bytes(image.tobytes()))
            index += 1
    finally:
        cap.release()
    if index != 15 or len(images) != len(SECONDS):
        raise ValueError("expected 15 decoded and nine selected frames")
    return images, source_hashes, resized_hashes


def append(path: Path, record: dict) -> None:
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def existing_records(path: Path, config_hash: str) -> dict:
    if not path.exists():
        return {}
    lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines or lines[0].get("kind") != "configuration" or lines[0].get("configuration_sha256") != config_hash:
        raise ValueError("resume configuration differs")
    out = {}
    for row in lines[1:]:
        if row.get("kind") in ("model_output", "model_failure", "dry_prompt"):
            key = (row["group"], row["video"], row["stage"])
            if key in out:
                raise ValueError("duplicate completed call")
            out[key] = row
    return out


def load_model(model_path: Path, attention: str):
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", WANDB_MODE="disabled")
    import torch
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

    if not torch.cuda.is_available() or not (model_path / "config.json").is_file():
        raise RuntimeError("existing local CUDA checkpoint required")
    processor = AutoProcessor.from_pretrained(model_path, local_files_only=True)
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        model_path, dtype=torch.bfloat16, attn_implementation=attention,
        local_files_only=True).to("cuda").eval()
    return model, processor


def package_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def model_call(model, processor, images, prompt: str) -> dict:
    import torch

    content = [{"type": "text", "text": prompt}]
    for second, image in zip(SECONDS, images):
        content.extend(({"type": "text", "text": f"Second {second}:"},
                        {"type": "image", "image": image}))
    start = time.perf_counter()
    inputs = processor.apply_chat_template(
        [{"role": "user", "content": content}], tokenize=True,
        add_generation_prompt=True, return_dict=True, return_tensors="pt")
    input_tokens = int(inputs["input_ids"].shape[-1])
    inputs = inputs.to("cuda")
    torch.cuda.reset_peak_memory_stats()
    with torch.inference_mode():
        output = model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=False)
    completion = output[:, input_tokens:]
    raw = processor.batch_decode(completion, skip_special_tokens=True)[0]
    torch.cuda.synchronize()
    result = evaluate(raw, list(SECONDS))
    return {"raw": raw, "validation": result, "input_tokens": input_tokens,
            "output_tokens": int(completion.shape[-1]),
            "elapsed_ms": round((time.perf_counter() - start) * 1000),
            "peak_vram_bytes": int(torch.cuda.max_memory_allocated()),
            "hit_output_cap": int(completion.shape[-1]) >= MAX_NEW_TOKENS}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--group-01", required=True, type=Path)
    parser.add_argument("--group-02", required=True, type=Path)
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--attention", choices=("flash_attention_2", "sdpa"), default="flash_attention_2")
    parser.add_argument("--limit-per-group", type=int, default=0)
    args = parser.parse_args()
    if args.output.resolve() in [args.group_01.resolve(), args.group_02.resolve()] or any(
        input_dir.resolve() in args.output.resolve().parents for input_dir in (args.group_01, args.group_02)):
        raise ValueError("output must be outside model_input")
    if not args.dry_run and args.model_path is None:
        parser.error("--model-path is required for inference")
    if args.limit_per_group < 0 or args.limit_per_group > 9:
        parser.error("limit-per-group must be 0..9")

    groups = (("group_01", args.group_01), ("group_02", args.group_02))
    jobs = []
    for group, path in groups:
        rows, clips = read_input(path)
        if args.limit_per_group:
            rows = rows[:args.limit_per_group]
        for row in rows:
            images, frame_hashes, resized_hashes = decode(
                path / row["video"], clips[row["video"]]["decoded_rgb_sha256"])
            jobs.append({"group": group, "row": row, "images": images,
                         "frame_hashes": frame_hashes, "resized_hashes": resized_hashes})
    config = {"suite_version": SUITE_VERSION, "dry_run": args.dry_run,
              "groups": {group: sha_file(path / "manifest.jsonl") for group, path in groups},
              "frame_seconds": SECONDS, "image_size": SIZE, "max_new_tokens": MAX_NEW_TOKENS,
              "stages": STAGES, "prompt_templates_sha256": sha_bytes(json.dumps(
                  {"common": COMMON, "tasks": TASKS}, sort_keys=True).encode()),
              "model_path": str(args.model_path) if args.model_path else None,
              "model_config_sha256": sha_file(args.model_path / "config.json") if args.model_path and
                  (args.model_path / "config.json").is_file() else None,
              "attention": args.attention, "limit_per_group": args.limit_per_group,
              "python_version": platform.python_version(),
              "torch_version": package_version("torch"),
              "transformers_version": package_version("transformers"),
              "opencv_version": package_version("opencv-python")}
    config_hash = sha_bytes(json.dumps(config, sort_keys=True).encode())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    completed = existing_records(args.output, config_hash)
    if not args.output.exists():
        append(args.output, {"kind": "configuration", "utc": datetime.now(timezone.utc).isoformat(),
                             "configuration_sha256": config_hash, **config})
        for job in jobs:
            row = job["row"]
            append(args.output, {"kind": "video_input", "group": job["group"],
                                 "video": row["video"], "video_sha256": row["sha256"],
                                 "frame_seconds": SECONDS, "decoded_frame_sha256": job["frame_hashes"],
                                 "resized_frame_sha256": job["resized_hashes"]})
    model = processor = None
    if not args.dry_run:
        model, processor = load_model(args.model_path, args.attention)
        if not any(row.get("kind") == "runtime_environment" for row in
                   (json.loads(line) for line in args.output.read_text(encoding="utf-8").splitlines() if line.strip())):
            import torch
            append(args.output, {"kind": "runtime_environment", "utc": datetime.now(timezone.utc).isoformat(),
                                 "cuda_version": torch.version.cuda,
                                 "gpu_name": torch.cuda.get_device_name(0),
                                 "gpu_total_memory_bytes": torch.cuda.get_device_properties(0).total_memory})
    for stage in STAGES:
        for job in jobs:
            group, row = job["group"], job["row"]
            video = row["video"]
            key = (group, video, stage)
            if key in completed:
                continue
            prior_name = PRIOR.get(stage)
            prior_record = completed.get((group, video, prior_name)) if prior_name else None
            if prior_name and (not prior_record or prior_record.get("kind") not in
                               (("dry_prompt",) if args.dry_run else ("model_output",))):
                record = {"kind": "model_failure", "group": group, "video": video,
                          "stage": stage, "error": "missing_prior_output"}
                append(args.output, record)
                completed[key] = record
                continue
            prior_text = ("<prior model response supplied at inference>" if args.dry_run else prior_record["raw"]) if prior_record else ""
            prompt = prompt_for(stage, row["instruction"], prior_text)
            base = {"group": group, "video": video, "stage": stage,
                    "prompt_sha256": sha_bytes(prompt.encode("utf-8")),
                    "prior_stage": prior_name,
                    "prior_raw_sha256": sha_bytes(prior_text.encode()) if prior_record else None}
            if args.dry_run:
                record = {"kind": "dry_prompt", **base, "prompt": prompt}
            else:
                try:
                    record = {"kind": "model_output", **base, **model_call(model, processor, job["images"], prompt)}
                except Exception as exc:
                    record = {"kind": "model_failure", **base,
                              "error": f"{type(exc).__name__}: {exc}"}
                    import torch
                    torch.cuda.empty_cache()
            append(args.output, record)
            completed[key] = record
            if record["kind"] == "model_failure" and "out of memory" in record.get("error", "").lower():
                raise RuntimeError("CUDA OOM; stopped after preserving failure")
    print(json.dumps({"output": str(args.output), "jobs": len(jobs),
                      "expected_stage_rows": len(jobs) * len(STAGES), "dry_run": args.dry_run}))


if __name__ == "__main__":
    main()

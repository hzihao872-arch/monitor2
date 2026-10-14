"""Development-only native TOPReward or Robometer PR33 inference on model_input.

The native methods keep their own scales. This wrapper only records their
exposed outputs; it does not claim those outputs reveal object semantics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import types
from datetime import datetime, timezone
from pathlib import Path

from .run_monitor_qwen import append_jsonl, sha256
from .run_relation_endpoint_pilot import checked_paths, inspect_inputs


def run(args: argparse.Namespace) -> None:
    input_dir, out_dir = checked_paths(args.input_dir, args.output_dir)
    rows = inspect_inputs(input_dir)
    out_dir.mkdir(parents=True)
    journal = out_dir / "native_calls.jsonl"
    repo, model_path = args.repo.resolve(), args.model_path.resolve()
    append_jsonl(journal, {
        "kind": "configuration", "utc": datetime.now(timezone.utc).isoformat(),
        "scope": "single_scene_development_pilot", "method": args.method,
        "input_dir": str(input_dir), "manifest_sha256": sha256(input_dir / "manifest.jsonl"),
        "media_manifest_sha256": sha256(input_dir / "media_hashes.json"),
        "repo": str(repo), "model_path": str(model_path), "dry_run": args.dry_run,
    })
    for row in rows:
        append_jsonl(journal, {"kind": "video_input", "video": row["video"],
                               "sha256": row["sha256"],
                               "decoded_pixel_sha256": row["decoded_pixel_sha256"]})
    if args.dry_run:
        return
    if not (model_path / "config.json").is_file():
        raise FileNotFoundError("existing local model config required; no download")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["WANDB_MODE"] = "disabled"
    if args.method == "TOPReward":
        run_topreward(rows, input_dir, out_dir, journal, repo, model_path)
    else:
        run_robometer(rows, input_dir, out_dir, journal, repo, model_path)


def run_topreward(rows, input_dir, out_dir, journal, repo, model_path):
    if not (repo / "topreward/clients/qwen.py").is_file():
        raise FileNotFoundError("existing official TOPReward client required")
    package = types.ModuleType("topreward.clients")
    package.__path__ = [str(repo / "topreward/clients")]
    sys.modules["topreward.clients"] = package
    from topreward.clients.qwen import QwenClient
    import cv2

    client = QwenClient(model_name=str(model_path))
    for row in rows:
        video = row["video"]
        capture = cv2.VideoCapture(str(input_dir / video))
        frames = []
        try:
            while True:
                okay, frame = capture.read()
                if not okay:
                    break
                frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        finally:
            capture.release()
        if len(frames) != 15:
            append_jsonl(journal, {"kind": "native_failure", "video": video,
                                   "error": f"decoded {len(frames)} frames"})
            continue
        actual_hashes = [hashlib.sha256(frame.tobytes()).hexdigest() for frame in frames]
        if actual_hashes != [row["decoded_pixel_sha256"][str(t)] for t in range(15)]:
            append_jsonl(journal, {"kind": "native_failure", "method": "TOPReward",
                                   "video": video, "error": "client decoder pixel hashes differ"})
            continue
        token_counts, prefix_ms = [], []
        original = client.compute_instruction_reward

        def observed(*a, **kw):
            started = time.perf_counter()
            result = original(*a, **kw)
            prefix_ms.append(round((time.perf_counter() - started) * 1000))
            token_counts.append(int(result.token_count))
            return result

        client.compute_instruction_reward = observed
        started = time.perf_counter()
        try:
            result = client.compute_instruction_rewards_for_prefixes(
                frames=frames, instruction=row["instruction"], num_samples=15,
                reduction="mean", fps=1.0, use_video_description=False,
                add_chat_template=False)
            if result.prefix_lengths != list(range(1, 16)) or len(token_counts) != 15:
                raise ValueError("unexpected native prefixes")
            payload = {"kind": "native_result", "method": "TOPReward", "video": video,
                       "instruction": row["instruction"], "video_sha256": row["sha256"],
                       "prefix_lengths": result.prefix_lengths,
                       "prefix_rewards": result.prefix_rewards,
                       "normalized_prefix_rewards_diagnostic_only": result.normalized_prefix_rewards,
                       "prefix_token_counts": token_counts, "prefix_elapsed_ms": prefix_ms,
                       "elapsed_ms": round((time.perf_counter() - started) * 1000),
                       "reduction": "mean", "fps": 1.0,
                       "use_video_description": False, "add_chat_template": False}
            path = out_dir / (Path(video).stem + ".json")
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            append_jsonl(journal, {**payload, "result_sha256": sha256(path)})
        except Exception as exc:
            append_jsonl(journal, {"kind": "native_failure", "method": "TOPReward",
                                   "video": video, "error": f"{type(exc).__name__}: {exc}",
                                   "prefixes_completed": len(token_counts)})
        finally:
            client.compute_instruction_reward = original


def run_robometer(rows, input_dir, out_dir, journal, repo, model_path):
    script = repo / "scripts/example_inference_local.py"
    if not script.is_file():
        raise FileNotFoundError("existing Robometer compatibility script required")
    import numpy as np

    for row in rows:
        video = row["video"]
        probe_code = (
            "import hashlib,importlib.util,json,sys;"
            "s=importlib.util.spec_from_file_location('rbm_local',sys.argv[1]);"
            "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
            "f=m.load_frames_input(sys.argv[2],fps=1.0,max_frames=512);"
            "print(json.dumps([hashlib.sha256(x.tobytes()).hexdigest() for x in f]))"
        )
        probe_env = os.environ.copy()
        probe_env["PYTHONPATH"] = str(repo)
        probe = subprocess.run([sys.executable, "-c", probe_code, str(script),
                                str(input_dir / video)], capture_output=True, text=True,
                               env=probe_env, check=False)
        try:
            native_hashes = json.loads(probe.stdout.splitlines()[-1]) if probe.returncode == 0 else []
        except (json.JSONDecodeError, IndexError):
            native_hashes = []
        append_jsonl(journal, {"kind": "native_decoder_probe", "video": video,
                               "returncode": probe.returncode,
                               "frame_count": len(native_hashes),
                               "decoded_rgb_sha256": native_hashes,
                               "same_pixels_as_manifest": native_hashes == [
                                   row["decoded_pixel_sha256"][str(t)] for t in range(15)],
                               "stderr_excerpt": probe.stderr[-1000:]})
        output = out_dir / (Path(video).stem + ".npy")
        command = [sys.executable, str(script), "--model-path", str(model_path),
                   "--video", str(input_dir / video), "--task", row["instruction"],
                   "--fps", "1", "--out", str(output)]
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(repo)
        started = time.perf_counter()
        result = subprocess.run(command, capture_output=True, text=True, env=environment,
                                check=False)
        duration_ms = round((time.perf_counter() - started) * 1000)
        (out_dir / (Path(video).stem + ".stdout.txt")).write_text(result.stdout, encoding="utf-8")
        (out_dir / (Path(video).stem + ".stderr.txt")).write_text(result.stderr, encoding="utf-8")
        success = output.with_name(output.stem + "_success_probs.npy")
        if result.returncode != 0 or not output.is_file() or not success.is_file():
            append_jsonl(journal, {"kind": "native_failure", "method": "Robometer PR33 compat",
                                   "video": video, "returncode": result.returncode,
                                   "elapsed_ms": duration_ms,
                                   "stdout_sha256": sha256(out_dir / (Path(video).stem + ".stdout.txt")),
                                   "stderr_sha256": sha256(out_dir / (Path(video).stem + ".stderr.txt"))})
            continue
        try:
            progress = np.load(output, allow_pickle=False).tolist()
            success_values = np.load(success, allow_pickle=False).tolist()
            if len(progress) != 15 or len(success_values) != 15:
                raise ValueError("unexpected progress/success length")
        except Exception as exc:
            append_jsonl(journal, {"kind": "native_failure", "method": "Robometer PR33 compat",
                                   "video": video, "error": f"{type(exc).__name__}: {exc}"})
            continue
        append_jsonl(journal, {"kind": "native_result", "method": "Robometer PR33 compat",
                               "video": video, "instruction": row["instruction"],
                               "video_sha256": row["sha256"], "progress": progress,
                               "success_head": success_values,
                               "progress_sha256": sha256(output), "success_sha256": sha256(success),
                               "elapsed_ms": duration_ms})


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

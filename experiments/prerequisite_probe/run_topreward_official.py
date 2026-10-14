"""Thin caller for the unmodified official TOPReward Qwen client."""

import argparse
import json
import sys
import types
from pathlib import Path

import cv2

# Keep the sole external instruction explicit; importing the simulator would
# pull truth-side dependencies into a model-only remote environment.
INSTRUCTION = "Put the blue cube in the green tray."
# The package initializer eagerly imports optional Gemini/OpenAI clients. Load the
# official Qwen module directly, without changing its implementation or prompts.
client_package = types.ModuleType("topreward.clients")
client_package.__path__ = [str(Path(__file__).parents[2] / "research" / "sources" / "TOPReward" / "topreward" / "clients")]
sys.modules["topreward.clients"] = client_package
from topreward.clients.qwen import QwenClient


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model-path", default="Qwen/Qwen3-VL-8B-Instruct",
                        help="Official HF model ID or exact pinned snapshot directory")
    args = parser.parse_args()
    cap = cv2.VideoCapture(str(args.video))
    frames = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    cap.release()
    if len(frames) != 15:
        raise RuntimeError(f"Expected 15 frames, got {len(frames)}")
    client = QwenClient(model_name=args.model_path)
    result = client.compute_instruction_rewards_for_prefixes(
        frames=frames, instruction=INSTRUCTION, num_samples=15,
        reduction="mean", fps=1.0, use_video_description=False,
        add_chat_template=False,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({
        "video": args.video.name, "instruction": INSTRUCTION,
        "prefix_lengths": result.prefix_lengths,
        "prefix_rewards": result.prefix_rewards,
        "model": "Qwen/Qwen3-VL-8B-Instruct",
        "model_path": args.model_path,
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

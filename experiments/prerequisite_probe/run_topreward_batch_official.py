"""Score the six frozen videos with one unmodified official TOPReward client."""

import argparse
import json
import sys
import time
import types
from pathlib import Path

import cv2


INSTRUCTION = "Put the blue cube in the green tray."
SOURCE = Path(__file__).parents[2] / "research" / "sources" / "TOPReward"
client_package = types.ModuleType("topreward.clients")
client_package.__path__ = [str(SOURCE / "topreward" / "clients")]
sys.modules["topreward.clients"] = client_package
from topreward.clients.qwen import QwenClient  # noqa: E402


def decode(path: Path) -> list:
    cap = cv2.VideoCapture(str(path))
    frames = []
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    finally:
        cap.release()
    if len(frames) != 15 or any(frame.shape != (480, 640, 3) for frame in frames):
        raise RuntimeError(f"Unexpected frames in {path.name}: {len(frames)}")
    return frames


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    client = QwenClient(model_name=args.model_path)
    for number in range(1, 7):
        video = args.input_dir / f"{number:04d}.mp4"
        frames = decode(video)
        start = time.monotonic()
        result = client.compute_instruction_rewards_for_prefixes(
            frames=frames,
            instruction=INSTRUCTION,
            num_samples=15,
            reduction="mean",
            fps=1.0,
            use_video_description=False,
            add_chat_template=False,
        )
        payload = {
            "video": video.name,
            "instruction": INSTRUCTION,
            "model": "Qwen/Qwen3-VL-8B-Instruct",
            "model_revision": "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b",
            "official_repository_commit": "4877a0ee5098cbec18485125466631b1dcc4a573",
            "model_path": args.model_path,
            "prefix_lengths": result.prefix_lengths,
            "prefix_rewards": result.prefix_rewards,
            "reduction": "mean",
            "fps": 1.0,
            "use_video_description": False,
            "add_chat_template": False,
            "elapsed_seconds": time.monotonic() - start,
        }
        output = args.out_dir / f"{number:04d}.json"
        output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"SCORED {video.name} -> {output}", flush=True)


if __name__ == "__main__":
    main()

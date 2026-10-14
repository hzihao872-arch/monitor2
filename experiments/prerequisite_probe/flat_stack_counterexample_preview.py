"""Development challenge: can the main view distinguish blue-on-red from blue-on-table?"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

from .distractor_scenes import make_flat_with_distractor
from .flat_square_dev import FlatSquareSpec, evaluate_terminal
from .flat_square_operational_check import RetryIK
from .flat_square_route_challenge import direct_place_spec, position
from .probe import FPS, PandaIK
from .produce import action_at, build_keyframes


def run(output: Path):
    output.mkdir(parents=True, exist_ok=True)
    records = {}
    for start in ("blocked", "open"):
        env = make_flat_with_distractor(start)
        try:
            env.reset(seed=20261005)
            scene = env.unwrapped
            keyframes, ik_errors = build_keyframes(env, direct_place_spec(), RetryIK(PandaIK()))
            images = {}
            for index in range(15 * FPS):
                if index:
                    env.step(action_at(index / FPS, keyframes))
                if index in (14 * FPS, 15 * FPS - 1):
                    frame = env.render().cpu().numpy()[0]
                    name = f"direct_place_{start}_{index}.png"
                    Image.fromarray(frame).save(output / name)
                    images[name] = hashlib.sha256(frame.tobytes()).hexdigest()
            records[start] = {
                "red_xyz": position(scene.red), "blue_xyz": position(scene.blue),
                "terminal": evaluate_terminal(list(scene._terminal_window), FlatSquareSpec()),
                "last_terminal_sample": scene._terminal_sample(),
                "ik_errors": ik_errors, "raw_rgb_sha256": images,
            }
        finally:
            env.close()
    (output / "mapping.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    return {k: {"terminal": v["terminal"], "blue_xyz": v["blue_xyz"]}
            for k, v in records.items()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output)))

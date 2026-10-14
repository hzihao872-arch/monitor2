"""Replay the saved scripts to capture a second, truth-only camera."""

import copy
import json
from pathlib import Path

import numpy as np
from PIL import Image

from .probe import make_env
from .produce import CASES, record_case, script_for


def capture(env, path):
    env.unwrapped.scene.update_render()
    camera = env.unwrapped.scene.sensors["front_camera"]
    camera.capture()
    rgb = camera.get_obs(rgb=True, depth=False, position=False, segmentation=False)["rgb"]
    Image.fromarray(rgb.cpu().numpy()[0]).save(path)


def main():
    root = Path("experiments/prerequisite_probe/artifacts")
    out = root / "truth" / "auxiliary"
    out.mkdir(parents=True, exist_ok=True)
    records = []
    for condition, stem in CASES.items():
        env = make_env("cell", script_for(condition)["red_start"])
        try:
            env.reset(seed=20261004)
            initial = copy.deepcopy(env.unwrapped.get_state_dict())
            capture(env, out / f"{stem}_pre.png")
            replay = record_case(env, condition, root, initial, render=False)
            capture(env, out / f"{stem}_post.png")
            original = json.loads((root / "truth" / f"{stem}.json").read_text(encoding="utf-8"))
            error = max(
                float(np.max(np.abs(np.asarray(replay[key]) - np.asarray(original[key]))))
                for key in ("blue_post", "red_post")
            )
            if error > .002:
                raise RuntimeError(f"Auxiliary replay diverged for {condition}: {error} m")
            records.append({"id": stem, "pre": f"{stem}_pre.png", "post": f"{stem}_post.png",
                            "replay_max_position_error_metres": error})
        finally:
            env.close()
    (root / "truth" / "auxiliary_review.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(json.dumps(records))


if __name__ == "__main__":
    main()

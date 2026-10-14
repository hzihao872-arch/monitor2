"""Author-only preview of the revised A lid, outside the blind/model packages."""

from pathlib import Path

from PIL import Image

from experiments.prerequisite_probe.fresh_prerequisite.scenes import (
    ACCESS, GATE_CLOSED, GATE_OPEN, make_env,
)


def main():
    target = Path("tmp/fresh_previews/access_dev_v3")
    target.mkdir(parents=True, exist_ok=True)
    env = make_env("access_gate", "blocked")
    try:
        env.reset(seed=20261006)
        for name, pose in (
            ("blocked", GATE_CLOSED),
            ("partial", (GATE_CLOSED[0], GATE_CLOSED[1] + ACCESS.partial_travel, GATE_CLOSED[2])),
            ("open", GATE_OPEN),
        ):
            env.unwrapped.set_prerequisite_pose(pose)
            Image.fromarray(env.render().cpu().numpy()[0]).save(target / f"{name}.png")
    finally:
        env.close()
    print(target, ACCESS.partial_open_width)


if __name__ == "__main__":
    main()

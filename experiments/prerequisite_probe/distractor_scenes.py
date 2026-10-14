"""Final-six development variants with one unrelated yellow object.

The original flat/source scene registrations remain available to reproduce the
S0/S1 and first observability-pilot artifacts without the yellow object.
"""

from __future__ import annotations

import json
from pathlib import Path

from mani_skill.utils.building import actors
from mani_skill.utils.registration import register_env
import sapien

from .flat_square_scene import FlatSquareDevEnv
from .probe import FPS
from .source_lid_scene import SourceLidDevEnv


YELLOW_HALF = 0.015
YELLOW_START_XY = (-0.18, 0.16)
YELLOW_DEST_XY = (-0.18, -0.02)


def add_yellow(scene):
    return actors.build_cube(
        scene,
        half_size=YELLOW_HALF,
        color=[0.98, 0.84, 0.03, 1],
        name="yellow_irrelevant_cube",
        initial_pose=sapien.Pose(p=[*YELLOW_START_XY, YELLOW_HALF]),
    )


@register_env("PrerequisiteFlatSquareDev-v2", max_episode_steps=1000)
class FlatSquareWithDistractorEnv(FlatSquareDevEnv):
    def _load_scene(self, options):
        super()._load_scene(options)
        self.yellow = add_yellow(self.scene)

    def _initialize_episode(self, env_idx, options):
        super()._initialize_episode(env_idx, options)
        self.yellow.set_pose(sapien.Pose(p=[*YELLOW_START_XY, YELLOW_HALF]))


@register_env("PrerequisiteSourceLidDev-v2", max_episode_steps=1000)
class SourceLidWithDistractorEnv(SourceLidDevEnv):
    def _load_scene(self, options):
        super()._load_scene(options)
        self.yellow = add_yellow(self.scene)

    def _initialize_episode(self, env_idx, options):
        super()._initialize_episode(env_idx, options)
        self.yellow.set_pose(sapien.Pose(p=[*YELLOW_START_XY, YELLOW_HALF]))


@register_env("PrerequisiteSourceLidDev-v3-handle", max_episode_steps=1000)
class SourceLidWithHandleEnv(SourceLidWithDistractorEnv):
    """Separate revision: a graspable red knob enables the H- challenge."""

    lid_handle = True


def _make(scene_id, red_start):
    import gymnasium as gym

    return gym.make(
        scene_id,
        red_start=red_start,
        obs_mode="state",
        render_mode="rgb_array",
        sim_backend="cpu",
        render_backend="cpu",
        num_envs=1,
        control_mode="pd_joint_pos",
        reward_mode="sparse",
        sim_config={"sim_freq": 120, "control_freq": FPS},
    )


def make_flat_with_distractor(red_start="blocked"):
    return _make("PrerequisiteFlatSquareDev-v2", red_start)


def make_source_with_distractor(red_start="blocked"):
    return _make("PrerequisiteSourceLidDev-v2", red_start)


def make_source_with_handle(red_start="blocked"):
    return _make("PrerequisiteSourceLidDev-v3-handle", red_start)


def save_preview(output: Path):
    from PIL import Image

    output.mkdir(parents=True, exist_ok=True)
    records = {}
    for kind, factory in (("flat_square", make_flat_with_distractor),
                          ("source_lid", make_source_with_distractor)):
        for red_start in ("blocked", "open"):
            env = factory(red_start)
            try:
                env.reset(seed=20261005)
                frame = env.render().cpu().numpy()[0]
                name = f"{kind}_{red_start}_main.png"
                Image.fromarray(frame).save(output / name)
                records[name] = {
                    "blue_xyz": env.unwrapped.blue.pose.p[0].cpu().numpy().tolist(),
                    "red_xyz": env.unwrapped.red.pose.p[0].cpu().numpy().tolist(),
                    "yellow_xyz": env.unwrapped.yellow.pose.p[0].cpu().numpy().tolist(),
                }
            finally:
                env.close()
    (output / "preview_state.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    return records


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--preview-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(save_preview(args.preview_dir)))

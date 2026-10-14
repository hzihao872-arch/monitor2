"""Isolated ManiSkill development scene for the tabletop flat-square goal."""

from __future__ import annotations

from collections import deque
import json
from pathlib import Path

import numpy as np
import sapien
import torch

from mani_skill.sensors.camera import CameraConfig
from mani_skill.utils import sapien_utils
from mani_skill.utils.building import actors
from mani_skill.utils.registration import register_env
from mani_skill.utils.scene_builder.table import TableSceneBuilder

from .flat_square_dev import FlatSquareSpec, evaluate_terminal
from .probe import FPS, SIZE, PrerequisiteProbeEnv


SPEC = FlatSquareSpec()
BLUE_XY = (-0.13, -0.13)
RED_OPEN_XY = (0.02, 0.18)


def any_robot_contact(link_impulses):
    """A single contacting link is enough to fail the release condition."""
    return any(float(np.linalg.norm(impulse)) > 1e-6 for impulse in link_impulses)


def build_target_square(scene):
    """Four low green strips leave the target table surface uncovered."""
    tx, ty = SPEC.target_x, SPEC.target_y
    border_half_width = 0.003
    border_half_height = 0.0005
    edge = SPEC.square_inner_half + border_half_width
    parts = (
        ("square_x_minus", (border_half_width, edge + border_half_width, border_half_height), (tx - edge, ty, border_half_height)),
        ("square_x_plus", (border_half_width, edge + border_half_width, border_half_height), (tx + edge, ty, border_half_height)),
        ("square_y_minus", (SPEC.square_inner_half, border_half_width, border_half_height), (tx, ty - edge, border_half_height)),
        ("square_y_plus", (SPEC.square_inner_half, border_half_width, border_half_height), (tx, ty + edge, border_half_height)),
    )
    result = {}
    for name, half, centre in parts:
        result[name] = actors.build_box(
            scene, half_sizes=half, color=[0.03, 0.82, 0.13, 1],
            name=name, body_type="static", initial_pose=sapien.Pose(p=centre),
        )
    return result


@register_env("PrerequisiteFlatSquareDev-v1", max_episode_steps=1000)
class FlatSquareDevEnv(PrerequisiteProbeEnv):
    """New scene registration; the legacy probe and its labels stay untouched."""

    def __init__(self, *args, red_start="blocked", **kwargs):
        self.flat_spec = SPEC
        self._terminal_window = deque(maxlen=20)
        super().__init__(*args, scene_kind="flat_square_dev", red_start=red_start, **kwargs)

    def _camera(self, name):
        pose = sapien_utils.look_at(eye=[-0.17, -0.42, 0.46], target=[0.07, -0.01, 0.04])
        return CameraConfig(name, pose, SIZE[0], SIZE[1], 0.85, 0.01, 10)

    def _load_scene(self, options):
        self.table_scene = TableSceneBuilder(self, robot_init_qpos_noise=0)
        self.table_scene.build()
        self.blue = actors.build_cube(
            self.scene, half_size=SPEC.blue_half, color=[0.04, 0.18, 0.95, 1],
            name="blue_cube", initial_pose=sapien.Pose(p=[0, 0, SPEC.blue_half]),
        )
        self.red = actors.build_cube(
            self.scene, half_size=SPEC.red_half, color=[0.95, 0.07, 0.04, 1],
            name="red_cube", initial_pose=sapien.Pose(p=[0, 0, SPEC.red_half]),
        )
        # Thin green strips mark a single inner tabletop square. No green floor
        # supports the blue cube: direct support must come from the table.
        self.static_parts = build_target_square(self.scene)

    def _initialize_episode(self, env_idx: torch.Tensor, options: dict):
        self.table_scene.initialize(env_idx)
        self._terminal_window.clear()
        self.blue.set_pose(sapien.Pose(p=[*BLUE_XY, SPEC.blue_half]))
        red_xy = (SPEC.target_x, SPEC.target_y) if self.red_start == "blocked" else RED_OPEN_XY
        self.red.set_pose(sapien.Pose(p=[*red_xy, SPEC.red_half]))

    def _terminal_sample(self):
        contacts = self.scene.get_contacts()
        blue_entity = self.blue._bodies[0].entity
        table_entity = self.table_scene.table._bodies[0].entity
        red_entity = self.red._bodies[0].entity
        table_impulse = sapien_utils.get_pairwise_contact_impulse(contacts, blue_entity, table_entity)
        red_impulse = sapien_utils.get_pairwise_contact_impulse(contacts, blue_entity, red_entity)
        robot_impulses = (
            sapien_utils.get_pairwise_contact_impulse(contacts, blue_entity, link._bodies[0].entity)
            for link in self.agent.robot.get_links()
        )
        qpos = self.agent.robot.get_qpos()[0].detach().cpu().numpy()
        return {
            "time_s": float(self.elapsed_steps[0]) / FPS,
            "blue_position": self.blue.pose.p[0].detach().cpu().numpy().tolist(),
            "blue_quaternion_wxyz": self.blue.pose.q[0].detach().cpu().numpy().tolist(),
            "blue_linear_speed_mps": float(torch.linalg.norm(self.blue.linear_velocity[0])),
            "blue_angular_speed_radps": float(torch.linalg.norm(self.blue.angular_velocity[0])),
            "table_support_contact": bool(table_impulse[2] > 1e-6),
            "other_support_contact": bool(red_impulse[2] > 1e-6),
            "gripper_open": bool(np.min(qpos[-2:]) > 0.035),
            "gripper_touching_blue": any_robot_contact(robot_impulses),
        }

    def evaluate(self):
        sample = self._terminal_sample()
        if self._terminal_window and sample["time_s"] <= self._terminal_window[-1]["time_s"]:
            self._terminal_window.pop()
        self._terminal_window.append(sample)
        result = evaluate_terminal(list(self._terminal_window), self.flat_spec)
        return {"success": torch.tensor([result["success"]], device=self.device)}

    def compute_dense_reward(self, obs, action, info):
        return info["success"].float()


def make_flat_env(red_start="blocked"):
    import gymnasium as gym
    return gym.make(
        "PrerequisiteFlatSquareDev-v1", red_start=red_start,
        obs_mode="state", render_mode="rgb_array", sim_backend="cpu",
        render_backend="cpu", num_envs=1, control_mode="pd_joint_pos",
        reward_mode="sparse", sim_config={"sim_freq": 120, "control_freq": FPS},
    )


def save_preview(output: Path):
    from PIL import Image
    output.mkdir(parents=True, exist_ok=True)
    records = {}
    for start in ("blocked", "open"):
        env = make_flat_env(start)
        try:
            env.reset(seed=20261005)
            frame = env.render().cpu().numpy()[0]
            path = output / f"flat_square_{start}_main.png"
            Image.fromarray(frame).save(path)
            records[start] = {
                "path": str(path), "shape": list(frame.shape),
                "blue_xyz": env.unwrapped.blue.pose.p[0].detach().cpu().numpy().tolist(),
                "red_xyz": env.unwrapped.red.pose.p[0].detach().cpu().numpy().tolist(),
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

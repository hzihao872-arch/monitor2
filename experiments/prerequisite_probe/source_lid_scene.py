"""Source-access lid candidate, separate from destination-occupancy mechanism."""

from __future__ import annotations

from collections import deque
import json
from pathlib import Path

import sapien
import torch
from mani_skill.utils.building import actors
from mani_skill.utils.registration import register_env
from mani_skill.utils.scene_builder.table import TableSceneBuilder

from .flat_square_scene import SPEC, FlatSquareDevEnv, build_target_square
from .probe import FPS


LID_BLOCKED_Z = 0.062
LID_HALF_THICKNESS = 0.006
LID_HALF_EXTENT = 0.066
LID_BAR_PITCH = 0.024
LID_BAR_HALF_WIDTH = 0.005
SOURCE_WALL_TOP = 0.056
SOURCE_INNER_HALF = 0.054
LID_OPEN_XY = (0.02, 0.18)
SOURCE_BLUE_XY = (-0.08, -0.07)
LID_HANDLE_LOCAL_XYZ = (0.045, 0.0, 0.021)
LID_HANDLE_HALF = 0.016


def source_cage_geometry_bound():
    """Ideal rigid exit-width check while the red lid stays at its start pose."""
    outer_bar_edge = 2 * LID_BAR_PITCH + LID_BAR_HALF_WIDTH
    return {
        "blue_minimum_caliper_width_m": 2 * SPEC.blue_half,
        "maximum_top_aperture_m": LID_BAR_PITCH - 2 * LID_BAR_HALF_WIDTH,
        "peripheral_slit_m": max(0.0, SOURCE_INNER_HALF - outer_bar_edge),
        "lid_bottom_z_m": LID_BLOCKED_Z - LID_HALF_THICKNESS,
        "wall_top_z_m": SOURCE_WALL_TOP,
    }


def build_red_grated_lid(scene, *, with_handle=False):
    """One rigid red body with narrow sight apertures, not a transparent slab."""
    builder = scene.create_actor_builder()
    material = sapien.render.RenderMaterial(base_color=[0.95, 0.07, 0.04, 1])
    for offset in (i * LID_BAR_PITCH for i in (-2, -1, 0, 1, 2)):
        for xyz, half in (((0, offset, 0), (LID_HALF_EXTENT, LID_BAR_HALF_WIDTH, LID_HALF_THICKNESS)),
                          ((offset, 0, 0), (LID_BAR_HALF_WIDTH, LID_HALF_EXTENT, LID_HALF_THICKNESS))):
            pose = sapien.Pose(p=xyz)
            builder.add_box_collision(pose=pose, half_size=half)
            builder.add_box_visual(pose=pose, half_size=half, material=material)
    if with_handle:
        handle_pose = sapien.Pose(p=LID_HANDLE_LOCAL_XYZ)
        handle_half = (LID_HANDLE_HALF,) * 3
        builder.add_box_collision(pose=handle_pose, half_size=handle_half)
        builder.add_box_visual(pose=handle_pose, half_size=handle_half, material=material)
    builder.set_initial_pose(sapien.Pose(p=[0, 0, LID_BLOCKED_Z]))
    return builder.build(name="red_source_lid")


@register_env("PrerequisiteSourceLidDev-v1", max_episode_steps=1000)
class SourceLidDevEnv(FlatSquareDevEnv):
    """Rigid source enclosure with a removable translucent red collision lid."""

    def _load_scene(self, options):
        self.table_scene = TableSceneBuilder(self, robot_init_qpos_noise=0)
        self.table_scene.build()
        self.blue = actors.build_cube(
            self.scene, half_size=SPEC.blue_half, color=[0.04, 0.18, 0.95, 1],
            name="blue_cube", initial_pose=sapien.Pose(p=[0, 0, SPEC.blue_half]),
        )
        self.red = build_red_grated_lid(
            self.scene, with_handle=getattr(self, "lid_handle", False)
        )
        self.static_parts = build_target_square(self.scene)
        sx, sy = SOURCE_BLUE_XY
        wall_half_height = SOURCE_WALL_TOP / 2
        walls = (
            ("source_x_minus", (0.006, 0.060, wall_half_height), (sx - 0.060, sy, wall_half_height)),
            ("source_x_plus", (0.006, 0.060, wall_half_height), (sx + 0.060, sy, wall_half_height)),
            ("source_y_minus", (0.054, 0.006, wall_half_height), (sx, sy - 0.060, wall_half_height)),
            ("source_y_plus", (0.054, 0.006, wall_half_height), (sx, sy + 0.060, wall_half_height)),
        )
        for name, half, centre in walls:
            self.static_parts[name] = actors.build_box(
                self.scene, half_sizes=half, color=[0.42, 0.47, 0.52, 1],
                name=name, body_type="static", initial_pose=sapien.Pose(p=centre),
            )

    def _initialize_episode(self, env_idx: torch.Tensor, options: dict):
        self.table_scene.initialize(env_idx)
        self._terminal_window = deque(maxlen=20)
        self.blue.set_pose(sapien.Pose(p=[*SOURCE_BLUE_XY, SPEC.blue_half]))
        red_xyz = [*SOURCE_BLUE_XY, LID_BLOCKED_Z] if self.red_start == "blocked" else [*LID_OPEN_XY, 0.006]
        self.red.set_pose(sapien.Pose(p=red_xyz))


def make_source_lid_env(red_start="blocked"):
    import gymnasium as gym
    return gym.make(
        "PrerequisiteSourceLidDev-v1", red_start=red_start,
        obs_mode="state", render_mode="rgb_array", sim_backend="cpu",
        render_backend="cpu", num_envs=1, control_mode="pd_joint_pos",
        reward_mode="sparse", sim_config={"sim_freq": 120, "control_freq": FPS},
    )


def save_preview(output: Path):
    from PIL import Image
    output.mkdir(parents=True, exist_ok=True)
    records = {}
    for start in ("blocked", "open"):
        env = make_source_lid_env(start)
        try:
            env.reset(seed=20261005)
            frame = env.render().cpu().numpy()[0]
            path = output / f"source_lid_{start}_main.png"
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

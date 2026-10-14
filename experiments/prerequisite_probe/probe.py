"""ManiSkill rigid-scene and video-input probe (no reward logic)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import sapien
import torch

from mani_skill.envs.sapien_env import BaseEnv
from mani_skill.sensors.camera import CameraConfig
from mani_skill.utils import sapien_utils
from mani_skill.utils.building import actors
from mani_skill.utils.registration import register_env
from mani_skill.utils.scene_builder.table import TableSceneBuilder


INSTRUCTION = "Put the blue cube in the green tray."
FPS = 30
SECONDS = 15
SIZE = (640, 480)

SCENE_LAYOUTS = {
    "cell": {"tray": (.12, -.12), "blue": (-.09, .12),
             "blocked": (.12, -.12, .048), "open": (.12, .13, .034)},
    "offset_cell": {"tray": (.18, .10), "blue": (-.13, -.13),
                    "blocked": (.18, .10, .048), "open": (.18, -.16, .034)},
    "pickup_gate": {"tray": (.12, -.12), "blue": (-.09, .12),
                    "blocked": (-.09, .04, .034), "open": (.12, .13, .034)},
    "pickup_gate_opposite": {"tray": (.12, -.12), "blue": (-.09, .12),
                             "blocked": (-.09, .185, .034), "open": (.12, .13, .034)},
    "mirror_cell": {"tray": (.10, .15), "blue": (-.12, -.10),
                    "blocked": (.10, .15, .048), "open": (.10, -.15, .034)},
    "left_cell": {"tray": (-.12, -.20), "blue": (.14, .11),
                  "blocked": (-.12, -.20, .048), "open": (.15, -.17, .034)},
    "pickup_gate_shifted": {"tray": (.12, -.12), "blue": (-.03, .12),
                            "blocked": (-.03, .04, .034), "open": (.16, .13, .034)},
    "rear_cell": {"tray": (.23, -.04), "blue": (-.16, .18),
                  "blocked": (.23, -.04, .048), "open": (.04, .18, .034)},
    "source_stack": {"tray": (.18, .10), "blue": (-.13, -.13),
                     "blocked": (-.13, -.13, .064), "open": (.015, .17, .018)},
    "tray_crossbar": {"tray": (.18, .10), "blue": (-.13, -.13),
                      "blocked": (.18, .10, .066), "open": (.015, .17, .015)},
    "source_bridge": {"tray": (.18, .10), "blue": (-.13, -.13),
                      "blocked": (-.13, -.13, .105), "open": (.015, .17, .015)},
}


def sample_indices(fps: int = FPS, seconds: int = SECONDS) -> list[int]:
    return list(range(0, fps * seconds, fps))


def _jsonable(value):
    if isinstance(value, dict):
        return {key: _jsonable(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (np.ndarray, torch.Tensor)):
        return value.detach().cpu().tolist() if isinstance(value, torch.Tensor) else value.tolist()
    if isinstance(value, (int, float, bool, str)) or value is None:
        return value
    raise TypeError(type(value))


def snapshot_signature(state: dict) -> str:
    payload = json.dumps(_jsonable(state), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class PandaIK:
    """CPU inverse kinematics for joint-position trajectories on Windows."""

    home_q = np.array([0, np.pi / 8, 0, -5 * np.pi / 8, 0, 3 * np.pi / 4, np.pi / 4])

    def __init__(self):
        import contextlib
        import io
        import pytorch_kinematics as pk
        from mani_skill.agents.robots.panda.panda import Panda

        with contextlib.redirect_stderr(io.StringIO()):
            self.chain = pk.build_serial_chain_from_urdf(
                Path(Panda.urdf_path).read_text(), "panda_hand_tcp"
            ).to(dtype=torch.float64)
        self.lower, self.upper = (np.array(x) for x in self.chain.get_joint_limits())
        self.target_rotation = np.diag([1.0, -1.0, -1.0])

    def fk(self, q: np.ndarray):
        value = self.chain.forward_kinematics(torch.as_tensor(q, dtype=torch.float64))
        matrix = value.get_matrix()[0].detach().numpy()
        matrix[:3, 3] += np.array([-.615, 0, 0])
        return matrix

    def solve(self, xyz: np.ndarray, q0: np.ndarray):
        from scipy.optimize import least_squares
        from scipy.spatial.transform import Rotation

        target = np.asarray(xyz, dtype=np.float64)

        def residual(q):
            matrix = self.fk(q)
            pos = matrix[:3, 3] - target
            rot = Rotation.from_matrix(self.target_rotation @ matrix[:3, :3].T).as_rotvec()
            return np.r_[pos, .12 * rot, .003 * (q - q0)]

        result = least_squares(
            residual, np.clip(q0, self.lower + 1e-4, self.upper - 1e-4),
            bounds=(self.lower + 1e-4, self.upper - 1e-4),
            max_nfev=90, ftol=1e-5,
        )
        q = result.x
        error = float(np.linalg.norm(self.fk(q)[:3, 3] - target))
        return q, error


def geometry(scene: str):
    """Static collision boxes: name, half sizes, centre, RGBA."""
    grey = [0.42, 0.47, 0.52, 1]
    green = [0.06, 0.72, 0.16, 1]
    if scene == "narrow":
        parts = [
            ("left_wall", (.135, .012, .077), (.13, -.092, .077), grey),
            ("right_wall", (.135, .012, .077), (.13, .092, .077), grey),
            ("rear_wall", (.012, .092, .077), (.264, 0, .077), grey),
        ]
        parts += [
            (f"roof_{i}", (.009, .092, .008), (x, 0, .160), grey)
            for i, x in enumerate((.014, .064, .114, .164, .214, .264))
        ]
        tx, ty = -.12, -.25
    elif scene in SCENE_LAYOUTS:
        parts = []
        tx, ty = SCENE_LAYOUTS[scene]["tray"]
        if scene == "source_bridge":
            bx, by = SCENE_LAYOUTS[scene]["blue"]
            parts += [
                ("source_bridge_left", (.012, .018, .045), (bx - .075, by, .045), grey),
                ("source_bridge_right", (.012, .018, .045), (bx + .075, by, .045), grey),
            ]
    else:
        raise ValueError(scene)
    # A real shallow tray: solid base and four walls, all collision-enabled.
    parts += [
        ("tray_base", (.083, .083, .007), (tx, ty, .007), green),
        ("tray_left", (.083, .008, .022), (tx, ty - .075, .029), green),
        ("tray_right", (.083, .008, .022), (tx, ty + .075, .029), green),
        ("tray_front", (.008, .067, .022), (tx - .075, ty, .029), green),
        ("tray_back", (.008, .067, .022), (tx + .075, ty, .029), green),
    ]
    return parts


@register_env("PrerequisiteProbe-v0", max_episode_steps=1000)
class PrerequisiteProbeEnv(BaseEnv):
    SUPPORTED_ROBOTS = ["panda"]

    def __init__(self, *args, scene_kind="narrow", red_start="blocked", **kwargs):
        self.scene_kind = scene_kind
        self.red_start = red_start
        super().__init__(*args, robot_uids="panda", **kwargs)

    @property
    def _default_sensor_configs(self):
        return [self._camera("base_camera"), self._front_camera()]

    @property
    def _default_human_render_camera_configs(self):
        return self._camera("render_camera")

    def _camera(self, name):
        pose = sapien_utils.look_at(eye=[-.35, -.48, .46], target=[.04, -.03, .045])
        return CameraConfig(name, pose, SIZE[0], SIZE[1], 1.05, .01, 10)

    def _front_camera(self):
        pose = sapien_utils.look_at(eye=[-.28, .39, .25], target=[.04, -.02, .045])
        return CameraConfig("front_camera", pose, SIZE[0], SIZE[1], 1.05, .01, 10)

    def _load_agent(self, options):
        super()._load_agent(options, sapien.Pose(p=[-.615, 0, 0]))

    def _load_scene(self, options):
        self.table_scene = TableSceneBuilder(self, robot_init_qpos_noise=0)
        self.table_scene.build()
        self.blue = actors.build_cube(
            self.scene, half_size=.023, color=[.04, .18, .95, 1],
            name="blue_cube", initial_pose=sapien.Pose(p=[0, 0, .023]),
        )
        if self.scene_kind == "source_stack":
            red_half = (.018, .018, .018)
        elif self.scene_kind in ("tray_crossbar", "source_bridge"):
            red_half = (.085, .015, .015)
        else:
            red_half = (.034, .034, .034)
        self.red = actors.build_box(
            self.scene, half_sizes=red_half, color=[.95, .07, .04, 1],
            name="red_block", initial_pose=sapien.Pose(p=[0, 0, .034]),
        )
        self.static_parts = {}
        for name, half, centre, color in geometry(self.scene_kind):
            self.static_parts[name] = actors.build_box(
                self.scene, half_sizes=half, color=color, name=name,
                body_type="static", initial_pose=sapien.Pose(p=centre),
            )

    def _initialize_episode(self, env_idx: torch.Tensor, options: dict):
        self.table_scene.initialize(env_idx)
        if self.scene_kind == "narrow":
            blue_xyz = (.16, 0, .023)
            blocked_xyz = (-.022, 0, .034)
            open_xyz = (-.04, .20, .034)
        else:
            layout = SCENE_LAYOUTS[self.scene_kind]
            blue_xyz = (*layout["blue"], .023)
            blocked_xyz = layout["blocked"]
            open_xyz = layout["open"]
        self.blue.set_pose(sapien.Pose(p=blue_xyz))
        self.red.set_pose(sapien.Pose(p=blocked_xyz if self.red_start == "blocked" else open_xyz))

    def _get_obs_extra(self, info: dict):
        return {}

    def evaluate(self):
        tx, ty = ((-.12, -.25) if self.scene_kind == "narrow" else
                  SCENE_LAYOUTS[self.scene_kind]["tray"])
        p = self.blue.pose.p
        placed = ((p[:, 0] - tx).abs() < .046) & ((p[:, 1] - ty).abs() < .046) & (p[:, 2] < .09)
        return {"success": placed}

    def compute_dense_reward(self, obs, action, info):
        return info["success"].float()


def make_env(scene_kind="narrow", red_start="blocked"):
    import gymnasium as gym

    return gym.make(
        "PrerequisiteProbe-v0", scene_kind=scene_kind, red_start=red_start,
        obs_mode="state", render_mode="rgb_array", sim_backend="cpu",
        render_backend="cpu", num_envs=1, control_mode="pd_joint_pos",
        reward_mode="sparse",
        sim_config={"sim_freq": 120, "control_freq": FPS},
    )


def save_smoke_frame(path: Path, scene_kind="narrow"):
    from PIL import Image

    env = make_env(scene_kind)
    try:
        env.reset(seed=20261004)
        frame = env.render().cpu().numpy()[0]
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(frame).save(path)
        return {"shape": list(frame.shape), "mean": float(frame.mean())}
    finally:
        env.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", choices=("narrow", "cell"), default="narrow")
    parser.add_argument("--smoke-frame", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(save_smoke_frame(args.smoke_frame, args.scene)))

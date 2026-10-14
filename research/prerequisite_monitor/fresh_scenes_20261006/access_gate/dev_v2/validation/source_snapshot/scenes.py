"""New rigid access and deployable landing scenes in ManiSkill/SAPIEN.

The gate and landing use prescribed kinematic motion on fixed guides. This is
explicitly recorded as a scene limitation, never described as a free dynamics
grasp. The blue cube is a dynamic body and its terminal support is measured by
SAPIEN contacts.
"""

from collections import deque

import numpy as np
import sapien
import torch

from mani_skill.sensors.camera import CameraConfig
from mani_skill.utils import sapien_utils
from mani_skill.utils.building import actors
from mani_skill.utils.registration import register_env
from mani_skill.utils.scene_builder.table import TableSceneBuilder

from experiments.prerequisite_probe.probe import PrerequisiteProbeEnv

from .contract import AccessSpec, SupportSpec, evaluate_terminal


ACCESS = AccessSpec()
SUPPORT = SupportSpec()
BLUE_START = (-0.10, -0.12)
GATE_CLOSED = (ACCESS.target_x, ACCESS.target_y, 0.176)
GATE_OPEN = (ACCESS.target_x, ACCESS.target_y + 0.130, 0.176)
PANEL_PARKED = (SUPPORT.target_x, -0.100, 0.115)
PANEL_DEPLOYED = (SUPPORT.target_x, SUPPORT.target_y, 0.115)
DECOY_START = (-0.015, 0.170, 0.027)
DECOY_END = (-0.015, 0.040, 0.027)


def _box(scene, name, half, center, color, body_type="static"):
    return actors.build_box(
        scene, half_sizes=half, color=color, name=name,
        body_type=body_type, initial_pose=sapien.Pose(p=center),
    )


@register_env("FreshPrerequisite-v1", max_episode_steps=1000)
class FreshPrerequisiteEnv(PrerequisiteProbeEnv):
    def __init__(self, *args, mechanism="access_gate", start_state="blocked", **kwargs):
        if mechanism not in ("access_gate", "support_surface"):
            raise ValueError(mechanism)
        if start_state not in ("blocked", "open"):
            raise ValueError(start_state)
        self.mechanism = mechanism
        self.start_state = start_state
        self.goal_spec = ACCESS if mechanism == "access_gate" else SUPPORT
        self._terminal_window = deque(maxlen=20)
        super().__init__(*args, scene_kind="fresh_prerequisite", red_start=start_state, **kwargs)

    def _camera(self, name):
        pose = sapien_utils.look_at(eye=[0.35, -0.38, 0.45], target=[0.03, 0.02, 0.065])
        return CameraConfig(name, pose, 640, 480, 0.86, 0.01, 10)

    def _front_camera(self):
        pose = sapien_utils.look_at(eye=[0.31, -0.20, 0.32], target=[0.07, 0.02, 0.08])
        return CameraConfig("front_camera", pose, 640, 480, 0.86, 0.01, 10)

    def _load_scene(self, options):
        self.table_scene = TableSceneBuilder(self, robot_init_qpos_noise=0)
        self.table_scene.build()
        self.blue = actors.build_cube(
            self.scene, half_size=self.goal_spec.cube_half,
            color=[0.05, 0.20, 0.92, 1], name="blue_cube",
            initial_pose=sapien.Pose(p=[*BLUE_START, self.goal_spec.cube_half]),
        )
        self.decoy = _box(self.scene, "pink_decoy", (.025, .025, .025),
                          DECOY_START, [0.92, 0.25, 0.52, 1], "kinematic")
        self.static_parts = {}
        if self.mechanism == "access_gate":
            self._build_access()
        else:
            self._build_support()

    def _build_access(self):
        x, y = ACCESS.target_x, ACCESS.target_y
        ivory = [0.78, 0.90, 0.88, 0.33]
        roof = [0.68, 0.77, 0.75, 1]
        self.floor = _box(self.scene, "box_floor", (.095, .095, .006),
                          (x, y, .006), [0.88, 0.93, 0.91, 1])
        self.static_parts["box_floor"] = self.floor
        # Four closed side walls and four solid roof bars around the only aperture.
        wall_defs = (
            ("wall_left", (.010, .095, .074), (x - .085, y, .086)),
            ("wall_right", (.010, .095, .074), (x + .085, y, .086)),
            ("wall_near", (.075, .010, .074), (x, y - .085, .086)),
            ("wall_far", (.075, .010, .074), (x, y + .085, .086)),
        )
        for name, half, center in wall_defs:
            self.static_parts[name] = _box(self.scene, name, half, center, ivory)
        roof_defs = (
            ("roof_left", (.020, .095, .006), (x - .075, y, .166)),
            ("roof_right", (.020, .095, .006), (x + .075, y, .166)),
            ("roof_near", (.055, .020, .006), (x, y - .075, .166)),
            ("roof_far", (.055, .020, .006), (x, y + .075, .166)),
        )
        for name, half, center in roof_defs:
            self.static_parts[name] = _box(self.scene, name, half, center, roof)
        # A visible opaque sliding lid; the roof aperture is genuinely open only
        # after this collision body has translated along its rails.
        self.prerequisite = _box(
            self.scene, "orange_sliding_lid", (.060, .060, .004),
            GATE_CLOSED, [0.96, 0.43, 0.07, 1], "kinematic",
        )
        self.handle_offset = (0, 0, .019)
        self.handle = _box(
            self.scene, "lid_handle", (.014, .014, .012),
            tuple(GATE_CLOSED[i] + self.handle_offset[i] for i in range(3)),
            [0.36, 0.27, 0.20, 1], "kinematic",
        )
        self.support_actor = self.floor

    def _build_support(self):
        x, y = SUPPORT.target_x, SUPPORT.target_y
        grey = [0.42, 0.46, 0.49, 1]
        # The rails are outside the landing footprint; no central fixed floor is
        # present at z=0.12. A falling cube may land on the table, which fails the
        # elevated target by height and panel-contact checks.
        for side, rail_x in (("left", x - .070), ("right", x + .070)):
            self.static_parts[f"rail_{side}"] = _box(
                self.scene, f"rail_{side}", (.008, .145, .008),
                (rail_x, -0.010, .105), grey,
            )
        for side, mark_x in (("left", x - .060), ("right", x + .060)):
            self.static_parts[f"landing_mark_{side}"] = _box(
                self.scene, f"landing_mark_{side}", (.003, .055, .002),
                (mark_x, y, .119), [0.11, 0.73, 0.28, 1],
            )
        self.prerequisite = _box(
            self.scene, "yellow_deployable_landing", (.055, .055, .005),
            PANEL_PARKED, [0.92, 0.73, 0.12, 1], "kinematic",
        )
        self.handle_offset = (0, -.049, .021)
        self.handle = _box(
            self.scene, "landing_handle", (.014, .010, .014),
            tuple(PANEL_PARKED[i] + self.handle_offset[i] for i in range(3)),
            [0.34, 0.31, 0.18, 1], "kinematic",
        )
        self.support_actor = self.prerequisite

    def _initialize_episode(self, env_idx: torch.Tensor, options: dict):
        self.table_scene.initialize(env_idx)
        self._terminal_window.clear()
        self.blue.set_pose(sapien.Pose(p=[*BLUE_START, self.goal_spec.cube_half]))
        self.decoy.set_pose(sapien.Pose(p=DECOY_START))
        if self.mechanism == "access_gate":
            pose = GATE_CLOSED if self.start_state == "blocked" else GATE_OPEN
        else:
            pose = PANEL_PARKED if self.start_state == "blocked" else PANEL_DEPLOYED
        self.set_prerequisite_pose(pose)

    def set_prerequisite_pose(self, center):
        self.prerequisite.set_pose(sapien.Pose(p=center))
        self.handle.set_pose(sapien.Pose(p=tuple(
            center[i] + self.handle_offset[i] for i in range(3))))

    def terminal_sample(self):
        contacts = self.scene.get_contacts()
        blue = self.blue._bodies[0].entity
        support = self.support_actor._bodies[0].entity
        impulse = sapien_utils.get_pairwise_contact_impulse(contacts, blue, support)
        support_name = "box_floor" if self.mechanism == "access_gate" else "landing_panel"
        supported = bool(float(impulse[2]) > 1e-6)
        robot_touch = any(
            float(np.linalg.norm(sapien_utils.get_pairwise_contact_impulse(
                contacts, blue, link._bodies[0].entity))) > 1e-6
            for link in self.agent.robot.get_links()
        )
        other_support = False
        for actor in list(self.static_parts.values()) + [self.decoy, self.prerequisite, self.handle]:
            if actor is self.support_actor:
                continue
            other_impulse = sapien_utils.get_pairwise_contact_impulse(
                contacts, blue, actor._bodies[0].entity)
            if float(other_impulse[2]) > 1e-6:
                other_support = True
                break
        qpos = self.agent.robot.get_qpos()[0].detach().cpu().numpy()
        return {
            "time_s": float(self.elapsed_steps[0]) / 30,
            "cube_center": self.blue.pose.p[0].detach().cpu().numpy().tolist(),
            "cube_quaternion_wxyz": self.blue.pose.q[0].detach().cpu().numpy().tolist(),
            "support_contact": support_name if supported else None,
            "other_support_contact": other_support,
            "gripper_open": bool(np.min(qpos[-2:]) > .035),
            "gripper_touching_cube": robot_touch,
            "linear_speed_mps": float(torch.linalg.norm(self.blue.linear_velocity[0])),
            "angular_speed_radps": float(torch.linalg.norm(self.blue.angular_velocity[0])),
        }

    def evaluate(self):
        sample = self.terminal_sample()
        if self._terminal_window and sample["time_s"] <= self._terminal_window[-1]["time_s"]:
            self._terminal_window.pop()
        self._terminal_window.append(sample)
        result = evaluate_terminal(list(self._terminal_window), self.goal_spec)
        return {"success": torch.tensor([result["success"]], device=self.device)}

    def compute_dense_reward(self, obs, action, info):
        return info["success"].float()


def make_env(mechanism, start_state):
    import gymnasium as gym

    return gym.make(
        "FreshPrerequisite-v1", mechanism=mechanism, start_state=start_state,
        obs_mode="state", render_mode="rgb_array", sim_backend="cpu",
        render_backend="cpu", num_envs=1, control_mode="pd_joint_pos",
        reward_mode="sparse", sim_config={"sim_freq": 120, "control_freq": 30},
    )

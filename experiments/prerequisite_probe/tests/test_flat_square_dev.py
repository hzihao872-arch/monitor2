"""Contract tests for the flat square development candidate."""

import math
import unittest

from experiments.prerequisite_probe.flat_square_dev import (
    FlatSquareSpec,
    INSTRUCTION,
    evaluate_terminal,
    search_static_unchanged_red,
)


SPEC = FlatSquareSpec()


def sample(x=0.0, y=0.0, z=0.023, *, yaw=0.0, tilt=0.0,
           table=True, other=False, open_gripper=True, gripper_touch=False,
           speed=0.0, angular_speed=0.0, time=0.0):
    # Quaternion is w, x, y, z. A face must rest on the table.
    cy, sy = math.cos(yaw / 2), math.sin(yaw / 2)
    ct, st = math.cos(tilt / 2), math.sin(tilt / 2)
    return {
        "time_s": time,
        "blue_position": [SPEC.target_x + x, SPEC.target_y + y, z],
        "blue_quaternion_wxyz": [cy * ct, cy * st, sy * st, sy * ct],
        "blue_linear_speed_mps": speed,
        "blue_angular_speed_radps": angular_speed,
        "table_support_contact": table,
        "other_support_contact": other,
        "gripper_open": open_gripper,
        "gripper_touching_blue": gripper_touch,
    }


def window(**kwargs):
    return [sample(time=t, **kwargs) for t in (0.0, 0.25, 0.5)]


class TerminalPredicateTests(unittest.TestCase):
    def test_approved_v2_goal_and_protocol_are_used(self):
        self.assertEqual(SPEC.protocol, "flat_square_dev_v2")
        self.assertEqual(
            INSTRUCTION,
            "Place the blue cube entirely inside the single green square with one whole face flat against the tabletop. Open the gripper and move it clear, then let the cube settle and stay still.",
        )

    def test_centered_and_offset_flat_table_placements_pass(self):
        self.assertTrue(evaluate_terminal(window(), SPEC)["success"])
        self.assertTrue(evaluate_terminal(window(x=0.005, yaw=0.04), SPEC)["success"])

    def test_rejects_partial_boundary_crossing(self):
        self.assertFalse(evaluate_terminal(window(x=0.009), SPEC)["success"])

    def test_submillimetre_boundary_noise_is_tolerated(self):
        self.assertTrue(evaluate_terminal(window(x=0.0072), SPEC)["success"])

    def test_rejects_stack_on_red_even_if_center_inside(self):
        self.assertFalse(evaluate_terminal(window(z=0.059, table=False, other=True), SPEC)["success"])

    def test_rejects_tilt_and_edge_support(self):
        self.assertFalse(evaluate_terminal(window(tilt=0.12), SPEC)["success"])

    def test_rejects_held_cube(self):
        self.assertFalse(evaluate_terminal(window(open_gripper=False, gripper_touch=True), SPEC)["success"])

    def test_rejects_sliding_out_after_initially_inside(self):
        states = window()
        states[-1] = sample(x=0.009, speed=0.03, time=0.5)
        self.assertFalse(evaluate_terminal(states, SPEC)["success"])

    def test_rejects_motion_that_remains_inside_square(self):
        states = [sample(time=0.0), sample(x=0.002, time=0.25), sample(x=0.004, time=0.5)]
        result = evaluate_terminal(states, SPEC)
        self.assertFalse(result["success"])
        self.assertIn("window_displacement", result["reasons"])

    def test_rejects_centered_cube_without_table_support(self):
        self.assertFalse(evaluate_terminal(window(table=False), SPEC)["success"])

    def test_red_position_is_not_a_predicate_input(self):
        self.assertNotIn("red_position", sample())
        self.assertTrue(evaluate_terminal(window(), SPEC)["success"])


class StaticChallengeTests(unittest.TestCase):
    def test_blocked_flat_square_has_no_unchanged_red_placement(self):
        result = search_static_unchanged_red(SPEC)
        self.assertGreater(result["full_footprint_candidates"], 0)
        self.assertEqual(result["non_colliding_supported_candidates"], 0)

    def test_open_square_has_table_supported_placements(self):
        result = search_static_unchanged_red(SPEC, red_present=False)
        self.assertGreater(result["non_colliding_supported_candidates"], 0)

    def test_search_grid_covers_tolerated_boundary_poses(self):
        result = search_static_unchanged_red(SPEC)
        self.assertGreaterEqual(
            result["searched_center_max_abs_m"],
            SPEC.square_inner_half + SPEC.footprint_tolerance - SPEC.blue_half,
        )


class RouteChallengeTests(unittest.TestCase):
    def test_direct_place_challenge_moves_only_the_blue_cube(self):
        from experiments.prerequisite_probe.flat_square_route_challenge import direct_place_spec

        route = direct_place_spec()
        self.assertEqual(route["object"], "blue")
        self.assertEqual(route["destination_xy"], (SPEC.target_x, SPEC.target_y))
        self.assertEqual(route["destination_z"], SPEC.blue_half + 0.015)

    def test_lateral_sweep_keeps_blue_held_during_red_contact_opportunity(self):
        from experiments.prerequisite_probe.flat_square_route_challenge import lateral_sweep_waypoints

        points = lateral_sweep_waypoints()
        low_held = [(t, xyz) for t, xyz, grip in points
                    if xyz is not None and xyz[2] < 0.03 and grip == -1.0]
        self.assertEqual(low_held[-2][1][:2], (SPEC.target_x - 0.06, SPEC.target_y))
        self.assertEqual(low_held[-1][1][:2], (SPEC.target_x, SPEC.target_y))

    def test_preparation_moves_red_outside_target_without_commanding_blue(self):
        from experiments.prerequisite_probe.flat_square_operational_check import red_prep_spec

        prep = red_prep_spec()
        self.assertEqual(prep["object"], "red")
        self.assertEqual(prep["destination_xy"], (0.02, 0.18))
        self.assertEqual(prep["destination_z"], SPEC.red_half)

    def test_source_open_route_uses_calibrated_drop_target(self):
        from experiments.prerequisite_probe.flat_square_route_challenge import source_direct_spec

        route = source_direct_spec()
        self.assertEqual(route["object"], "blue")
        self.assertEqual(route["destination_xy"], (0.19, SPEC.target_y))

    def test_source_lid_push_route_sweeps_across_lid_without_blue_command(self):
        from experiments.prerequisite_probe.flat_square_route_challenge import source_lid_push_waypoints

        points = source_lid_push_waypoints()
        low = [(xyz, grip) for _, xyz, grip in points if xyz is not None and xyz[2] < 0.09]
        self.assertEqual(low[0][0][0], -0.18)
        self.assertEqual(low[-1][0][0], 0.12)
        self.assertTrue(all(grip == 1.0 for _, grip in low))

    def test_two_stage_lid_push_has_low_tabletop_clearance_sweep(self):
        from experiments.prerequisite_probe.flat_square_route_challenge import source_lid_two_stage_waypoints

        points = source_lid_two_stage_waypoints()
        low_table = [xyz for _, xyz, _ in points if xyz is not None and xyz[2] < 0.03]
        self.assertEqual(low_table[0][:2], (0.05, -0.17))
        self.assertEqual(low_table[-1][:2], (0.05, 0.08))

    def test_source_fixed_pick_continuation_uses_cage_center(self):
        from experiments.prerequisite_probe.flat_square_route_challenge import source_fixed_blue_waypoints

        points = source_fixed_blue_waypoints()
        low_pick = [xyz for _, xyz, grip in points
                    if xyz is not None and xyz[2] < 0.03 and xyz[0] < 0 and grip == 1.0]
        self.assertTrue(low_pick)
        self.assertTrue(all(xyz[:2] == (-0.08, -0.07) for xyz in low_pick))

    def test_source_cage_openings_are_smaller_than_cube_width(self):
        from experiments.prerequisite_probe.source_lid_scene import source_cage_geometry_bound

        bound = source_cage_geometry_bound()
        self.assertLess(bound["maximum_top_aperture_m"], bound["blue_minimum_caliper_width_m"])
        self.assertLessEqual(bound["lid_bottom_z_m"], bound["wall_top_z_m"] + 1e-9)
        self.assertLess(bound["peripheral_slit_m"], bound["blue_minimum_caliper_width_m"])


class SimulatorPrototypeTests(unittest.TestCase):
    def test_source_lid_handle_variant_can_lift_open_lid(self):
        from experiments.prerequisite_probe.distractor_scenes import make_source_with_handle
        from experiments.prerequisite_probe.source_lid_reblock_search import handle_pick_waypoints
        from experiments.prerequisite_probe.flat_square_route_challenge import build_waypoint_keyframes
        from experiments.prerequisite_probe.probe import FPS, PandaIK
        from experiments.prerequisite_probe.produce import action_at

        env = make_source_with_handle("open")
        try:
            env.reset(seed=20261005)
            keyframes, _ = build_waypoint_keyframes(env, PandaIK(), handle_pick_waypoints())
            for step in range(1, 7 * FPS):
                env.step(action_at(step / FPS, keyframes))
            self.assertGreater(float(env.unwrapped.red.pose.p[0, 2]), 0.08)
        finally:
            env.close()

    def test_final_scene_variants_add_same_irrelevant_yellow_object(self):
        from experiments.prerequisite_probe.distractor_scenes import (
            YELLOW_START_XY,
            make_flat_with_distractor,
            make_source_with_distractor,
        )

        for factory in (make_flat_with_distractor, make_source_with_distractor):
            env = factory("blocked")
            try:
                env.reset(seed=20261005)
                yellow = env.unwrapped.yellow.pose.p[0].cpu().numpy()
                self.assertAlmostEqual(yellow[0], YELLOW_START_XY[0], places=5)
                self.assertAlmostEqual(yellow[1], YELLOW_START_XY[1], places=5)
                self.assertGreater(math.dist(yellow[:2], (SPEC.target_x, SPEC.target_y)), 0.20)
                self.assertEqual(env.render().cpu().numpy()[0].shape, (480, 640, 3))
            finally:
                env.close()

    def test_single_robot_link_contact_counts_as_unreleased(self):
        from experiments.prerequisite_probe.flat_square_scene import any_robot_contact

        self.assertTrue(any_robot_contact([(0, 0, 0), (0.0, 0.002, 0.0)]))
        self.assertFalse(any_robot_contact([(0, 0, 0), (0.0, 0.0, 0.0)]))

    def test_blocked_and_open_preview_use_the_same_main_camera(self):
        from experiments.prerequisite_probe.flat_square_scene import make_flat_env

        poses = []
        for start in ("blocked", "open"):
            env = make_flat_env(start)
            try:
                env.reset(seed=20261005)
                frame = env.render().cpu().numpy()[0]
                self.assertEqual(frame.shape, (480, 640, 3))
                red = env.unwrapped.red.pose.p[0].cpu().numpy()
                poses.append(red)
            finally:
                env.close()
        self.assertAlmostEqual(poses[0][0], SPEC.target_x, places=5)
        self.assertAlmostEqual(poses[0][1], SPEC.target_y, places=5)
        self.assertGreater(math.dist(poses[0][:2], poses[1][:2]), 0.08)

    def test_open_scene_accepts_released_stable_table_placement(self):
        import numpy as np
        import sapien
        from experiments.prerequisite_probe.flat_square_scene import make_flat_env

        env = make_flat_env("open")
        try:
            env.reset(seed=20261005)
            env.unwrapped.blue.set_pose(sapien.Pose(p=[SPEC.target_x, SPEC.target_y, SPEC.blue_half]))
            qpos = env.unwrapped.agent.robot.get_qpos()[0, :7].cpu().numpy()
            action = np.r_[qpos, 1.0].astype(np.float32)
            successes = []
            for _ in range(30):
                _, _, _, _, info = env.step(action)
                successes.append(bool(info["success"][0]))
            self.assertTrue(successes[-1])
        finally:
            env.close()

    def test_source_lid_candidate_changes_source_access_relation(self):
        from experiments.prerequisite_probe.source_lid_scene import make_source_lid_env

        poses = []
        for start in ("blocked", "open"):
            env = make_source_lid_env(start)
            try:
                env.reset(seed=20261005)
                frame = env.render().cpu().numpy()[0]
                self.assertEqual(frame.shape, (480, 640, 3))
                poses.append(env.unwrapped.red.pose.p[0].cpu().numpy())
            finally:
                env.close()
        self.assertAlmostEqual(poses[0][0], -0.08, places=5)
        self.assertAlmostEqual(poses[0][1], -0.07, places=5)
        self.assertGreater(math.dist(poses[0][:2], poses[1][:2]), 0.08)

    def test_open_source_lid_scene_can_evaluate_flat_goal(self):
        import numpy as np
        import sapien
        from experiments.prerequisite_probe.source_lid_scene import make_source_lid_env

        env = make_source_lid_env("open")
        try:
            env.reset(seed=20261005)
            env.unwrapped.blue.set_pose(sapien.Pose(p=[SPEC.target_x, SPEC.target_y, SPEC.blue_half]))
            qpos = env.unwrapped.agent.robot.get_qpos()[0, :7].cpu().numpy()
            action = np.r_[qpos, 1.0].astype(np.float32)
            for _ in range(30):
                _, _, _, _, info = env.step(action)
            self.assertTrue(bool(info["success"][0]))
        finally:
            env.close()


if __name__ == "__main__":
    unittest.main()

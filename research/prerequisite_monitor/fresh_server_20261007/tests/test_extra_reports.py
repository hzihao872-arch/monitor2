import unittest

from extra_reports import compare_p2, p3_cell


class ExtraReportTests(unittest.TestCase):
    def test_p2_keeps_point_differences_and_flip(self):
        first = {"cells": {"access_gate": {"TOPReward": {
            "by_condition": {"E": {"status": "valid", "points_t0_t14": [1] * 15, "delta_window": 1}},
            "pairs": {"E>S": {"outcome": "win"}}}}}}
        second = {"cells": {"access_gate": {"TOPReward": {
            "by_condition": {"E": {"status": "valid", "points_t0_t14": [2] * 15, "delta_window": 2}},
            "pairs": {"E>S": {"outcome": "loss"}}}}}}
        report = compare_p2(first, second)
        cell = report["cells"]["access_gate"]["TOPReward"]
        self.assertEqual(cell["by_condition"]["E"]["point_difference_repeat_minus_first"], [1] * 15)
        self.assertTrue(cell["pairs"]["E>S"]["direction_flipped"])

    def test_p3_uses_t14_only(self):
        aliases = {"0001.mp4": "N_b", "0002.mp4": "S", "0003.mp4": "N_o", "0004.mp4": "G"}
        rows = [{"kind": "native_result", "video": video, "prefix_rewards": [0] * 14 + [value]}
                for video, value in zip(aliases, (0, 1, 2, 3))]
        report = p3_cell(rows, aliases, "TOPReward")
        self.assertEqual(report["comparisons_t14"]["S-N_b"]["difference"], 1)
        self.assertEqual(report["comparisons_t14"]["G-N_o"]["difference"], 1)


if __name__ == "__main__":
    unittest.main()

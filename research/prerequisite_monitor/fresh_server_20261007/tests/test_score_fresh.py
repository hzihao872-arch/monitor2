import unittest

from score_fresh_batch import score_method


CONDITIONS = ("E", "S", "I_b", "N_b", "R", "H", "I_o", "N_o", "G")
MAPPING = {f"{i:04}.mp4": condition for i, condition in enumerate(CONDITIONS, 1)}


class ScoreFreshTests(unittest.TestCase):
    def rows(self):
        rows = []
        for video, condition in MAPPING.items():
            value = {"E": 3, "S": 1, "I_b": 0, "N_b": 0, "R": 0,
                     "H": -2, "I_o": 0, "N_o": 0, "G": 4}[condition]
            curve = [0.0] * 12 + [float(value)] * 3
            if condition == "R":
                curve[7:9] = [2.0, 2.0]
            rows.append({"kind": "native_result", "video": video, "progress": curve,
                         "success_head": [0.0] * 14 + [0.9]})
        return rows

    def test_six_prespecified_differences_and_r(self):
        result = score_method(self.rows(), MAPPING, "Robometer")
        self.assertEqual([x["outcome"] for x in result["pairs"].values()], ["win"] * 6)
        self.assertEqual(result["pairs"]["E>S"]["difference"], 2.0)
        self.assertEqual(result["by_condition"]["R"]["t7_t8"], [2.0, 2.0])
        self.assertEqual(result["by_condition"]["R"]["end_median_t12_t14"], 0.0)
        self.assertEqual(result["by_condition"]["G"]["success_head_t14"], 0.9)

    def test_exact_zero_is_tie(self):
        rows = self.rows()
        rows[1]["progress"] = rows[0]["progress"].copy()
        result = score_method(rows, MAPPING, "Robometer")
        self.assertEqual(result["pairs"]["E>S"]["outcome"], "tie")

    def test_failure_makes_affected_pairs_unavailable(self):
        rows = self.rows()
        rows[0] = {"kind": "native_failure", "video": "0001.mp4", "error": "OOM"}
        result = score_method(rows, MAPPING, "Robometer")
        self.assertEqual(result["by_condition"]["E"]["status"], "failed")
        self.assertEqual(result["pairs"]["E>S"]["outcome"], "unavailable")
        self.assertEqual(result["pairs"]["G>N_o"]["outcome"], "win")

    def test_nonfinite_is_unscorable(self):
        rows = self.rows()
        rows[0]["progress"][0] = float("nan")
        result = score_method(rows, MAPPING, "Robometer")
        self.assertEqual(result["by_condition"]["E"]["status"], "invalid")


if __name__ == "__main__":
    unittest.main()

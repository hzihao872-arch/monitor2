"""Native baseline scorer preserves missing clips as runtime failures."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path


class NativeNewScoreTests(unittest.TestCase):
    def test_missing_native_output_is_reported_without_dropping_video(self):
        from experiments.prerequisite_probe.score_native_new import score_scene

        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / "scene"
            truth = root / "truth"
            truth.mkdir(parents=True)
            cases = {f"{i:04d}": {"condition": case}
                     for i, case in enumerate(("B+", "B0", "U0", "H-", "G+", "N0"), 1)}
            frozen = truth / "frozen_test.json"
            frozen.write_text(json.dumps({"scene_family": "synthetic", "cases": cases}))
            (truth / "frozen_test.sha256").write_text(
                hashlib.sha256(frozen.read_bytes()).hexdigest() + "\n")
            top = base / "s01.topreward"
            top.mkdir()
            (top / "0001.json").write_text(json.dumps({
                "prefix_lengths": list(range(1, 16)), "prefix_rewards": list(range(15)),
                "instruction": "Put the blue cube in the green tray."}))
            report = score_scene(root, top, base / "s01.robometer_pr33_compat")
            self.assertEqual(report["TOPReward"]["videos"]["B+"]["status"], "valid")
            self.assertEqual(report["TOPReward"]["videos"]["B0"]["status"], "missing")
            self.assertEqual(report["Robometer PR33 dtype compat"]["counts"]["missing"], 6)
            self.assertIsNone(report["TOPReward"]["pairwise"]["Bplus_vs_B0_delta"])


if __name__ == "__main__":
    unittest.main()

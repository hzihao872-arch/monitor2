"""Boundary tests for the first causal rescue batch."""

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "research/prerequisite_monitor/development/scene_video_next/flat_red_only_six_candidate_v1/model_input"
DESIGN = ROOT / "research/prerequisite_monitor/development/architecture_next/causal_rescue_20261006/design.json"


class CausalRescueInputTests(unittest.TestCase):
    def test_builder_preserves_six_videos_and_90_pixels(self):
        from experiments.prerequisite_probe.build_causal_rescue_inputs import build_arm, verify_arm

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for arm in ("L1", "L2"):
                built = build_arm(SOURCE, DESIGN, root / arm, arm)
                report = verify_arm(SOURCE, DESIGN, root / arm, arm)
                self.assertEqual(report["video_count"], 6)
                self.assertEqual(report["decoded_pixel_count"], 90)
                self.assertEqual(report["status"], "pass")
                self.assertEqual(built["zip_sha256"], hashlib.sha256((root / arm / "model_input.zip").read_bytes()).hexdigest())
                rows = [json.loads(line) for line in (root / arm / "model_input/manifest.jsonl").read_text().splitlines()]
                self.assertEqual(len({row["instruction"] for row in rows}), 1)
                self.assertEqual(rows[0]["instruction"], json.loads(DESIGN.read_text())["arms"][arm]["instruction"])
                for row in rows:
                    self.assertEqual((root / arm / "model_input" / row["video"]).read_bytes(), (SOURCE / row["video"]).read_bytes())
                with zipfile.ZipFile(root / arm / "model_input.zip") as archive:
                    self.assertEqual(sorted(archive.namelist()), sorted(["instruction.txt", "manifest.jsonl", "media_hashes.json"] + [f"{i:04}.mp4" for i in range(1, 7)]))

    def test_rejects_source_with_truth_or_extra_file(self):
        from experiments.prerequisite_probe.build_causal_rescue_inputs import build_arm

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "model_input"
            source.mkdir()
            for path in SOURCE.iterdir():
                (source / path.name).write_bytes(path.read_bytes())
            (source / "truth.json").write_text("{}")
            with self.assertRaises(ValueError):
                build_arm(source, DESIGN, root / "out", "L1")


if __name__ == "__main__":
    unittest.main()

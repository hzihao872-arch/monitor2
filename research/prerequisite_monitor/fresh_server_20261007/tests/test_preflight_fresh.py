import unittest
from pathlib import Path

from model_side.pilot_pkg.preflight_fresh_server import inspect_input_zip


ROOT = Path(__file__).resolve().parents[2] / "fresh_scenes_20261006"


class PreflightFreshTests(unittest.TestCase):
    def test_each_frozen_zip_has_nine_anonymous_videos(self):
        for arm in ("access_gate", "support_surface"):
            with self.subTest(arm=arm):
                result = inspect_input_zip(ROOT / arm / "dev_v2" / "model_input.zip")
                self.assertEqual(result["video_count"], 9)
                self.assertEqual(result["pixel_hash_count"], 135)
                self.assertEqual(len(result["video_sha256"]), 9)


if __name__ == "__main__":
    unittest.main()

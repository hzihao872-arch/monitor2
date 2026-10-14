import json
import unittest
from pathlib import Path

from model_side.pilot_pkg.precheck_native_decoder import check_video


WORKSPACE = Path(__file__).resolve().parents[4]


class NativeDecoderPrecheckTests(unittest.TestCase):
    def test_one_frozen_clip_matches_robometer_native_decoder(self):
        inp = WORKSPACE / "research/prerequisite_monitor/fresh_scenes_20261006/access_gate/dev_v2/model_input"
        media = json.loads((inp / "media_hashes.json").read_text())
        expected = media["clips"][0]["decoded_rgb_sha256"]
        result = check_video(inp / "0001.mp4", expected,
                             WORKSPACE / "research/sources/robometer/scripts/example_inference_local.py",
                             WORKSPACE / ".venv-robometer/Scripts/python.exe",
                             WORKSPACE / "research/sources/robometer", decoder_mode="extract_only")
        self.assertTrue(result["match"], result)
        self.assertEqual(result["frame_count"], 15)


if __name__ == "__main__":
    unittest.main()

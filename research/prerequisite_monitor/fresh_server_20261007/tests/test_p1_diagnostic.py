import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from optional.p1_qwen import run


ROOT = Path(__file__).resolve().parents[2] / "fresh_scenes_20261006"


class P1DiagnosticTests(unittest.TestCase):
    def test_dry_run_has_two_arms_nine_legal_frames_and_no_model_calls(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "dry.jsonl"
            run(Namespace(access_input=ROOT / "access_gate/dev_v2/model_input",
                          support_input=ROOT / "support_surface/dev_v2/model_input",
                          model_path=Path(temp), output=output, stage="visual", dry_run=True,
                          limit_per_arm=1, pilot=False))
            rows = [json.loads(line) for line in output.read_text().splitlines()]
            self.assertEqual(len([r for r in rows if r["kind"] == "video_input"]), 2)
            self.assertEqual(len([r for r in rows if r["kind"] == "model_output"]), 0)
            self.assertEqual(rows[1]["frame_seconds"], [0, 2, 4, 6, 7, 8, 10, 12, 14])
            self.assertEqual(len(rows[1]["frame_sha256"]), 9)


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path

from optional.seal_p1 import summarize


class SealP1Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.calls = self.root / "raw" / "calls.jsonl"
        self.calls.parent.mkdir()
        self.rows = [{"kind": "configuration", "stage": "visual"}]
        for arm in ("access_gate", "support_surface"):
            self.rows.append({"kind": "video_input", "arm": arm, "video": "0001.mp4", "video_sha256": "hash",
                              "frame_seconds": [0, 2, 4, 6, 7, 8, 10, 12, 14], "frame_sha256": ["hash"] * 9})
            self.rows.append({"kind": "model_output", "arm": arm, "video": "0001.mp4", "raw": "{}", "parse_status": "invalid"})

    def write(self):
        self.calls.write_text("".join(json.dumps(x) + "\n" for x in self.rows))

    def test_complete_pilot_keeps_invalid_parse_as_raw_result(self):
        self.write()
        self.assertEqual(summarize(self.calls, expected_count=2)["status"], "complete")

    def test_duplicate_outcome_is_incomplete(self):
        self.rows.append(self.rows[-1].copy())
        self.write()
        self.assertEqual(summarize(self.calls, expected_count=2)["status"], "incomplete")

    def test_failure_is_kept(self):
        self.rows[-1] = {"kind": "model_failure", "arm": "support_surface", "video": "0001.mp4", "error": "OOM"}
        self.write()
        self.assertEqual(summarize(self.calls, expected_count=2)["status"], "complete_with_failures")

    def test_one_arm_missing_is_incomplete(self):
        self.rows[-2]["arm"] = "access_gate"
        self.rows[-2]["video"] = "0002.mp4"
        self.rows[-1]["arm"] = "access_gate"
        self.rows[-1]["video"] = "0002.mp4"
        self.write()
        self.assertEqual(summarize(self.calls, expected_count=2)["status"], "incomplete")


if __name__ == "__main__":
    unittest.main()

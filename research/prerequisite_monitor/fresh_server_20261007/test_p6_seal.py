"""Synthetic journal checks for the P6 raw seal; no model or truth access."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from p6pkg.seal import seal, summarize, verify
from score_p6_direct import score

ROOT = Path(__file__).resolve().parent
SCENES = ROOT.parent / "fresh_scenes_20261006"
INPUTS = {arm: SCENES / arm / "dev_v2" / "model_input" for arm in ("access_gate", "support_surface")}


class SealChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw = self.root / "raw"
        self.raw.mkdir()
        rows = [json.loads(line) for line in (ROOT / "p6_dry_run.jsonl").read_text(encoding="utf-8").splitlines()]
        rows[0]["dry_run"] = False
        video_inputs = [item for item in rows if item["kind"] == "video_input"]
        rows.extend({"kind": "model_output", "arm": item["arm"], "video": item["video"],
                     "raw": '{"label":"unchanged","reason":"test","evidence_seconds":[0,14],"uncertainty":""}',
                     "parse_status": "valid", "parsed": {"label": "unchanged", "reason": "test",
                                                       "evidence_seconds": [0, 14], "uncertainty": ""}}
                    for item in video_inputs)
        self.rows = rows
        self.write()

    def write(self):
        (self.raw / "calls.jsonl").write_text("\n".join(json.dumps(row) for row in self.rows) + "\n", encoding="utf-8")

    def test_complete_and_verify(self):
        path = self.root / "seal.json"
        self.assertEqual(seal(self.raw, path, 18, INPUTS)["status"], "complete")
        self.assertEqual(verify(self.raw, path, 18, INPUTS)["result_count"], 18)
        scored = score(self.raw, path, INPUTS, SCENES)
        self.assertEqual(scored["counts"]["access_gate"]["label_match"], 6)
        self.assertEqual(scored["counts"]["support_surface"]["label_match"], 6)
        with (self.raw / "calls.jsonl").open("a", encoding="utf-8") as stream:
            stream.write("\n")
        with self.assertRaisesRegex(ValueError, "SHA changed"):
            verify(self.raw, path, 18, INPUTS)

    def test_missing_duplicate_and_prompt_change(self):
        self.rows.pop()
        self.write()
        self.assertEqual(summarize(self.raw / "calls.jsonl", 18, INPUTS)["status"], "incomplete")
        self.rows.append(dict(self.rows[-1]))
        self.write()
        self.assertEqual(summarize(self.raw / "calls.jsonl", 18, INPUTS)["status"], "incomplete")
        self.rows[-1]["video"] = "0009.mp4"
        self.rows[1]["prompt_sha256"] = "0" * 64
        self.write()
        self.assertIn("video, frame, or prompt SHA differs", summarize(self.raw / "calls.jsonl", 18, INPUTS)["issues"])


if __name__ == "__main__":
    unittest.main()

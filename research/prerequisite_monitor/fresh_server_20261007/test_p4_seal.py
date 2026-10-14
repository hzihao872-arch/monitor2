"""Integrity checks for sealed P4 outcomes using copied, synthetic journals."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from optional.p4_seal import sha256, summarize

HERE = Path(__file__).resolve().parent
P0 = HERE / "local_results" / "p0" / "raw"


class P4SealTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.inputs = {arm: HERE / "p4_inputs" / "neutral" / arm / "model_input"
                       for arm in ("access_gate", "support_surface")}
        for arm, source in self.inputs.items():
            target = self.root / arm / "topreward"
            target.mkdir(parents=True)
            goal = (source / "instruction.txt").read_text(encoding="utf-8").strip()
            original = P0 / arm / "topreward"
            rows = [json.loads(line) for line in (original / "native_calls.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
            for row in rows:
                if row["kind"] == "configuration":
                    row["manifest_sha256"] = sha256(source / "manifest.jsonl")
                elif row["kind"] == "native_result":
                    row["instruction"] = goal
                    file = target / (Path(row["video"]).stem + ".json")
                    payload = json.loads((original / file.name).read_text(encoding="utf-8"))
                    payload["instruction"] = goal
                    file.write_text(json.dumps(payload) + "\n", encoding="utf-8")
                    row["result_sha256"] = sha256(file)
            (target / "native_calls.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_complete_and_missing_result(self) -> None:
        self.assertEqual(summarize(self.root, self.inputs)["status"], "complete")
        journal = self.root / "access_gate" / "topreward" / "native_calls.jsonl"
        rows = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines()]
        rows.remove(next(row for row in rows if row["kind"] == "native_result"))
        journal.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        self.assertEqual(summarize(self.root, self.inputs)["status"], "incomplete")

    def test_duplicate_and_bad_curve(self) -> None:
        journal = self.root / "support_surface" / "topreward" / "native_calls.jsonl"
        rows = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines()]
        result = next(row for row in rows if row["kind"] == "native_result")
        journal.write_text("".join(json.dumps(row) + "\n" for row in rows + [result]), encoding="utf-8")
        self.assertEqual(summarize(self.root, self.inputs)["status"], "incomplete")
        result["prefix_rewards"] = result["prefix_rewards"][:-1]
        journal.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        self.assertEqual(summarize(self.root, self.inputs)["status"], "incomplete")

    def test_result_file_disagrees_with_journal(self) -> None:
        journal = self.root / "access_gate" / "topreward" / "native_calls.jsonl"
        rows = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines()]
        result = next(row for row in rows if row["kind"] == "native_result")
        file = journal.parent / (Path(result["video"]).stem + ".json")
        payload = json.loads(file.read_text(encoding="utf-8"))
        payload["prefix_rewards"][0] += 1
        file.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        result["result_sha256"] = sha256(file)
        journal.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        self.assertEqual(summarize(self.root, self.inputs)["status"], "incomplete")


if __name__ == "__main__":
    unittest.main()

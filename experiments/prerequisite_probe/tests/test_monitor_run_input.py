import hashlib
import json
import tempfile
import unittest
from pathlib import Path


class MonitorRunInputTests(unittest.TestCase):
    def test_common_prompt_distinguishes_goal_from_preparation(self):
        from experiments.prerequisite_probe.run_monitor_qwen import prompt_for

        prompt = prompt_for("P", "Put an object in a container.")
        self.assertIn("final goal fully visibly achieved", prompt)
        self.assertIn("preparatory condition", prompt)
        self.assertIn("An unnamed object can matter physically", prompt)
        self.assertIn("Compare this one relation at the first and last frame", prompt)
        self.assertIn("Never put descriptions in these enum fields", prompt)

    def write_input(self, parent: Path, extra=None):
        directory = parent / "model_input"
        directory.mkdir()
        payload = b"not-a-real-video"
        (directory / "0001.mp4").write_bytes(payload)
        row = {"video": "0001.mp4", "instruction": "Put the blue cube in the green tray.",
               "sha256": hashlib.sha256(payload).hexdigest(), "fps": 1,
               "frame_indices_from_30fps": list(range(0, 450, 30))}
        if extra:
            row.update(extra)
        (directory / "manifest.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
        return directory

    def test_loads_only_numbered_videos_and_instruction(self):
        from experiments.prerequisite_probe.run_monitor_qwen import collect_inputs

        with tempfile.TemporaryDirectory() as temp:
            directory = self.write_input(Path(temp))
            rows = collect_inputs(directory)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["video"], "0001.mp4")
            self.assertEqual(rows[0]["instruction"], "Put the blue cube in the green tray.")

    def test_rejects_hidden_label_in_manifest(self):
        from experiments.prerequisite_probe.run_monitor_qwen import collect_inputs

        with tempfile.TemporaryDirectory() as temp:
            directory = self.write_input(Path(temp), {"condition": "B+"})
            with self.assertRaisesRegex(ValueError, "unexpected manifest fields"):
                collect_inputs(directory)

    def test_rejects_non_model_input_folder(self):
        from experiments.prerequisite_probe.run_monitor_qwen import collect_inputs

        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            directory = self.write_input(parent)
            with self.assertRaisesRegex(ValueError, "model_input"):
                collect_inputs(directory.rename(parent / "truth"))

    def test_rejects_manifest_hash_mismatch(self):
        from experiments.prerequisite_probe.run_monitor_qwen import collect_inputs

        with tempfile.TemporaryDirectory() as temp:
            directory = self.write_input(Path(temp))
            (directory / "0001.mp4").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "sha256 mismatch"):
                collect_inputs(directory)


if __name__ == "__main__":
    unittest.main()

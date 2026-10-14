import json
import tempfile
import unittest
from pathlib import Path

from experiments.prerequisite_probe.fresh_prerequisite.generate import (
    require_empty_output,
    validate_model_manifest_row,
)


class PackageBoundaryTests(unittest.TestCase):
    def test_generator_refuses_nonempty_version_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "dev_v1"
            destination.mkdir()
            (destination / "prior.txt").write_text("frozen", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                require_empty_output(destination)
            self.assertEqual((destination / "prior.txt").read_text(encoding="utf-8"), "frozen")

    def test_manifest_rejects_truth_fields_and_preparation_instruction(self):
        base = {
            "video": "0001.mp4",
            "instruction": "Put the blue cube inside the transparent box.",
            "sha256": "a" * 64,
            "fps": 1,
            "frame_indices_from_30fps": list(range(0, 450, 30)),
        }
        self.assertEqual(validate_model_manifest_row(base), base)
        with self.assertRaises(ValueError):
            validate_model_manifest_row({**base, "condition": "E"})
        with self.assertRaises(ValueError):
            validate_model_manifest_row({**base, "instruction": "Open the door, then put the blue cube inside."})


if __name__ == "__main__":
    unittest.main()

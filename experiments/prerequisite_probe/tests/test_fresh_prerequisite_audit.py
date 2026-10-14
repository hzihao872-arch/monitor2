import tempfile
import unittest
from pathlib import Path

from experiments.prerequisite_probe.fresh_prerequisite.audit import (
    model_input_name_issues, public_manifest_row,
)


class InputIsolationTests(unittest.TestCase):
    def test_native_inspector_decode_metadata_is_not_treated_as_model_manifest(self):
        inspected = {
            "video": "0001.mp4", "instruction": "Place the cube on the landing.",
            "sha256": "a" * 64, "fps": 1,
            "frame_indices_from_30fps": list(range(0, 450, 30)),
            "decoded_pixel_sha256": {"0": "b" * 64},
        }
        public = public_manifest_row(inspected)
        self.assertNotIn("decoded_pixel_sha256", public)
        self.assertEqual(len(public), 5)

    def test_only_anonymous_media_and_fixed_manifests_are_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            for number in range(1, 10):
                (folder / f"{number:04d}.mp4").touch()
            for name in ("manifest.jsonl", "media_hashes.json", "instruction.txt"):
                (folder / name).touch()
            self.assertEqual(model_input_name_issues(folder), [])
            (folder / "truth.json").touch()
            self.assertTrue(model_input_name_issues(folder))


if __name__ == "__main__":
    unittest.main()

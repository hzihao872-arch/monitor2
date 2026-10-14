"""Cloud upload must contain only frozen, label-free input and runner code."""

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


class CloudBundleTests(unittest.TestCase):
    def test_rejects_method_code_drift_after_freeze(self):
        from experiments.prerequisite_probe.prepare_cloud_bundle import create_bundle

        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            frozen = base / "method_freeze.json"
            frozen.write_text(json.dumps({"file_sha256": {
                "experiments/prerequisite_probe/run_monitor_qwen.py": "0" * 64}}))
            frozen.with_suffix(".sha256").write_text(
                hashlib.sha256(frozen.read_bytes()).hexdigest() + "\n")
            with self.assertRaisesRegex(ValueError, "method code hash mismatch"):
                create_bundle([], base / "upload.zip", method_freeze=frozen)

    def test_archive_has_no_truth_and_checks_freeze_hashes(self):
        from experiments.prerequisite_probe.prepare_cloud_bundle import create_bundle

        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            roots = []
            for name in ("candidate_a", "candidate_b"):
                root = base / name
                (root / "model_input").mkdir(parents=True)
                (root / "truth").mkdir()
                video = b"fake-video-" + name.encode()
                video_hash = hashlib.sha256(video).hexdigest()
                (root / "model_input" / "0001.mp4").write_bytes(video)
                row = {"video": "0001.mp4", "instruction": "Put a cube in a tray.",
                       "sha256": video_hash, "fps": 1,
                       "frame_indices_from_30fps": list(range(0, 450, 30))}
                (root / "model_input" / "manifest.jsonl").write_text(json.dumps(row) + "\n")
                freeze = {"cases": {"0001": {"video_sha256": video_hash}}}
                frozen = root / "truth" / "frozen_test.json"
                frozen.write_text(json.dumps(freeze))
                (root / "truth" / "frozen_test.sha256").write_text(
                    hashlib.sha256(frozen.read_bytes()).hexdigest() + "\n")
                (root / "truth" / "secret_labels.json").write_text("DO NOT UPLOAD")
                roots.append(root)
            archive = base / "upload.zip"
            result = create_bundle(roots, archive)
            self.assertEqual(result["video_count"], 2)
            with zipfile.ZipFile(archive) as bundle:
                names = bundle.namelist()
                self.assertTrue(all("truth" not in item and "secret" not in item
                                    for item in names))
                self.assertIn("new_tests/s01/model_input/0001.mp4", names)
                self.assertIn("new_tests/s02/model_input/0001.mp4", names)
                self.assertIn("experiments/prerequisite_probe/run_monitor_qwen.py", names)
                self.assertEqual(bundle.read("new_tests/s01/model_input/0001.mp4"),
                                 b"fake-video-candidate_a")


if __name__ == "__main__":
    unittest.main()

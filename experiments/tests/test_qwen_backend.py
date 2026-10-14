import unittest
import hashlib
import tempfile
from pathlib import Path

from experiments.qwen_backend import compose_messages
from experiments.run_online import validate_media


class QwenMessageTest(unittest.TestCase):
    def test_interleaved_frames_keep_source_times(self):
        frames = [{"time": 0.0, "path": "a.png"}, {"time": 2.0, "path": "b.png"}]
        messages = compose_messages("judge", frames, lambda path: path)
        content = messages[0]["content"]
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual([x["image"] for x in content if x["type"] == "image"], ["a.png", "b.png"])
        self.assertEqual([x["text"] for x in content if x["type"] == "text"], ["judge", "Frame at 0.0 s", "Frame at 2.0 s"])

    def test_media_hash_drift_blocks_model_run(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "frame.png"
            path.write_bytes(b"first")
            track = {"frames": [{"path": str(path), "sha256": hashlib.sha256(b"first").hexdigest()}]}
            validate_media(track)
            path.write_bytes(b"replaced")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                validate_media(track)


if __name__ == "__main__":
    unittest.main()

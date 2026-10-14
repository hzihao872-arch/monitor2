import hashlib
import tempfile
import unittest
from pathlib import Path

from experiments.prerequisite_probe.fresh_prerequisite.freeze import file_inventory


class ManifestTests(unittest.TestCase):
    def test_inventory_hashes_files_without_self_reference(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "data").mkdir()
            (root / "data" / "x.txt").write_bytes(b"evidence")
            (root / "manifest.json").write_text("stale", encoding="utf-8")
            (root / "manifest.sha256").write_text("stale", encoding="utf-8")
            records = file_inventory(root)
            self.assertEqual(set(records), {"data/x.txt"})
            self.assertEqual(records["data/x.txt"]["sha256"], hashlib.sha256(b"evidence").hexdigest())
            self.assertEqual(records["data/x.txt"]["size_bytes"], 8)


if __name__ == "__main__":
    unittest.main()

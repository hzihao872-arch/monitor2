import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from optional.p3_static_pack import generate


FROZEN = Path(__file__).resolve().parents[2] / "fresh_scenes_20261006"


class P3StaticTests(unittest.TestCase):
    def test_eight_anonymous_exact_pixel_static_clips(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "static"
            report = generate(FROZEN, output)
            self.assertEqual(report["clip_count"], 8)
            for arm in ("access_gate", "support_surface"):
                with zipfile.ZipFile(output / arm / "model_input.zip") as archive:
                    names = archive.namelist()
                    self.assertEqual(len(names), 7)
                    self.assertFalse(any("condition" in x or "truth" in x for x in names))
                local_map = json.loads((output / arm / "mapping_local_only.json").read_text())
                self.assertEqual({v["condition"] for v in local_map.values()}, {"N_b", "S", "N_o", "G"})


if __name__ == "__main__":
    unittest.main()

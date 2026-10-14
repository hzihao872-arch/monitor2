import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from model_side.pilot_pkg.smoke_old_input import run


OLD = Path(__file__).resolve().parents[2] / "development" / "architecture_next" / "causal_rescue_20261006" / "first_batch" / "L1" / "model_input"


class OldInputSmokeTests(unittest.TestCase):
    def test_dry_run_selects_one_old_video(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "smoke"
            run(Namespace(input_dir=OLD, output_dir=output, method="TOPReward", repo=Path(temp),
                          model_path=Path(temp), dry_run=True))
            journal = (output / "native_calls.jsonl").read_text()
            self.assertEqual(journal.count('"kind": "video_input"'), 1)


if __name__ == "__main__":
    unittest.main()

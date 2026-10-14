"""Input boundary and media integrity checks for the development pilot."""

import tempfile
import unittest
import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODEL_INPUT = (ROOT / "research/prerequisite_monitor/development/scene_video_next/"
               "flat_red_only_six_candidate_v1/model_input")


class SingleScenePilotRunnerTests(unittest.TestCase):
    def test_only_model_input_and_external_output_are_accepted(self):
        from experiments.prerequisite_probe.run_relation_endpoint_pilot import checked_paths

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "raw.jsonl"
            checked_paths(MODEL_INPUT, output)
            with self.assertRaises(ValueError):
                checked_paths(MODEL_INPUT.parent / "truth", output)
            with self.assertRaises(ValueError):
                checked_paths(MODEL_INPUT, MODEL_INPUT / "raw.jsonl")

    def test_anonymous_input_decodes_to_manifested_pixels(self):
        from experiments.prerequisite_probe.run_relation_endpoint_pilot import inspect_inputs

        rows = inspect_inputs(MODEL_INPUT)
        self.assertEqual(len(rows), 6)
        self.assertEqual({row["video"] for row in rows},
                         {f"{i:04}.mp4" for i in range(1, 7)})
        self.assertTrue(all(len(row["decoded_pixel_sha256"]) == 15 for row in rows))

    def test_native_dry_run_records_six_inputs_without_model(self):
        from experiments.prerequisite_probe.run_native_single_scene_pilot import run

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "native"
            run(argparse.Namespace(method="TOPReward", input_dir=MODEL_INPUT,
                                   output_dir=output, repo=ROOT / "research/sources/TOPReward",
                                   model_path=ROOT / "nonexistent_model", dry_run=True))
            rows = [json.loads(line) for line in (output / "native_calls.jsonl").read_text(
                encoding="utf-8").splitlines()]
            self.assertEqual(sum(row["kind"] == "video_input" for row in rows), 6)
            self.assertEqual(sum(row["kind"] == "native_result" for row in rows), 0)


if __name__ == "__main__":
    unittest.main()

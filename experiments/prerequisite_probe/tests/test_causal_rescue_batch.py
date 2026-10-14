"""First-batch seal and score tests with synthetic native curves."""

import json
import tempfile
import unittest
from pathlib import Path


def put_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def make_raw(raw, failure=False):
    for arm in ("L1", "L2"):
        for method in ("topreward", "robometer"):
            rows = [{"kind": "configuration", "method": method, "arm": arm}]
            rows += [{"kind": "video_input", "video": f"{i:04}.mp4"} for i in range(1, 7)]
            if method == "robometer":
                rows += [{"kind": "native_decoder_probe", "video": f"{i:04}.mp4",
                          "same_pixels_as_manifest": True, "frame_count": 15}
                         for i in range(1, 7)]
            for i in range(1, 7):
                if failure and arm == "L2" and method == "robometer" and i == 6:
                    rows.append({"kind": "native_failure", "video": f"{i:04}.mp4", "error": "fake failure"})
                else:
                    values = [0.0] * 12 + [float(i)] * 3
                    row = {"kind": "native_result", "video": f"{i:04}.mp4", "elapsed_ms": 100}
                    row.update({"prefix_rewards": values} if method == "topreward" else
                               {"progress": values, "success_head": [0.0] * 15})
                    rows.append(row)
            put_jsonl(raw / arm / method / "native_calls.jsonl", rows)


class CausalRescueBatchTests(unittest.TestCase):
    def test_local_scoring_reports_both_deltas_and_failures(self):
        from experiments.prerequisite_probe.seal_causal_rescue_batch import seal
        from experiments.prerequisite_probe.score_causal_rescue_batch import score

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw, seal_path, aliases = root / "raw", root / "seal.json", root / "aliases.json"
            make_raw(raw, failure=True)
            seal(raw, seal_path)
            aliases.write_text(json.dumps({"aliases": [
                {"server_video": f"{i:04}.mp4", "condition": condition}
                for i, condition in enumerate(("B0", "H-", "U0", "N0", "B+", "G+"), 1)]}))
            result = score(raw, seal_path, aliases)
            self.assertEqual(result["arms"]["L1"]["TOPReward"]["by_condition"]["B+"]["delta_window"], 5.0)
            self.assertEqual(result["arms"]["L1"]["TOPReward"]["by_condition"]["B+"]["delta_t14"], 5.0)
            self.assertEqual(result["arms"]["L1"]["TOPReward"]["pairs_window"]["B+>U0"]["outcome"], "win")
            self.assertEqual(result["arms"]["L2"]["Robometer"]["by_condition"]["G+"]["status"], "failed")
            self.assertEqual(result["arms"]["L2"]["Robometer"]["pairs_window"]["G+>N0"]["outcome"], "unavailable")

    def test_preflight_zip_rejects_extra_truth_member(self):
        from experiments.prerequisite_probe.preflight_causal_rescue_server import inspect_input_zip
        from experiments.prerequisite_probe.build_causal_rescue_inputs import SOURCE, DESIGN, build_arm
        import zipfile

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build_arm(SOURCE, DESIGN, root / "L1", "L1")
            good = root / "L1/model_input.zip"
            self.assertEqual(inspect_input_zip(good)["video_count"], 6)
            bad = root / "bad.zip"
            with zipfile.ZipFile(good) as original, zipfile.ZipFile(bad, "w") as modified:
                for name in original.namelist():
                    modified.writestr(name, original.read(name))
                modified.writestr("truth/map.json", "{}")
            with self.assertRaises(ValueError):
                inspect_input_zip(bad)

    def test_seal_requires_six_outcomes_and_detects_tamper(self):
        from experiments.prerequisite_probe.seal_causal_rescue_batch import seal, verify

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw, seal_path = root / "raw", root / "seal.json"
            make_raw(raw, failure=True)
            result = seal(raw, seal_path)
            self.assertEqual(result["status"], "complete_with_failures")
            self.assertEqual(result["total_results"], 23)
            self.assertEqual(result["total_failures"], 1)
            verify(raw, seal_path)
            with (raw / "L1/topreward/native_calls.jsonl").open("a") as stream:
                stream.write("{}\n")
            with self.assertRaises(ValueError):
                verify(raw, seal_path)

    def test_seal_marks_missing_clip_incomplete(self):
        from experiments.prerequisite_probe.seal_causal_rescue_batch import seal

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_raw(root / "raw")
            path = root / "raw/L1/topreward/native_calls.jsonl"
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            put_jsonl(path, [row for row in rows if not (row.get("kind") == "native_result" and row.get("video") == "0006.mp4")])
            self.assertEqual(seal(root / "raw", root / "seal.json")["status"], "incomplete")

    def test_seal_rejects_robometer_pixel_mismatch(self):
        from experiments.prerequisite_probe.seal_causal_rescue_batch import seal

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            make_raw(root / "raw")
            path = root / "raw/L1/robometer/native_calls.jsonl"
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            for row in rows:
                if row.get("kind") == "native_decoder_probe" and row.get("video") == "0002.mp4":
                    row["same_pixels_as_manifest"] = False
            put_jsonl(path, rows)
            self.assertEqual(seal(root / "raw", root / "seal.json")["status"], "incomplete")


if __name__ == "__main__":
    unittest.main()

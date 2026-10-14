"""Synthetic raw results test the seal-before-truth analysis boundary."""

import json
import tempfile
import unittest
from pathlib import Path


CONDITIONS = ("B+", "B0", "U0", "H-", "G+", "N0")
DIRECTIONS = ("positive", "zero", "zero", "negative", "positive", "zero")


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def make_raw(root):
    paired, top, robo, aliases = [], [], [], []
    for i, (condition, direction) in enumerate(zip(CONDITIONS, DIRECTIONS), 1):
        video = f"{i:04}.mp4"
        aliases.append({"server_video": video, "condition": condition})
        for arm in ("D2", "candidate"):
            for pass_number in (1, 2):
                paired.append({"kind": "visual_call", "video": video, "arm": arm,
                               "pass": pass_number, "validity": "valid", "raw": "{}",
                               "record": {}, "input_tokens": 100, "output_tokens": 20,
                               "elapsed_ms": 10})
            paired.append({"kind": "pair_decision", "video": video, "arm": arm,
                           "direction": direction, "reason": "final_record"})
        base = {"B+": 0.5, "B0": 0.1, "U0": 0.0,
                "H-": -0.2, "G+": 1.0, "N0": 0.0}[condition]
        values = [0.0] * 12 + [base] * 3
        top.append({"kind": "native_result", "video": video,
                    "prefix_rewards": values})
        robo.append({"kind": "native_result", "video": video,
                     "progress": values, "success_head": [0.0] * 15})
    write_jsonl(root / "paired.jsonl", paired)
    write_jsonl(root / "topreward/native_calls.jsonl", top)
    write_jsonl(root / "robometer/native_calls.jsonl", robo)
    return aliases


class SingleScenePilotAnalysisTests(unittest.TestCase):
    def test_sealed_synthetic_analysis_and_tamper_rejection(self):
        from experiments.prerequisite_probe.seal_single_scene_pilot import seal, verify
        from experiments.prerequisite_probe.analyze_single_scene_pilot import analyze

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw, seal_path, truth = root / "raw", root / "seal.json", root / "truth.json"
            aliases = make_raw(raw)
            truth.write_text(json.dumps({"aliases": aliases}), encoding="utf-8")
            self.assertEqual(seal(raw, seal_path)["status"], "complete")
            report, packet = analyze(raw, seal_path, truth)
            self.assertEqual(report["TOPReward"]["valid_count"], 6)
            self.assertEqual(report["Robometer_PR33_compat"]["valid_count"], 6)
            self.assertEqual(report["D2"]["budget"]["input_tokens"], 1200)
            self.assertEqual(report["relation_endpoint_v1"]["pairwise"]["B+>B0"]["outcome"], "win")
            self.assertEqual(len(packet), 12)
            with (raw / "paired.jsonl").open("a", encoding="utf-8") as stream:
                stream.write("{}\n")
            with self.assertRaises(ValueError):
                verify(raw, seal_path)

    def test_optional_fact_probe_is_hashed_and_not_called_native_trace(self):
        from experiments.prerequisite_probe.analyze_semantic_checkpoint_probe import analyze
        from experiments.prerequisite_probe.run_monitor_qwen import sha256

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            probe, truth = root / "probe.jsonl", root / "aliases.json"
            aliases = [{"server_video": f"{i:04}.mp4", "condition": condition}
                       for i, condition in enumerate(CONDITIONS, 1)]
            truth.write_text(json.dumps({"aliases": aliases}), encoding="utf-8")
            rows = []
            for alias in aliases:
                record = {"goal_object": "blue cube", "other_object": "red cube",
                          "goal_region": "green square", "other_at_0": "unknown",
                          "other_at_14": "unknown", "returned": "unknown",
                          "goal_at_0": "outside", "goal_at_14": "outside",
                          "complete_at_14": "false", "missing_visual_evidence": "none",
                          "evidence": [{"second": 0}, {"second": 14}]}
                rows.append({"kind": "fact_probe", "video": alias["server_video"],
                             "raw": json.dumps(record)})
            write_jsonl(probe, rows)
            result = analyze(probe, sha256(probe), truth)
            self.assertTrue(result["not_native_topreward_or_robometer_trace"])
            self.assertEqual(len(result["by_condition"]), 6)
            with self.assertRaises(ValueError):
                analyze(probe, "0" * 64, truth)


if __name__ == "__main__":
    unittest.main()

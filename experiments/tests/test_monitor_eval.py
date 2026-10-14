import json
import tempfile
import unittest
from pathlib import Path

from experiments.monitor_eval import (
    Budget,
    frame_packet,
    instruction_at,
    load_online_track,
    parse_output,
    run_track,
    score_bcy,
    score_event_delay,
    score_tick_metrics,
    build_prompt,
)


class ProtocolSemanticsTest(unittest.TestCase):
    def setUp(self):
        self.track = {
            "trajectory_id": "synthetic-01",
            "role": "synthetic_fixture",
            "instruction_versions": [
                {"version": "v1", "effective_at": 0, "text": "Put the cup in the tray."},
                {"version": "v2", "effective_at": 3, "text": "Put the cup in the tray, then move it."},
            ],
            "objects": ["cup_in_tray"],
            "frames": [
                {"time": x, "path": f"frame{x}.png", "sha256": str(x)}
                for x in [0.0, 0.9, 1.0, 2.2, 3.0, 4.4, 5.0, 6.0]
            ],
        }

    def test_online_loader_blocks_reference_and_future_instruction(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "track.json"
            p.write_text(json.dumps({**self.track, "reference_labels": ["secret"]}))
            with self.assertRaises(ValueError):
                load_online_track(p)
            p.write_text(json.dumps(self.track))
            track = load_online_track(p)
            self.assertEqual(instruction_at(track, 2)["version"], "v1")
            self.assertEqual(instruction_at(track, 3)["version"], "v2")

    def test_fixed_packet_uses_only_past_frames_and_deduplicates(self):
        packet = frame_packet(self.track, 4)
        self.assertEqual([f["time"] for f in packet], [3.0, 0.0])
        self.assertTrue(all(f["time"] <= 4 for f in packet))
        self.assertEqual([f["time"] for f in frame_packet(self.track, 0)], [0.0])

    def test_parser_keeps_unknown_and_marks_invalid_object(self):
        raw = json.dumps({"judgments": [
            {"object_id": "cup_in_tray", "H": "+", "C": "?", "P": "?", "G": "?", "evidence_time": 1},
            {"object_id": "not_declared", "H": "+", "C": "+", "P": "+", "G": "+"},
        ], "memory": "seen cup"})
        got = parse_output(raw, ["cup_in_tray"], 2)
        self.assertEqual(got["judgments"]["cup_in_tray"]["C"], "?")
        self.assertEqual(got["memory"], "seen cup")
        self.assertEqual(parse_output("not json", ["cup_in_tray"], 2)["judgments"]["cup_in_tray"]["C"], "⊥")
        future = json.dumps({"judgments": [{"object_id": "cup_in_tray", "H": "+", "C": "+", "P": "+", "G": "+", "evidence_time": 3}]})
        self.assertEqual(parse_output(future, ["cup_in_tray"], 2)["judgments"]["cup_in_tray"]["C"], "⊥")

    def test_bcy_denominators_do_not_reward_abstention(self):
        events = [
            {"event_id": "loss", "trajectory_id": "r", "object_id": "o", "side": "negative", "tv_upper": 2, "visible_intervals": [[2, 4]]},
            {"event_id": "hold", "trajectory_id": "s", "object_id": "o", "side": "positive", "tv_upper": 1, "visible_intervals": [[1, 3]]},
        ]
        records = [
            {"trajectory_id": "r", "tick": 2, "judgments": {"o": {"C": "?"}}},
            {"trajectory_id": "s", "tick": 1, "judgments": {"o": {"C": "+"}}},
        ]
        score = score_bcy(events, records)
        self.assertEqual(score["E_negative"], 1)
        self.assertEqual(score["E_positive"], 1)
        self.assertEqual(score["BCY"], 0.5)
        self.assertEqual(score["Miss0_negative"], 1.0)
        self.assertEqual(score["FC_negative"], 0.0)

    def test_tick_metrics_separate_online_unknown_reference_unknown_and_invalid(self):
        labels = [
            {"trajectory_id": "r", "tick": 0, "object_id": "o", "reference": "+", "online": "+"},
            {"trajectory_id": "r", "tick": 1, "object_id": "o", "reference": "-", "online": "-"},
            {"trajectory_id": "r", "tick": 2, "object_id": "o", "reference": "+", "online": "?"},
            {"trajectory_id": "r", "tick": 3, "object_id": "o", "reference": "?", "online": "?"},
        ]
        outputs = [
            {"trajectory_id": "r", "tick": 0, "judgments": {"o": {"C": "+"}}},
            {"trajectory_id": "r", "tick": 1, "judgments": {"o": {"C": "⊥"}}},
            {"trajectory_id": "r", "tick": 2, "judgments": {"o": {"C": "-"}}},
            {"trajectory_id": "r", "tick": 3, "judgments": {"o": {"C": "+"}}},
        ]
        got = score_tick_metrics(labels, outputs)
        self.assertEqual(got["decidable_denominator"], 2)
        self.assertEqual(got["correct_coverage_numerator"], 1)
        self.assertEqual(got["online_unknown_denominator"], 1)
        self.assertEqual(got["overconfidence_numerator"], 1)
        self.assertEqual(got["reference_unknown_count"], 1)
        self.assertEqual(got["coverage"], 0.5)
        self.assertEqual(got["correct_coverage"], 0.5)
        self.assertEqual(got["selective_error"], 0.0)
        self.assertEqual(got["overconfidence"], 1.0)

    def test_delay_stops_at_occlusion_and_repair(self):
        event = {"event_id": "e", "trajectory_id": "r", "object_id": "o", "side": "negative", "tv_upper": 2, "visible_intervals": [[2, 4], [6, 9]], "repair_time": 7}
        outputs = [
            {"trajectory_id": "r", "tick": t, "judgments": {"o": {"C": value}}}
            for t, value in [(2, "?"), (3, "+"), (4, "-"), (6, "?"), (7, "-")]
        ]
        self.assertEqual(score_event_delay(event, outputs)["status"], "right_censored")
        self.assertEqual(score_event_delay(event, outputs)["observation_end_seconds"], 4.0)
        event["visible_intervals"] = [[2, 8]]
        outputs[2]["judgments"]["o"]["C"] = "?"
        self.assertEqual(score_event_delay(event, outputs)["status"], "repair_competing")
        self.assertEqual(score_event_delay(event, outputs)["observation_end_seconds"], 7.0)
        outputs[1]["judgments"]["o"]["C"] = "-"
        self.assertEqual(score_event_delay(event, outputs)["delay_seconds"], 1)

    def test_repair_before_first_decidable_tick_excludes_event_from_primary_denominator(self):
        event = {"event_id": "early-repair", "trajectory_id": "r", "object_id": "o",
                 "side": "negative", "tv_upper": 2.4,
                 "visible_intervals": [[2.4, 4]], "repair_time": 2.8}
        self.assertEqual(score_bcy([event], [])["E_negative"], 0)
        self.assertEqual(score_event_delay(event, [])["status"], "not_evaluable")

    def test_budget_tracks_per_tick_and_whole_track(self):
        budget = Budget(total_ticks=2)
        self.assertIsNone(budget.add(tick=0, calls=1, frames=4, input_tokens=4096, output_tokens=256, memory_tokens=100))
        self.assertEqual(budget.add(tick=1, calls=1, frames=4, input_tokens=4097, output_tokens=0, memory_tokens=0), "input_tokens")
        self.assertEqual(budget.totals["calls"], 2)
        self.assertEqual(budget.totals["input_tokens"], 8193)

    def test_method_prompts_have_same_source_and_distinct_update_rule(self):
        instruction = self.track["instruction_versions"][0]
        p0 = build_prompt("S0", instruction, ["cup_in_tray"], "", 1)
        p1 = build_prompt("S1", instruction, ["cup_in_tray"], "earlier view", 1)
        pc = build_prompt("C1", instruction, ["cup_in_tray"], "earlier view", 1)
        self.assertIn(instruction["text"], p0)
        self.assertIn(instruction["text"], p1)
        self.assertIn(instruction["text"], pc)
        self.assertIn("earlier view", p1)
        self.assertIn("earlier view", pc)
        self.assertNotIn("earlier view", p0)

    def test_budget_failure_is_invalid_and_keeps_raw_output(self):
        class OverBudget:
            def infer(self, method, instruction, objects, frames, memory, tick):
                return {"raw": '{"judgments": []}', "input_tokens": 4097, "output_tokens": 5, "memory_tokens": 0, "elapsed_ms": 1, "peak_vram_bytes": 0}
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "track.json"
            p.write_text(json.dumps({**self.track, "frames": self.track["frames"][:1]}))
            run_track(p, OverBudget(), "S0", Path(td) / "out", Path(td) / "ledger.csv")
            row = json.loads((Path(td) / "out" / "records.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(row["budget_reason"], "input_tokens")
            self.assertEqual(row["judgments"]["cup_in_tray"]["C"], "⊥")
            self.assertIn("judgments", row["raw"])

    def test_resume_keeps_prior_output_and_cost(self):
        class Backend:
            def __init__(self):
                self.fail_once = True
                self.seen = []
            def infer(self, method, instruction, objects, frames, memory, tick):
                self.seen.append((tick, memory, [f["time"] for f in frames]))
                if tick == 1 and self.fail_once:
                    self.fail_once = False
                    raise RuntimeError("temporary failure")
                raw = json.dumps({"judgments": [{"object_id": objects[0], "H": "+", "C": "?", "P": "?", "G": "?"}], "memory": f"summary {tick}"})
                return {"raw": raw, "input_tokens": 50, "output_tokens": 20, "memory_tokens": 4, "elapsed_ms": 1, "peak_vram_bytes": 0}
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "track.json"
            p.write_text(json.dumps({**self.track, "frames": self.track["frames"][:4]}))
            backend = Backend()
            a = run_track(p, backend, "S1", Path(td) / "out", Path(td) / "ledger.csv")
            self.assertEqual(a["status"], "failed")
            b = run_track(p, backend, "S1", Path(td) / "out", Path(td) / "ledger.csv", resume=True)
            self.assertEqual(b["status"], "completed")
            records = [json.loads(x) for x in (Path(td) / "out" / "records.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual([x["tick"] for x in records], [0, 1, 2])
            self.assertEqual(backend.seen[-1][1], "summary 0")
            self.assertEqual(b["cost"]["calls"], 3)
            self.assertEqual(len((Path(td) / "ledger.csv").read_text().splitlines()), 3)


if __name__ == "__main__":
    unittest.main()

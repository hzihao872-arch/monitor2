import json
import tempfile
import unittest
from pathlib import Path

from model_side.pilot_pkg.seal_fresh_batch import input_rows, summarize


class SealFreshTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.raw = self.root / "raw"
        self.inputs = {}
        for arm in ("access_gate", "support_surface"):
            inp = self.root / arm / "model_input"
            inp.mkdir(parents=True)
            rows = []
            for i in range(1, 10):
                video = f"{i:04}.mp4"
                (inp / video).write_bytes(video.encode())
                rows.append({"video": video, "instruction": "goal", "sha256": __import__("hashlib").sha256(video.encode()).hexdigest()})
            (inp / "manifest.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
            self.inputs[arm] = inp
            for method in ("topreward", "robometer"):
                cell = self.raw / arm / method
                cell.mkdir(parents=True)
                journal = [{"kind": "configuration", "method": method}]
                journal += [{"kind": "video_input", "video": r["video"], "sha256": r["sha256"]} for r in rows]
                for r in rows:
                    if method == "robometer":
                        journal.append({"kind": "native_decoder_probe", "video": r["video"], "frame_count": 15, "same_pixels_as_manifest": True})
                        stem = Path(r["video"]).stem
                        progress_file = cell / (stem + ".npy")
                        success_file = cell / (stem + "_success_probs.npy")
                        progress_file.write_bytes(b"progress")
                        success_file.write_bytes(b"success")
                        journal.append({"kind": "native_result", "video": r["video"], "video_sha256": r["sha256"],
                                        "progress": [0.1] * 15, "success_head": [0.2] * 15,
                                        "progress_sha256": __import__("hashlib").sha256(progress_file.read_bytes()).hexdigest(),
                                        "success_sha256": __import__("hashlib").sha256(success_file.read_bytes()).hexdigest()})
                    else:
                        payload = {"kind": "native_result", "video": r["video"], "video_sha256": r["sha256"],
                                   "prefix_rewards": [0.1] * 15, "prefix_lengths": list(range(1, 16))}
                        path = cell / (Path(r["video"]).stem + ".json")
                        path.write_text(json.dumps(payload))
                        payload["result_sha256"] = __import__("hashlib").sha256(path.read_bytes()).hexdigest()
                        journal.append(payload)
                (cell / "native_calls.jsonl").write_text("".join(json.dumps(r) + "\n" for r in journal))

    def update(self, arm="access_gate", method="topreward", change=None):
        path = self.raw / arm / method / "native_calls.jsonl"
        rows = [json.loads(x) for x in path.read_text().splitlines()]
        change(rows)
        path.write_text("".join(json.dumps(x) + "\n" for x in rows))

    def status(self):
        return summarize(self.raw, self.inputs)["status"]

    def test_complete_nine_by_four(self):
        self.assertEqual(self.status(), "complete")

    def test_failure_is_preserved_and_scorable(self):
        def change(rows):
            row = next(r for r in rows if r.get("kind") == "native_result")
            row.clear()
            row.update(kind="native_failure", video="0001.mp4", error="OOM")
        self.update(change=change)
        self.assertEqual(self.status(), "complete_with_failures")

    def test_decoder_hash_failure_stops_scoring(self):
        def change(rows):
            row = next(r for r in rows if r.get("kind") == "native_result")
            row.clear()
            row.update(kind="native_failure", video="0001.mp4", error="client decoder pixel hashes differ")
        self.update(change=change)
        self.assertEqual(self.status(), "incomplete")

    def test_missing_result_is_incomplete(self):
        self.update(change=lambda rows: rows.pop())
        self.assertEqual(self.status(), "incomplete")

    def test_duplicate_result_is_incomplete(self):
        self.update(change=lambda rows: rows.append(rows[-1].copy()))
        self.assertEqual(self.status(), "incomplete")

    def test_bad_curve_is_incomplete(self):
        self.update(change=lambda rows: rows[-1].update(prefix_rewards=[0.1] * 14))
        self.assertEqual(self.status(), "incomplete")

    def test_nonfinite_curve_is_incomplete(self):
        self.update(change=lambda rows: rows[-1].update(prefix_rewards=[float("nan")] * 15))
        self.assertEqual(self.status(), "incomplete")

    def test_wrong_video_hash_is_incomplete(self):
        self.update(change=lambda rows: rows[-1].update(video_sha256="bad"))
        self.assertEqual(self.status(), "incomplete")

    def test_four_static_video_inputs_supported_separately(self):
        static = Path(__file__).resolve().parents[1] / "p3_static_input/access_gate/model_input"
        self.assertEqual(len(input_rows(static, expected_count=4)), 4)

    def test_missing_native_artifact_hash_is_incomplete(self):
        self.update(method="robometer", change=lambda rows: rows[-1].pop("progress_sha256"))
        self.assertEqual(self.status(), "incomplete")


if __name__ == "__main__":
    unittest.main()

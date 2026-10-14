"""No-model input/contract dry run on sealed anonymous P0 input packages.

Reads no truth, condition mapping, P0 scores, or model output. Uses the local
copy of each video only after its bytes match the P0 transfer ZIP member.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import cv2

from monitor_contract_v0 import VERSION, evaluate


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FRESH = ROOT / "research/prerequisite_monitor/fresh_server_20261007"
SECONDS = [0, 2, 4, 6, 7, 8, 10, 12, 14]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def synthetic_record(start_route: str, middle_route: str, end_route: str,
                     direction: str, start_done: str = "false", end_done: str = "false",
                     alternative_start: str = "refuted", alternative_end: str = "refuted",
                     uncertainty: str | None = None):
    return {
        "spec_version": VERSION,
        "mid_second": 7,
        "goal_done": {"t0": start_done, "t_mid": "false", "t14": end_done},
        "candidate_relation": {
            "entity": "movable structure", "region": "target region",
            "predicate": "required region is available",
            "satisfied": {"t0": "false", "t_mid": "true", "t14": "false"},
            "goal_relevance": "supported",
            "alternative_route": {"t0": alternative_start, "t14": alternative_end},
        },
        "continuation": {"t0": start_route, "t_mid": middle_route, "t14": end_route},
        "evidence": [{"second": second, "region": "target region", "claim": "synthetic citation"}
                     for second in (0, 7, 14)],
        "uncertainty_reason": uncertainty,
        "direction": direction,
    }


def check_p0_inputs() -> list[dict]:
    reports = []
    for arm in ("access_gate", "support_surface"):
        archive = FRESH / "local_transfer_p0" / f"{arm}.zip"
        video_dir = FRESH / "p4_inputs/neutral" / arm / "model_input"
        with zipfile.ZipFile(archive) as zipped:
            names = set(zipped.namelist())
            required = {f"{index:04d}.mp4" for index in range(1, 10)} | {
                "instruction.txt", "manifest.jsonl", "media_hashes.json"}
            assert names == required, (archive, names ^ required)
            instruction = zipped.read("instruction.txt").decode("utf-8").strip()
            manifest = [json.loads(line) for line in zipped.read("manifest.jsonl").decode("utf-8").splitlines()]
            media = {item["video"]: item for item in json.loads(zipped.read("media_hashes.json"))["clips"]}
            assert len(manifest) == len(media) == 9
            cases = []
            for row in manifest:
                name = row["video"]
                assert name in media and row["instruction"] == instruction
                assert row["sha256"] == digest(zipped.read(name))
                path = video_dir / name
                assert path.exists() and digest(path.read_bytes()) == row["sha256"]
                cap = cv2.VideoCapture(str(path))
                assert cap.isOpened(), path
                frame_hashes = {}
                for second in SECONDS:
                    assert cap.set(cv2.CAP_PROP_POS_FRAMES, second), (path, second)
                    ok, frame = cap.read()
                    assert ok, (path, second)
                    frame_hashes[str(second)] = digest(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).tobytes())
                cap.release()
                expected = media[name]["decoded_rgb_sha256"]
                matches = {key: value == expected[int(key)] for key, value in frame_hashes.items()}
                cases.append({"video": name, "video_sha256": row["sha256"],
                              "decoded_frame_matches": matches,
                              "all_decoded_frames_match": all(matches.values())})
            reports.append({"anonymous_group": arm, "archive_sha256": digest(archive.read_bytes()),
                            "instruction_sha256": digest(zipped.read("instruction.txt")),
                            "video_count": len(cases), "cases": cases})
    return reports


def check_contract() -> list[dict]:
    examples = {
        "beneficial": synthetic_record("blocked", "possible", "possible", "beneficial"),
        "harmful": synthetic_record("possible", "blocked", "blocked", "harmful"),
        "reversal": synthetic_record("blocked", "possible", "blocked", "unchanged"),
        "completed_priority": synthetic_record("blocked", "blocked", "unknown", "completed", end_done="true"),
        "unknown_route": synthetic_record("unknown", "possible", "possible", "unknown", uncertainty="route unresolved"),
        "unknown_alternative": synthetic_record("blocked", "possible", "possible", "unknown",
                                                 alternative_start="unknown", uncertainty="alternative route unresolved"),
        "unchanged": synthetic_record("possible", "possible", "possible", "unchanged"),
    }
    results = [{"name": name, **evaluate(json.dumps(record), SECONDS)} for name, record in examples.items()]
    results.append({"name": "parse_failure", **evaluate('{"bad":', SECONDS)})
    bad_evidence = synthetic_record("blocked", "possible", "possible", "beneficial")
    bad_evidence["evidence"][1]["second"] = 15
    results.append({"name": "invalid_citation", **evaluate(json.dumps(bad_evidence), SECONDS)})
    bad_direction = synthetic_record("blocked", "possible", "possible", "unchanged")
    results.append({"name": "direction_conflict", **evaluate(json.dumps(bad_direction), SECONDS)})
    expected_status = {name: ("valid" if name in examples else
                              "parse_failure" if name == "parse_failure" else
                              "schema_or_evidence_failure" if name == "invalid_citation" else "direction_conflict")
                       for name in [*examples, "parse_failure", "invalid_citation", "direction_conflict"]}
    assert all(item["status"] == expected_status[item["name"]] for item in results)
    assert next(item for item in results if item["name"] == "reversal")["transient"] == "beneficial_then_revoked"
    return results


def main():
    report = {
        "scope": "input_and_contract_only_no_model_no_truth",
        "spec_version": VERSION,
        "sample_seconds": SECONDS,
        "input_audit": check_p0_inputs(),
        "synthetic_contract_cases": check_contract(),
    }
    report["video_count"] = sum(group["video_count"] for group in report["input_audit"])
    report["decoded_frame_match_count"] = sum(sum(case["decoded_frame_matches"].values())
                                              for group in report["input_audit"] for case in group["cases"])
    report["decoded_frame_total"] = report["video_count"] * len(SECONDS)
    out = HERE / "local_dry_run.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"video_count": report["video_count"],
                      "decoded_frame_match_count": report["decoded_frame_match_count"],
                      "decoded_frame_total": report["decoded_frame_total"],
                      "contract_cases": len(report["synthetic_contract_cases"]),
                      "report_sha256": digest(out.read_bytes())}, ensure_ascii=False))


if __name__ == "__main__":
    main()

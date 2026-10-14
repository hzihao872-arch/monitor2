"""Independent byte/frame and truth-isolation audit of a flat-only candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .flat_square_dev import INSTRUCTION
from .produce import sha256
from .scene_observability_pilot import decoded_frame_hashes
from .six_case_route_prototypes import CONDITIONS


def audit(output: Path):
    candidate = output / "candidate_input"
    truth = output / "truth"
    manifest = json.loads((candidate / "media_hashes.json").read_text(encoding="utf-8"))
    mapping = json.loads((truth / "mapping_and_trajectories.json").read_text(encoding="utf-8"))
    issues = []
    clips = manifest["clips"]
    records = mapping["records"]
    if len(clips) != 6 or len(records) != 6:
        issues.append("wrong_clip_count")
    if sorted(row["condition"] for row in records) != sorted(CONDITIONS):
        issues.append("wrong_condition_set")
    if manifest["instruction"] != INSTRUCTION:
        issues.append("instruction_mismatch")
    if (candidate / "instruction.txt").read_text(encoding="utf-8").strip() != INSTRUCTION:
        issues.append("instruction_file_mismatch")
    expected = {row["video"] for row in clips} | {"instruction.txt", "media_hashes.json"}
    actual = {path.name for path in candidate.iterdir() if path.is_file()}
    if expected != actual:
        issues.append("unexpected_candidate_files")
    observed = []
    for row in clips:
        video = candidate / row["video"]
        decoded = decoded_frame_hashes(video)
        if decoded != row["decoded_rgb_sha256"]:
            issues.append(f"decoded_hash_mismatch:{row['video']}")
        if len(decoded) != 15:
            issues.append(f"wrong_decoded_frame_count:{row['video']}")
        if row["sample_indices_30fps"] != list(range(0, 450, 30)):
            issues.append(f"wrong_sample_indices:{row['video']}")
        if sha256(video) != row["video_sha256"]:
            issues.append(f"video_hash_mismatch:{row['video']}")
        observed.append({"video": row["video"], "decoded_frames": len(decoded),
                         "video_sha256": sha256(video)})
    for record in records:
        want = (mapping["blocked_snapshot_sha256"] if record["condition"] in ("B+", "B0")
                else mapping["open_snapshot_sha256"])
        if record["initial_state_sha256"] != want:
            issues.append(f"wrong_initial_branch:{record['video']}")
        if record["admission_issues"]:
            issues.append(f"physical_admission_failed:{record['video']}")
    input_text = (candidate / "media_hashes.json").read_text(encoding="utf-8")
    if any(word in input_text for word in ("condition", "terminal", "scene_kind", "truth")):
        issues.append("truth_field_in_candidate_manifest")
    blocked_shared = all(row["initial_state_sha256"] == mapping["blocked_snapshot_sha256"]
                         for row in records if row["condition"] in ("B+", "B0"))
    open_shared = all(row["initial_state_sha256"] == mapping["open_snapshot_sha256"]
                      for row in records if row["condition"] not in ("B+", "B0"))
    report = {"status": "pass" if not issues else "fail", "issues": issues,
              "clips": observed, "blocked_initial_shared": blocked_shared,
              "open_initial_shared": open_shared}
    (truth / "input_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.output)
    print(json.dumps(result))
    if result["issues"]:
        raise SystemExit(1)

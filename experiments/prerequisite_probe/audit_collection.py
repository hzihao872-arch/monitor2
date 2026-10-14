"""Check completeness and input identity of collected unseen model runs.

This intentionally never reads numeric model outputs.
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

FAMILIES = (
    "unseen_offset_cell",
    "unseen_pickup_gate_v2",
    "unseen_mirror_cell",
    "unseen_left_cell",
    "unseen_pickup_gate_shifted",
    "unseen_rear_cell",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit(root: Path) -> dict:
    out = {"checked_at_utc": datetime.now(timezone.utc).isoformat(), "families": {}}
    for family in FAMILIES:
        base = root / family
        truth = base / "truth"
        result = base / "model_results"
        frozen = json.loads((truth / "frozen_test.json").read_text(encoding="utf-8"))
        expected = {f"{stem}.mp4": item for stem, item in frozen["cases"].items()}
        local_frames = {row["video"]: row for row in json.loads((truth / "actual_frames.json").read_text(encoding="utf-8"))}
        cloud_hashes = {}
        for line in (result / "input_video_sha256.txt").read_text(encoding="utf-8").splitlines():
            value, path = line.split(maxsplit=1)
            cloud_hashes[Path(path).name] = value
        checks = {
            "freeze_sidecar": (truth / "frozen_test.sha256").read_text(encoding="ascii").strip() == sha256(truth / "frozen_test.json"),
            "cloud_video_hashes": set(cloud_hashes) == set(expected) and all(cloud_hashes[name] == item["video_sha256"] for name, item in expected.items()),
            "local_video_hashes": all(sha256(base / "model_input" / name) == item["video_sha256"] for name, item in expected.items()),
            "top_output_count": len(list((result / "topreward").glob("[0-9][0-9][0-9][0-9].json"))) == 6,
            "rob_output_count": len(list((result / "robometer_pr33_compat").glob("[0-9][0-9][0-9][0-9].npy"))) == 6,
            "rob_success_count": len(list((result / "robometer_pr33_compat").glob("[0-9][0-9][0-9][0-9]_success_probs.npy"))) == 6,
            "top_command_log": all((result / "topreward" / name).is_file() for name in ("command.txt", "run.log")),
            "rob_commands_logs": all((result / "robometer_pr33_compat" / f"{stem}{ext}").is_file() for stem in ("0001", "0002", "0003", "0004", "0005", "0006") for ext in (".command.txt", ".log")),
        }
        log = (result / "cloud_run.log").read_text(encoding="utf-8", errors="replace")
        checks["cloud_completed"] = f"TOP_COMPLETE {family}" in log and f"ROB_COMPLETE {family} 0006" in log
        for method in ("topreward", "robometer_pr33_compat"):
            decoded = json.loads((result / method / "decoded_frames.json").read_text(encoding="utf-8"))
            videos = {row["video"]: row for row in decoded["videos"]}
            checks[f"{method}_decoded_frames"] = set(videos) == set(expected) and all(
                videos[name]["decoded_frame_count"] == 15
                and videos[name]["video_sha256"] == expected[name]["video_sha256"]
                and videos[name]["decoded_rgb_sha256"] == local_frames[name]["decoded_rgb_sha256"]
                for name in expected
            )
        out["families"][family] = {"checks": checks, "passed": all(checks.values()), "model_runs": 12 if all(checks.values()) else None}
    out["complete"] = all(item["passed"] for item in out["families"].values())
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("experiments/prerequisite_probe/artifacts"))
    args = parser.parse_args()
    result = audit(args.root)
    path = args.root / "unseen_collection_status.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"complete": result["complete"], "families": {key: value["passed"] for key, value in result["families"].items()}}))

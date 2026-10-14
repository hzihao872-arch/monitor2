"""Write an immutable-in-practice audit snapshot before any unseen model scoring."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .produce import CASES, sha256


def freeze(root: Path) -> dict:
    here = Path(__file__).parent
    truth = root / "truth"
    oracle = {row["case"]: row for row in map(json.loads, (truth / "oracle_checks.jsonl").read_text(encoding="utf-8").splitlines())}
    cases = {}
    scene_family = None
    for condition, stem in CASES.items():
        record = json.loads((truth / f"{stem}.json").read_text(encoding="utf-8"))
        if scene_family is None:
            scene_family = record["scene"]
        elif scene_family != record["scene"]:
            raise ValueError("Mixed scene families in one frozen set")
        cases[stem] = {
            "condition": condition,
            "video_sha256": sha256(root / "model_input" / f"{stem}.mp4"),
            "raw_sha256": sha256(root / "raw" / f"{stem}.mp4"),
            "pre_state_sha256": record["pre_state_sha256"],
            "success_in_video": record["success"],
            "q_control": oracle[condition]["q_control"] if condition in oracle else None,
            "q_action": oracle[condition]["q_action"] if condition in oracle else None,
            "C": oracle[condition]["C"] if condition in oracle else None,
        }
    payload = {
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "before_unseen_model_scores",
        "scene_family": scene_family,
        "instruction": "Put the blue cube in the green tray.",
        "event_windows_seconds": {"pre": [0, 2], "action": [2, 12], "post": [12, 14]},
        "statistic": "native scale, median(post)-median(pre), no per-video normalization",
        "label_gates": {"effective_C_min": 0.30, "ineffective_abs_C_max": 0.10, "hindering_C_max": -0.30},
        "exclusions": ["wrong frame count or dimensions", "target/obstacle/action result not visible in model-decoded main frames", "failed physical label gate", "IK error over 0.025 m", "controller instability"],
        "noise_threshold": None,
        "noise_threshold_reason": "Only one development N0 clip; no thresholded error rate",
        "continuation_seeds": list(range(20)),
        "input_frames_sha256": sha256(truth / "actual_frames.json"),
        "oracle_file_sha256": sha256(truth / "oracle_checks.jsonl"),
        "code_sha256": {name: sha256(here / name) for name in ("probe.py", "produce.py", "audit_inputs.py", "validate.py", "freeze_unseen.py")},
        "protocol_sha256": sha256(here / "evaluation_protocol.md"),
        "cases": cases,
    }
    data = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    path = truth / "frozen_test.json"
    if path.exists():
        raise FileExistsError(path)
    path.write_text(data, encoding="utf-8")
    (truth / "frozen_test.sha256").write_text(hashlib.sha256(path.read_bytes()).hexdigest() + "\n", encoding="ascii")
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    result = freeze(args.root)
    print(json.dumps({"frozen_at_utc": result["frozen_at_utc"], "cases": len(result["cases"])}))

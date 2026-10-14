"""Validate frozen probe artifacts without passing truth to model code."""

import json
import subprocess
from pathlib import Path

from .probe import INSTRUCTION, sample_indices
from .produce import CASES, sha256


def video_info(path):
    output = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=nb_frames,r_frame_rate,width,height",
        "-of", "json", str(path),
    ], text=True)
    return json.loads(output)["streams"][0]


def validate(root):
    truth = root / "truth"
    results = {case: json.loads((truth / f"{stem}.json").read_text(encoding="utf-8"))
               for case, stem in CASES.items()}
    oracle = {x["case"]: x for x in map(json.loads, (truth / "oracle_checks.jsonl").read_text(encoding="utf-8").splitlines())}
    decoded = {x["video"]: x for x in json.loads((truth / "actual_frames.json").read_text(encoding="utf-8"))}
    checks = {}
    checks["same_Bplus_B0_snapshot"] = results["B+"]["pre_state_sha256"] == results["B0"]["pre_state_sha256"]
    checks["all_preparation_blue_static"] = all(
        max(abs(a - b) for a, b in zip(results[case]["blue_pre"], results[case]["blue_post"])) < .005
        for case in ("B+", "B0", "U0", "H-")
    )
    checks["physical_labels"] = (
        oracle["B+"]["C"] >= .30 and abs(oracle["B0"]["C"]) <= .10 and
        abs(oracle["U0"]["C"]) <= .10 and oracle["H-"]["C"] <= -.30
    )
    checks["Gplus_succeeds_N0_does_not"] = results["G+"]["success"] and not results["N0"]["success"]
    checks["all_20_paired_seeds"] = all(
        len(oracle[case]["action_success_by_seed"]) == len(oracle[case]["control_success_by_seed"]) == 20
        for case in ("B+", "B0", "U0", "H-")
    )
    details = {}
    for case, stem in CASES.items():
        raw_path = root / "raw" / f"{stem}.mp4"
        model_path = root / "model_input" / f"{stem}.mp4"
        raw_info = video_info(raw_path)
        model_info = video_info(model_path)
        item = results[case]
        details[stem] = {
            "raw": raw_info, "model_input": model_info,
            "raw_sha256_match": sha256(raw_path) == item["raw_sha256"],
            "model_sha256_match": sha256(model_path) == item["model_video_sha256"],
            "decoded_frames": decoded[f"{stem}.mp4"]["decoded_frame_count"],
            "sample_indices_match": item["sample_frame_indices"] == sample_indices(),
            "instruction_match": item["instruction"] == INSTRUCTION,
        }
        checks[f"video_{stem}"] = (
            raw_info == {"width": 640, "height": 480, "r_frame_rate": "30/1", "nb_frames": "450"}
            and model_info == {"width": 640, "height": 480, "r_frame_rate": "1/1", "nb_frames": "15"}
            and details[stem]["raw_sha256_match"] and details[stem]["model_sha256_match"]
            and details[stem]["decoded_frames"] == 15 and details[stem]["sample_indices_match"]
            and details[stem]["instruction_match"]
        )
    if not all(checks.values()):
        raise RuntimeError(f"Validation failed: {[k for k, ok in checks.items() if not ok]}")
    return {"checks": checks, "details": details, "status": "video_and_oracle_verified_model_scores_unavailable"}


if __name__ == "__main__":
    root = Path("experiments/prerequisite_probe/artifacts")
    report = validate(root)
    (root / "truth" / "validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"passed": len(report["checks"]), "status": report["status"]}))

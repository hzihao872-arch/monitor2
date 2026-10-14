"""Write phase-one model status from the verified native-score analysis."""

from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).parent
RESULTS = HERE / "artifacts" / "model_results"
IDS = [f"{i:04d}" for i in range(1, 7)]


def save(name: str, value: dict) -> None:
    (RESULTS / name).write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main() -> None:
    analysis = json.loads((RESULTS / "analysis_native.json").read_text(encoding="utf-8"))
    methods = analysis["methods"]
    if set(methods) != {"TOPReward", "Robometer PR33 dtype compat"}:
        raise RuntimeError(f"Unexpected completed methods: {list(methods)}")
    if analysis["missing_methods"] != ["Robometer"]:
        raise RuntimeError("Strict original Robometer must remain missing")
    for number in IDS:
        if not (RESULTS / "topreward" / f"{number}.json").exists():
            raise RuntimeError(f"Missing TOPReward {number}")
        for suffix in (".npy", "_success_probs.npy", ".log", ".command.txt"):
            if not (RESULTS / "robometer_pr33_compat" / f"{number}{suffix}").exists():
                raise RuntimeError(f"Missing Robometer PR33 {number}{suffix}")

    pairs = {
        "TOPReward": methods["TOPReward"]["pairwise"],
        "Robometer": None,
        "Robometer_PR33_dtype_compat": methods["Robometer PR33 dtype compat"]["pairwise"],
        "strict_original_robometer_reason": (
            "Unmodified official script failed on first forward with mixed FP32/BF16; "
            "environment failure is not a model miss or tie."
        ),
        "metric": "post 12-14 s median minus pre 0-2 s median; native scales",
    }
    save("paired_sorting.json", pairs)

    status = {
        "instruction": analysis["instruction"],
        "videos": [f"{number}.mp4" for number in IDS],
        "input_frame_audit": {
            "TOPReward": "cloud_topreward_decoded_frames.json",
            "Robometer": "cloud_robometer_decoded_frames.json",
            "frozen_truth_reference": "../truth/actual_frames.json",
            "match": "six videos x 15 RGB frames exactly match frozen local frame SHA-256 lists",
        },
        "TOPReward": {
            "group": "no additional reward model training",
            "repository_commit": "4877a0ee5098cbec18485125466631b1dcc4a573",
            "model": "Qwen/Qwen3-VL-8B-Instruct",
            "model_revision": "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b",
            "result_status": "six valid original-model outputs",
            "prefix_rewards": [f"topreward/{number}.json" for number in IDS],
            "full_log": "topreward/cloud_run.log",
            "run_script": "../../cloud_run_topreward_official.sh",
            "weight_hashes": "official_weight_hashes.json",
        },
        "Robometer": {
            "group": "pretrained reward model; zero-shot transfer to this task",
            "repository_commit": "352d160389daa964788de1ec933d1925f3a6de4f",
            "model": "robometer/Robometer-4B",
            "model_revision": "beef63bc914c5c189329d49c6d712d96d632aa34",
            "result_status": "尚无该模型结果",
            "progress": None,
            "success_head": None,
            "failure": "unmodified official script fails at first forward: float != c10::BFloat16",
            "failure_log": "robometer/0001.official_dtype_fail.log",
            "full_log": "robometer/cloud_run.official_dtype_fail.log",
            "run_script": "../../cloud_run_robometer_official.sh",
        },
        "Robometer_PR33_dtype_compat": {
            "group": "separate compatibility run; not the strict unmodified original",
            "model": "robometer/Robometer-4B",
            "model_revision": "beef63bc914c5c189329d49c6d712d96d632aa34",
            "base_model": "Qwen/Qwen3-VL-4B-Instruct",
            "base_revision": "ebb281ec70b05090aa6165b016eac8ec08e71b17",
            "result_status": "six valid native outputs with PR #33 dtype patch",
            "code_base_commit": "352d160389daa964788de1ec933d1925f3a6de4f",
            "patch_commit": "19562e8fe0e63f74b64aa06f8e8fbfaf76127ea7",
            "patch_file": "../../patches/robometer_pr33.patch",
            "python": "3.10.22",
            "torch": "2.8.0+cu128",
            "transformers": "4.57.6",
            "unsloth": "2026.8.18",
            "unsloth_zoo": "2026.8.17",
            "progress": [f"robometer_pr33_compat/{number}.npy" for number in IDS],
            "success_head": [
                f"robometer_pr33_compat/{number}_success_probs.npy" for number in IDS
            ],
            "per_video_commands_and_logs": [
                [
                    f"robometer_pr33_compat/{number}.command.txt",
                    f"robometer_pr33_compat/{number}.log",
                ]
                for number in IDS
            ],
            "full_log": "robometer_pr33_compat/cloud_run.log",
            "run_script": "../../cloud_run_robometer_pr33_compat.sh",
            "weight_equivalence": "unsloth_qwen4_weight_equivalence.json",
        },
        "analysis": "analysis_native.json",
        "model_action_curves": "native_action_curves.png",
        "paired_rankings": "paired_sorting.json",
        "noise_threshold": None,
        "noise_threshold_reason": (
            "One N0 development clip cannot establish a frozen noise threshold; "
            "no thresholded miss or false-award rate is claimed."
        ),
        "cloud": {
            "provider": "SeetaCloud",
            "gpu": "RTX 5090 32 GB",
            "listed_price_cny_per_hour": 3.03,
            "original_weights_sha256_verified": True,
            "download_and_setup_logs": "cloud_logs/",
            "dedicated_ssh_public_key_removed": True,
        },
        "interpretation": (
            "One frozen geometry family, one video per condition, one missing independent "
            "visual reviewer. These are development-probe observations, not proof of a "
            "general failure or a causal mechanism."
        ),
    }
    save("status.json", status)
    print("Wrote status.json and paired_sorting.json")


if __name__ == "__main__":
    main()

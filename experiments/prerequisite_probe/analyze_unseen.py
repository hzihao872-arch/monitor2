"""Analyze frozen unseen families only after native model outputs are present."""

import json
from pathlib import Path

import numpy as np

from .analyze_native_scores import comparison, summarize


BASE = Path(__file__).parent / "artifacts"
FAMILIES = (
    "unseen_offset_cell",
    "unseen_pickup_gate_v2",
    "unseen_mirror_cell",
    "unseen_left_cell",
    "unseen_pickup_gate_shifted",
    "unseen_rear_cell",
)
METHODS = ("topreward", "robometer_pr33_compat")


def native_points(root: Path, method: str, stem: str) -> list[float]:
    if method == "topreward":
        payload = json.loads((root / "model_results" / method / f"{stem}.json").read_text(encoding="utf-8"))
        if payload["instruction"] != "Put the blue cube in the green tray." or payload["prefix_lengths"] != list(range(1, 16)):
            raise ValueError(f"TOPReward input mismatch: {root.name}/{stem}")
        return payload["prefix_rewards"]
    return np.load(root / "model_results" / method / f"{stem}.npy", allow_pickle=False).tolist()


def check_decoding(root: Path, method: str) -> bool:
    local = {x["video"]: x for x in json.loads((root / "truth" / "actual_frames.json").read_text(encoding="utf-8"))}
    remote = json.loads((root / "model_results" / method / "decoded_frames.json").read_text(encoding="utf-8"))
    for entry in remote["videos"]:
        expected = local[entry["video"]]
        if entry["decoded_rgb_sha256"] != expected["decoded_rgb_sha256"]:
            raise ValueError(f"Decoded frame mismatch: {root.name}/{method}/{entry['video']}")
    return len(remote["videos"]) == 6


def event_delta(values, pre=(0, 3), post=(12, 15)) -> float:
    v = np.asarray(values, dtype=float)
    return float(np.median(v[post[0]:post[1]]) - np.median(v[pre[0]:pre[1]]))


def pairwise(videos, pre=(0, 3), post=(12, 15)):
    delta = {v["condition"]: event_delta(v["native_points"], pre, post) for v in videos.values()}
    return {
        "deltas": delta,
        "Bplus_vs_B0": comparison(delta["B+"], delta["B0"]),
        "Bplus_vs_U0": comparison(delta["B+"], delta["U0"]),
        "Hminus_vs_N0": comparison(delta["H-"], delta["N0"], lower_is_better=True),
        "Gplus_vs_N0": comparison(delta["G+"], delta["N0"]),
    }


def main():
    output = {"families": {}, "methods": {}, "thresholded_rates": None,
              "threshold_note": "Only one development N0; no frozen noise threshold."}
    for family in FAMILIES:
        root = BASE / family
        frozen = json.loads((root / "truth" / "frozen_test.json").read_text(encoding="utf-8"))
        family_record = {"freeze": str(root / "truth" / "frozen_test.json"),
                         "physical": {v["condition"]: {"q_control": v["q_control"], "q_action": v["q_action"], "C": v["C"]}
                                      for v in frozen["cases"].values()}, "methods": {}}
        for method in METHODS:
            directory = root / "model_results" / method
            if not all((directory / (f"{stem}.json" if method == "topreward" else f"{stem}.npy")).exists() for stem in frozen["cases"]):
                family_record["methods"][method] = {"status": "incomplete", "available": sorted(p.name for p in directory.glob("*") if p.is_file())}
                continue
            decoded_match = check_decoding(root, method)
            videos = {}
            for stem, condition_record in frozen["cases"].items():
                values = native_points(root, method, stem)
                videos[stem] = {"condition": condition_record["condition"], **summarize(values)}
                if method == "robometer_pr33_compat":
                    success = np.load(directory / f"{stem}_success_probs.npy", allow_pickle=False).tolist()
                    videos[stem]["success_head"] = summarize(success)
            family_record["methods"][method] = {
                "status": "complete", "decoded_frames_match": decoded_match,
                "videos": videos, "primary": pairwise(videos),
                "boundary_sensitivity": {
                    "post_11_13": pairwise(videos, post=(11, 14)),
                    "post_13_14": pairwise(videos, post=(13, 15)),
                    "pre_0_1": pairwise(videos, pre=(0, 2)),
                    "pre_1_3": pairwise(videos, pre=(1, 4)),
                },
            }
        output["families"][family] = family_record
    for method in METHODS:
        complete = [r["methods"][method] for r in output["families"].values() if r["methods"][method]["status"] == "complete"]
        output["methods"][method] = {"complete_scene_families": len(complete),
            "Bplus_above_B0_count": sum(r["primary"]["Bplus_vs_B0"]["outcome"] == "win" for r in complete),
            "Bplus_above_U0_count": sum(r["primary"]["Bplus_vs_U0"]["outcome"] == "win" for r in complete),
            "Hminus_below_N0_count": sum(r["primary"]["Hminus_vs_N0"]["outcome"] == "win" for r in complete),
            "Gplus_above_N0_count": sum(r["primary"]["Gplus_vs_N0"]["outcome"] == "win" for r in complete)}
    path = BASE / "unseen_analysis_native.json"
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output["methods"], indent=2))


if __name__ == "__main__":
    main()

"""Summarize frozen, native scores, keeping compatibility runs separate.

The model runners must finish first. This script reads the isolated truth only
afterwards and never supplies labels or controller outcomes to either model.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).parents[2]
ARTIFACTS = ROOT / "experiments" / "prerequisite_probe" / "artifacts"
RESULTS = ARTIFACTS / "model_results"
IDS = [f"{number:04d}" for number in range(1, 7)]
INSTRUCTION = "Put the blue cube in the green tray."
COLORS = {"B+": "#087e8b", "B0": "#e09f3e", "U0": "#9a6dd7", "H−": "#c75146", "G+": "#14853d", "N0": "#66717e"}


def summarize(values: list[float]) -> dict:
    array = np.asarray(values, dtype=np.float64)
    if array.shape != (15,) or not np.isfinite(array).all():
        raise ValueError(f"Expected 15 finite native points, got {array.shape}")
    pre = float(np.median(array[0:3]))       # t = 0,1,2 s
    action = float(np.median(array[2:13]))   # t = 2,...,12 s
    post = float(np.median(array[12:15]))    # t = 12,13,14 s
    return {
        "native_points": array.tolist(),
        "seconds": list(range(15)),
        "pre_0_2_median": pre,
        "action_2_12_median": action,
        "post_12_14_median": post,
        "post_minus_pre": post - pre,
        "action_peak": float(np.max(array[2:13])),
        "action_positive_step_peak": float(np.max(np.diff(array[2:13]))),
    }


def comparison(left: float, right: float, *, lower_is_better: bool = False) -> dict:
    difference = left - right
    if np.isclose(difference, 0.0, rtol=0.0, atol=1e-8):
        outcome = "tie"
    elif (difference < 0) if lower_is_better else (difference > 0):
        outcome = "win"
    else:
        outcome = "loss"
    return {"left": left, "right": right, "difference": difference,
            "direction": "lower" if lower_is_better else "higher", "outcome": outcome}


def read_truth_mapping() -> dict[str, str]:
    mapping = {}
    for identifier in IDS:
        record = json.loads((ARTIFACTS / "truth" / f"{identifier}.json").read_text(encoding="utf-8"))
        mapping[identifier] = "H−" if record["case"] == "H-" else record["case"]
    if set(mapping.values()) != {"B+", "B0", "U0", "H−", "G+", "N0"}:
        raise RuntimeError("Frozen truth mapping has changed")
    return mapping


def read_method(method: str, mapping: dict[str, str]) -> tuple[dict, dict] | None:
    points = {}
    success = {}
    for identifier in IDS:
        if method == "TOPReward":
            path = RESULTS / "topreward" / f"{identifier}.json"
            if not path.exists():
                return None
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload["instruction"] != INSTRUCTION or payload["prefix_lengths"] != list(range(1, 16)):
                raise RuntimeError(f"TOPReward input or native prefixes differ: {identifier}")
            values = payload["prefix_rewards"]
        else:
            directory = "robometer" if method == "Robometer" else "robometer_pr33_compat"
            path = RESULTS / directory / f"{identifier}.npy"
            success_path = RESULTS / directory / f"{identifier}_success_probs.npy"
            if not path.exists() or not success_path.exists():
                return None
            values = np.load(path, allow_pickle=False).tolist()
            success[identifier] = np.load(success_path, allow_pickle=False).tolist()
        points[identifier] = summarize(values)
        points[identifier]["case"] = mapping[identifier]
    return points, success


def pairwise(points: dict[str, dict]) -> dict:
    by_case = {entry["case"]: entry for entry in points.values()}
    delta = lambda case: by_case[case]["post_minus_pre"]
    post = lambda case: by_case[case]["post_12_14_median"]
    return {
        "Bplus_vs_B0_delta": comparison(delta("B+"), delta("B0")),
        "Bplus_vs_U0_delta": comparison(delta("B+"), delta("U0")),
        "Hminus_vs_N0_delta": comparison(delta("H−"), delta("N0"), lower_is_better=True),
        "Hminus_vs_N0_post": comparison(post("H−"), post("N0"), lower_is_better=True),
        "Gplus_vs_N0_delta": comparison(delta("G+"), delta("N0")),
    }


def plot_curves(methods: dict) -> None:
    if not methods:
        return
    fig, axes = plt.subplots(len(methods), 1, figsize=(11, 4.3 * len(methods)), sharex=True, squeeze=False)
    for axis, (method, record) in zip(axes[:, 0], methods.items()):
        axis.axvspan(0, 2, color="#dce7ef", alpha=0.45, label="pre 0–2 s")
        axis.axvspan(2, 12, color="#f5e9d3", alpha=0.45, label="action 2–12 s")
        axis.axvspan(12, 14, color="#e1efdf", alpha=0.55, label="post 12–14 s")
        for entry in record["videos"].values():
            case = entry["case"]
            axis.plot(entry["seconds"], entry["native_points"], marker="o", markersize=2.8,
                      linewidth=1.4, label=case, color=COLORS[case])
        axis.set_ylabel("native prefix log score" if method == "TOPReward" else "native progress")
        axis.set_title(method)
        axis.grid(alpha=0.2)
        axis.legend(ncol=3, fontsize=8)
    axes[-1, 0].set_xlabel("time from video start (s); native 1 FPS points")
    axes[-1, 0].set_xticks(range(15))
    fig.tight_layout()
    fig.savefig(RESULTS / "native_action_curves.png", dpi=180)
    plt.close(fig)


def main() -> None:
    mapping = read_truth_mapping()
    methods = {}
    for method in ("TOPReward", "Robometer", "Robometer PR33 dtype compat"):
        loaded = read_method(method, mapping)
        if loaded is None:
            continue
        videos, success = loaded
        methods[method] = {
            "videos": videos,
            "pairwise": pairwise(videos),
            "success_head_raw": success if method.startswith("Robometer") else None,
            "success_head_diagnostic": (
                {identifier: summarize(values) for identifier, values in success.items()}
                if method.startswith("Robometer") and all(len(values) == 15 for values in success.values()) else None
            ),
            "noise_threshold": None,
            "noise_threshold_note": "One N0 development video cannot establish the frozen noise threshold; no thresholded error rate is reported.",
        }
    output = {
        "instruction": INSTRUCTION,
        "windows_seconds": {"pre": [0, 1, 2], "action": list(range(2, 13)), "post": [12, 13, 14]},
        "main_metric": "median(post native points) - median(pre native points); no per-video min-max",
        "methods": methods,
        "missing_methods": [method for method in ("TOPReward", "Robometer") if method not in methods],
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "analysis_native.json").write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    plot_curves(methods)
    print(f"Analyzed {', '.join(methods) if methods else 'no complete method'}")


if __name__ == "__main__":
    main()

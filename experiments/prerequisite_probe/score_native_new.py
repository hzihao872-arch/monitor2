"""Offline, native-scale TOPReward/Robometer comparison for new frozen scenes."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path

from .run_monitor_qwen import sha256


GOAL = "Put the blue cube in the green tray."
PAIRS = (("B+", "B0", "Bplus_vs_B0_delta", False),
         ("B+", "U0", "Bplus_vs_U0_delta", False),
         ("H-", "N0", "Hminus_vs_N0_delta", True),
         ("G+", "N0", "Gplus_vs_N0_delta", False))


def _native(values) -> dict:
    values = [float(x) for x in values]
    if len(values) != 15 or not all(math.isfinite(x) for x in values):
        raise ValueError("native output must have 15 finite points")
    pre = statistics.median(values[:3])
    post = statistics.median(values[12:])
    return {"points": values, "pre_0_2_median": pre,
            "post_12_14_median": post, "post_minus_pre": post - pre}


def _method(frozen: dict, directory: Path, kind: str) -> dict:
    videos = {}
    counts = {"valid": 0, "missing": 0, "invalid": 0}
    for stem, case in frozen["cases"].items():
        condition = case["condition"]
        path = directory / f"{stem}.{'json' if kind == 'TOPReward' else 'npy'}"
        if not path.is_file():
            item = {"status": "missing", "video": stem + ".mp4"}
        else:
            try:
                if kind == "TOPReward":
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    if payload["instruction"] != GOAL or payload["prefix_lengths"] != list(range(1, 16)):
                        raise ValueError("unexpected goal or prefix lengths")
                    values = payload["prefix_rewards"]
                else:
                    import numpy as np
                    values = np.load(path, allow_pickle=False).tolist()
                item = {"status": "valid", "video": stem + ".mp4", **_native(values)}
            except Exception as exc:
                item = {"status": "invalid", "video": stem + ".mp4",
                        "error": f"{type(exc).__name__}: {exc}"}
        videos[condition] = item
        counts[item["status"]] += 1
    pairwise = {}
    for left, right, name, lower in PAIRS:
        a, b = videos[left], videos[right]
        if a["status"] != "valid" or b["status"] != "valid":
            pairwise[name] = None
        else:
            difference = a["post_minus_pre"] - b["post_minus_pre"]
            pairwise[name] = {"difference": difference,
                              "outcome": "tie" if abs(difference) <= 1e-8 else (
                                  "win" if (difference < 0 if lower else difference > 0)
                                  else "loss")}
    return {"videos": videos, "counts": counts, "pairwise": pairwise,
            "scale": "native; no per-video normalization"}


def score_scene(root: Path, top_dir: Path, robo_dir: Path) -> dict:
    freeze = root / "truth" / "frozen_test.json"
    if sha256(freeze) != (root / "truth" / "frozen_test.sha256").read_text().strip():
        raise ValueError("frozen test hash mismatch")
    frozen = json.loads(freeze.read_text(encoding="utf-8"))
    return {"TOPReward": _method(frozen, top_dir, "TOPReward"),
            "Robometer PR33 dtype compat": _method(frozen, robo_dir, "Robometer")}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--topreward-dir", type=Path, required=True)
    parser.add_argument("--robometer-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    report = score_scene(args.root, args.topreward_dir, args.robometer_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({method: data["counts"] for method, data in report.items()}))


if __name__ == "__main__":
    main()

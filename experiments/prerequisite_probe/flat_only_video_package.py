"""Six provisional flat-square development clips with isolated truth.

The videos are written to candidate_input/, never model_input/. A separate
reader check of the blue-on-red hard negative is required before promotion.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import random

from .distractor_scenes import make_flat_with_distractor
from .final_scene_videos import _record_one
from .flat_square_dev import FlatSquareSpec, INSTRUCTION
from .probe import PandaIK, SIZE, snapshot_signature
from .six_case_route_prototypes import CONDITIONS


PROTOCOL = "flat_square_only_development_v1"


def run(output: Path):
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refuse to overwrite: {output}")
    candidate = output / "candidate_input"
    truth = output / "truth"
    candidate.mkdir(parents=True)
    truth.mkdir(parents=True)
    starts = {}
    for state in ("blocked", "open"):
        env = make_flat_with_distractor(state)
        try:
            env.reset(seed=20261005)
            starts[state] = copy.deepcopy(env.unwrapped.get_state_dict())
        finally:
            env.close()
    random_ids = random.Random(20261005).sample(range(1000, 10000), len(CONDITIONS))
    records, failures = [], []
    ik = PandaIK()
    for condition, number in zip(CONDITIONS, random_ids):
        state = "blocked" if condition in ("B+", "B0") else "open"
        video = candidate / f"clip_{number}.mp4"
        try:
            row = _record_one("flat_square", condition, starts[state], video, ik)
            records.append(row)
            if row["admission_issues"]:
                failures.append({"video": video.name, "condition": condition,
                                 "issues": row["admission_issues"]})
        except Exception as exc:
            failures.append({"video": video.name, "condition": condition,
                             "error": f"{type(exc).__name__}: {exc}"})
    (truth / "mapping_and_trajectories.json").write_text(json.dumps({
        "protocol": PROTOCOL,
        "goal_predicate": FlatSquareSpec().protocol,
        "blocked_snapshot_sha256": snapshot_signature(starts["blocked"]),
        "open_snapshot_sha256": snapshot_signature(starts["open"]),
        "records": records, "failures": failures,
    }, indent=2), encoding="utf-8")
    if failures or len(records) != 6:
        raise RuntimeError(f"{len(failures)} failed/rejected clips; retained at {output}")
    manifest = {
        "protocol": PROTOCOL,
        "instruction": INSTRUCTION,
        "video_format": {"duration_s": 15, "fps": 1,
                         "width": SIZE[0], "height": SIZE[1]},
        "clips": [{"video": row["video"], "video_sha256": row["video_sha256"],
                   "sample_indices_30fps": row["sample_indices_30fps"],
                   "decoded_rgb_sha256": row["decoded_rgb_sha256"]}
                  for row in sorted(records, key=lambda item: item["video"])],
    }
    (candidate / "media_hashes.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (candidate / "instruction.txt").write_text(INSTRUCTION + "\n", encoding="utf-8")
    expected = {row["video"] for row in records} | {"instruction.txt", "media_hashes.json"}
    actual = {path.name for path in candidate.iterdir() if path.is_file()}
    if actual != expected:
        raise RuntimeError(f"input isolation failure: {actual ^ expected}")
    forbidden = ("condition", "scene_kind", "terminal", "truth", "continuation", "success")
    if any(word in (candidate / "media_hashes.json").read_text(encoding="utf-8")
           for word in forbidden):
        raise RuntimeError("truth marker in candidate_input manifest")
    (output / "STATUS.md").write_text(
        "# 平面单场景开发候选\n\n"
        "六段候选视频及逐帧哈希已生成；真值只在 truth/。"
        "叠红对抗视频的独立审读尚未封存，本目录尚未成为服务器 model_input，"
        "也不是方法冻结后的盲测。\n",
        encoding="utf-8",
    )
    return {"status": "provisional_flat_development_only",
            "videos": len(records), "issues": sum(len(row["admission_issues"]) for row in records),
            "candidate_input": str(candidate), "truth": str(truth)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output)))

"""Cross-check frozen inputs, downloaded raw scores, and report references."""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np


HERE = Path(__file__).parent
ROOT = HERE.parents[1]
ARTIFACTS = HERE / "artifacts"
RESULTS = ARTIFACTS / "model_results"
IDS = [f"{number:04d}" for number in range(1, 7)]
INSTRUCTION = "Put the blue cube in the green tray."


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check_links(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", source):
        if "://" in target or target.startswith("#"):
            continue
        local = (path.parent / target.split("#", 1)[0]).resolve()
        if not local.exists():
            raise RuntimeError(f"Broken link in {path.name}: {target}")


def main() -> None:
    truth = {row["video"]: row for row in read_json(ARTIFACTS / "truth" / "actual_frames.json")}
    for name in ("cloud_topreward_decoded_frames.json", "cloud_robometer_decoded_frames.json"):
        audit = read_json(RESULTS / name)
        assert len(audit["videos"]) == 6
        for row in audit["videos"]:
            expected = truth[row["video"]]
            assert row["decoded_frame_count"] == expected["decoded_frame_count"] == 15
            assert row["frame_shape_rgb"] == [480, 640, 3]
            assert row["decoded_rgb_sha256"] == expected["decoded_rgb_sha256"]

    for number in IDS:
        top = read_json(RESULTS / "topreward" / f"{number}.json")
        assert top["video"] == f"{number}.mp4" and top["instruction"] == INSTRUCTION
        assert top["prefix_lengths"] == list(range(1, 16))
        assert np.isfinite(np.asarray(top["prefix_rewards"], dtype=float)).all()
        assert len(top["prefix_rewards"]) == 15
        progress = np.load(RESULTS / "robometer_pr33_compat" / f"{number}.npy", allow_pickle=False)
        success = np.load(
            RESULTS / "robometer_pr33_compat" / f"{number}_success_probs.npy", allow_pickle=False
        )
        for values in (progress, success):
            assert values.shape == (15,) and np.isfinite(values).all()
        assert ((success >= 0) & (success <= 1)).all()
        assert not (RESULTS / "robometer" / f"{number}.npy").exists()

    analysis = read_json(RESULTS / "analysis_native.json")
    assert set(analysis["methods"]) == {"TOPReward", "Robometer PR33 dtype compat"}
    assert analysis["missing_methods"] == ["Robometer"]
    status = read_json(RESULTS / "status.json")
    assert status["TOPReward"]["result_status"] == "six valid original-model outputs"
    assert status["Robometer"]["result_status"] == "尚无该模型结果"

    for relative in (
        "reports/prerequisite_probe_phase1_20261004.md",
        "docs/plans/2026-10-04-prerequisite-video-input-spec.md",
        "docs/plans/2026-10-04-implicit-prerequisite-phase1.md",
    ):
        check_links(ROOT / relative)
    print("Verified six raw outputs per completed method, strict-original absence, frame hashes, and report links")


if __name__ == "__main__":
    main()

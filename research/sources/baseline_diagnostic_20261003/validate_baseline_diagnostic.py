"""Validate the new source binding without running a model."""

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    fetch = json.loads((HERE / "fetch_manifest.json").read_text(encoding="utf-8"))
    for row in fetch["files"]:
        path = HERE / row["path"]
        assert path.is_file(), path
        assert path.stat().st_size == row["bytes"], path
        assert sha256(path) == row["sha256"], path
        assert row["head_status"] == 200, path

    episodes = [json.loads(line) for line in (HERE / "contextprogress/episodes.jsonl").read_text(encoding="utf-8").splitlines()]
    subtasks = [json.loads(line) for line in (HERE / "contextprogress/subtasks.jsonl").read_text(encoding="utf-8").splitlines()]
    episode = next(row for row in episodes if row["episode_id"] == "RMBench/place_block_mat/episode1")
    manifest = json.loads((HERE / "contextprogress" / episode["manifest"]).read_text(encoding="utf-8"))
    mapping = json.loads((HERE / "contextprogress/episode_id_mapping.json").read_text(encoding="utf-8"))
    assert len(episodes) == 120 and len(subtasks) == 552
    assert episode["original_episode"] == manifest["original_episode"] == mapping["mapping"]["RMBench/place_block_mat"]["episode1"] == "episode4"
    boundaries = [[x["start_frame"], x["end_frame_exclusive"]] for x in manifest["subtasks"]]
    assert boundaries == episode["subtask_boundaries"]
    assert episode["num_frames"] == manifest["source_frame_count"] == 1056
    assert episode["num_subtasks"] == len(boundaries) == 6
    for row in subtasks:
        if row["episode_id"] == episode["episode_id"]:
            assert [row["start_frame"], row["end_frame_exclusive"]] == boundaries[row["subtask_index"]]

    video = HERE / "contextprogress" / episode["video"]
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=width,height,r_frame_rate,nb_frames", "-of", "json", str(video)
    ], text=True))
    assert int(probe["streams"][0]["nb_frames"]) == 1056
    assert probe["streams"][0]["r_frame_rate"] == "30/1"
    assert int(probe["format"]["size"]) == video.stat().st_size

    anchors = []
    for frame in [160, 180, 330, 360]:
        k = next(i for i, (start, end) in enumerate(boundaries) if start <= frame < end)
        start, end = boundaries[k]
        anchors.append({"frame": frame, "seconds_playback": round(frame / 30, 6), "subtask_index": k,
                        "native_progress_0_100": round(100 * (k + (frame - start) / (end - 1 - start)) / 6, 6)})
    assert anchors[0]["native_progress_0_100"] < anchors[2]["native_progress_0_100"]

    cases = json.loads((HERE / "case_registry.json").read_text(encoding="utf-8"))
    assert cases["frozen_before_candidate_outputs"] and len(cases["cases"]) == 3
    data = json.loads((ROOT / "experiments/data_manifest.json").read_text(encoding="utf-8"))
    assert data["version"] == "S7-screening-4"
    added = next(row for row in data["sources"] if row["name"].startswith("ContextProgress-Bench bounded"))
    for row in added["files"]:
        path = ROOT / row["path"]
        assert path.is_file() and sha256(path) == row["sha256"], path
    r2 = json.loads((HERE / "r2vlm_alfred_bench_api.json").read_text(encoding="utf-8"))
    assert r2["sha"] == "055291beea223800dd507cc139d08da16dee33e8"

    docs = [ROOT / "research/from_evonav_to_baseline_diagnostic.md", ROOT / "research/status.md", ROOT / "research/decision_log.md"]
    missing = []
    for doc in docs:
        for target in re.findall(r"\]\(([^)]+)\)", doc.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "#")):
                continue
            target = target.split("#", 1)[0]
            if target and not (doc.parent / target).exists():
                missing.append(f"{doc.relative_to(ROOT)} -> {target}")
    assert not missing, missing
    assert sha256(ROOT / "experiments/run_ledger.csv") == "45935ce6e6fe0b3a14b6528bd9ef4642c8aa0aaf650da01c74ad095492eb63de"
    assert sha256(ROOT / "research/08_pilot_report.md") == "2152a446b88fd1ae7e11bf37fa97dc7e878b2a57ec828ee646d649ce2ba2c58a"

    output = {
        "validated_utc": datetime.now(timezone.utc).isoformat(),
        "new_source_files": len(fetch["files"]),
        "new_source_bytes": sum(row["bytes"] for row in fetch["files"]),
        "hashes_and_head_status_ok": True,
        "contextprogress_index_counts": {"episodes": len(episodes), "subtasks": len(subtasks)},
        "bound_episode": episode["episode_id"],
        "bound_original_episode": "episode4",
        "video_frames": 1056,
        "video_fps": 30,
        "video_bytes": video.stat().st_size,
        "native_progress_anchors": anchors,
        "local_markdown_links_ok": True,
        "prior_run_ledger_and_pilot_report_unchanged": True,
        "r2vlm_benchmark_api_sha256": sha256(HERE / "r2vlm_alfred_bench_api.json"),
        "no_model_run": True,
    }
    (HERE / "validation.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()

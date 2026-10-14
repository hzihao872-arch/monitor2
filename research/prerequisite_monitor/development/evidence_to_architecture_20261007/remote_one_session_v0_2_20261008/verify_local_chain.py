"""Verify downloaded development evidence against its local input package."""

from __future__ import annotations

import hashlib
import io
import json
import math
import tarfile
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent
PACKAGE = SOURCE / "one_session_model_side_v0.2.0.zip"
EXPECTED_ARCHIVES = {
    "qwen_evidence.tar.gz": "43e76844c56f3926ef2afc90416b558a70b0a2997ccee35f7f477ee1b69b4b4b",
    "text_evidence.tar.gz": "a4c2aad3fad9e070f55ec1c9a3b9627ae8e4530081ba314dddafc4f694b8e1ad",
    "supplement_evidence.tar.gz": "d2610d189512a4cdf537f17681f287a1c2ca6f390caf4410fbbc12668a8738d8",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main() -> None:
    manifest = json.loads((SOURCE / "one_session_package_manifest.json").read_text(encoding="utf-8"))
    assert sha(PACKAGE.read_bytes()) == manifest["sha256"]
    for name, digest in EXPECTED_ARCHIVES.items():
        assert sha((ROOT / name).read_bytes()) == digest, name

    source_videos: dict[tuple[str, str], str] = {}
    with zipfile.ZipFile(PACKAGE) as outer:
        assert outer.testzip() is None
        bundle = json.loads(outer.read("bundle_manifest.json"))
        assert bundle["members"] == manifest["members"]
        assert set(outer.namelist()) == set(bundle["members"]) | {"bundle_manifest.json"}
        for name, digest in bundle["members"].items():
            assert sha(outer.read(name)) == digest, name
        for group in ("group_01", "group_02"):
            with zipfile.ZipFile(io.BytesIO(outer.read(group + ".zip"))) as inner:
                assert inner.testzip() is None
                assert set(inner.namelist()) == {f"{i:04d}.mp4" for i in range(1, 10)} | {
                    "instruction.txt", "manifest.jsonl", "media_hashes.json"}
                media = json.loads(inner.read("media_hashes.json"))["clips"]
                clips = {row["video"]: row for row in media}
                rows = [json.loads(line) for line in inner.read("manifest.jsonl").splitlines()]
                assert len(rows) == len(clips) == 9
                for row in rows:
                    video = row["video"]
                    assert row["sha256"] == sha(inner.read(video)) == clips[video]["video_sha256"]
                    source_videos[(group, video)] = row["sha256"]

    qwen_dir = ROOT / "qwen_evidence"
    qwen_seal = json.loads((qwen_dir / "qwen_seal.json").read_text(encoding="utf-8"))
    assert qwen_seal["complete"] and qwen_seal["recorded_calls"] == 162
    assert qwen_seal["package_sha256"] == manifest["sha256"]
    assert qwen_seal["raw_sha256"] == sha((qwen_dir / "raw.jsonl").read_bytes())
    qwen_rows = lines(qwen_dir / "raw.jsonl")
    calls = [row for row in qwen_rows if row.get("kind") in ("model_output", "model_failure")]
    assert len(calls) == 162
    assert Counter(row["stage"] for row in calls) == Counter({
        stage: 18 for stage in ("V0", "D1", "T1", "P1", "TP1", "D2", "TP2", "D3", "F3")})
    assert not [row for row in calls if row["kind"] == "model_failure"]
    for row in qwen_rows:
        if row.get("kind") == "video_input":
            assert row["video_sha256"] == source_videos[row["group"], row["video"]]

    text_dir = ROOT / "text_evidence"
    inputs = text_dir / "text_inputs"
    raw = text_dir / "text_raw"
    text_seal = json.loads((text_dir / "text_seal.json").read_text(encoding="utf-8"))
    text_manifest_bytes = (inputs / "text_probe_manifest.json").read_bytes()
    text_manifest = json.loads(text_manifest_bytes)
    assert text_seal["complete"] and text_seal["recorded_jobs"] == 72
    assert text_seal["input_manifest_sha256"] == sha(text_manifest_bytes)
    assert text_manifest["source_suite_raw_sha256"] == qwen_seal["raw_sha256"]
    assert len(text_manifest["members"]) == 72
    for entry in text_seal["files"]:
        file = raw / entry["path"]
        assert file.stat().st_size == entry["size_bytes"]
        assert sha(file.read_bytes()) == entry["sha256"]

    text_results = 0
    for variant in text_manifest["variants"]:
        for group in ("group_01", "group_02"):
            by_video = {row["video"]: row for row in lines(inputs / variant / group / "model_input" / "manifest.jsonl")}
            assert len(by_video) == 9
            for video, row in by_video.items():
                assert row["sha256"] == source_videos[group, video]
                member = next(item for item in text_manifest["members"] if
                              (item["variant"], item["group"], item["video"]) == (variant, group, video))
                assert member["instruction_sha256"] == sha(row["instruction"].encode())
                result = json.loads((raw / variant / group / (Path(video).stem + ".json")).read_text())
                assert result["video_sha256"] == row["sha256"]
                assert result["instruction"] == row["instruction"]
                assert result["prefix_lengths"] == list(range(1, 16))
                assert len(result["prefix_rewards"]) == 15
                assert all(math.isfinite(value) for value in result["prefix_rewards"])
                text_results += 1

    token_file = ROOT / "supplement_evidence" / "text_instruction_token_counts.jsonl"
    assert sha(token_file.read_bytes()) == "d5167b9d1ef5fa16120829c5f155fe163fe8256f2398e088dfbd3c43e4854cef"
    token_rows = lines(token_file)
    assert len(token_rows) == 72
    for row in token_rows:
        manifest_row = next(item for item in text_manifest["members"] if
                            (item["variant"], item["group"], item["video"]) ==
                            (row["variant"], row["group"], row["video"]))
        assert row["instruction_sha256"] == manifest_row["instruction_sha256"]

    report = {
        "scope": "development_only_not_G2",
        "package_sha256": manifest["sha256"],
        "downloaded_archive_sha256": EXPECTED_ARCHIVES,
        "qwen_raw_sha256": qwen_seal["raw_sha256"],
        "qwen_calls_verified": len(calls),
        "qwen_runtime_failures": 0,
        "text_input_manifest_sha256": text_seal["input_manifest_sha256"],
        "text_raw_files_verified": len(text_seal["files"]),
        "text_native_results_verified": text_results,
        "text_instruction_token_rows_verified": len(token_rows),
        "source_videos_verified": len(source_videos),
    }
    path = ROOT / "chain_verification.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()

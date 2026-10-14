"""Create development TOPReward task-text probes from allowed inputs only.

The official TOPReward method is called separately and remains unchanged.
These altered task strings are diagnostics, never P0 or formal method inputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path


VARIANTS = {
    "matched_neutral": "This short clip shows a fixed camera view of a tabletop scene over several seconds. Judge the visible recording in relation to the final goal. No further frames are shown.",
    "general_preparation": "This short clip may show a useful preparatory change before the final goal is visibly completed. Judge whether the visible change helps later completion of the final goal.",
}


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def raw_proposals(path: Path) -> dict[tuple[str, str], tuple[str | None, str]]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("kind") != "model_output" or row.get("stage") != "TP1":
            continue
        key = (row["group"], row["video"])
        try:
            value = json.loads(row["raw"])
            relation = value["candidate_relation"]
            predicate = relation["predicate"]
            if (row["validation"]["status"] != "valid" or
                relation["goal_relevance"] != "supported" or
                not isinstance(predicate, str) or not predicate.strip()):
                predicate = None
        except (KeyError, ValueError, TypeError):
            predicate = None
        if predicate:
            predicate = " ".join(predicate.split())[:240]
        result[key] = (predicate, hashlib.sha256(row["raw"].encode()).hexdigest())
    return result


def copy_video(source: Path, destination: Path) -> None:
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--group-01", required=True, type=Path)
    parser.add_argument("--group-02", required=True, type=Path)
    parser.add_argument("--out-root", required=True, type=Path)
    parser.add_argument("--suite-raw", type=Path, help="sealed model-side suite output; enables two automatic relation probes")
    args = parser.parse_args()
    if args.out_root.exists():
        raise FileExistsError(args.out_root)
    groups = (("group_01", args.group_01), ("group_02", args.group_02))
    proposals = raw_proposals(args.suite_raw) if args.suite_raw else {}
    variants = list(VARIANTS)
    if args.suite_raw:
        variants.extend(("auto_relation", "auto_counterclaim"))
    info = {"scope": "development_task_text_diagnostic_not_native_P0_not_G2",
            "variants": variants, "source_suite_raw_sha256": sha(args.suite_raw) if args.suite_raw else None,
            "members": []}
    for variant in variants:
        for group, source in groups:
            source_rows = [json.loads(line) for line in (source / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
            if len(source_rows) != 9:
                raise ValueError("expected nine inputs per group")
            dest = args.out_root / variant / group / "model_input"
            dest.mkdir(parents=True)
            new_rows = []
            for row in source_rows:
                video = row["video"]
                if sha(source / video) != row["sha256"]:
                    raise ValueError("source video hash mismatch")
                copy_video(source / video, dest / video)
                base = row["instruction"].strip()
                if variant in VARIANTS:
                    suffix = VARIANTS[variant]
                    proposal_hash = None
                    proposal_present = None
                else:
                    predicate, proposal_hash = proposals.get((group, video), (None, None))
                    proposal_present = bool(predicate)
                    if predicate:
                        if variant == "auto_relation":
                            suffix = f"A possible visible prerequisite proposed from this clip is: {predicate}. Check it against the video before judging the final goal."
                        else:
                            suffix = f"Counterclaim for checking: the proposed relation '{predicate}' does not matter for the final goal. Check this against the video before judging."
                    else:
                        suffix = "No reliable visible prerequisite was proposed from this clip. Judge the stated final goal from the video."
                new_rows.append({**row, "instruction": base + " " + suffix})
                info["members"].append({"variant": variant, "group": group,
                                        "video": video, "video_sha256": row["sha256"],
                                        "instruction_sha256": hashlib.sha256(new_rows[-1]["instruction"].encode()).hexdigest(),
                                        "instruction_chars": len(new_rows[-1]["instruction"]),
                                        "proposal_raw_sha256": proposal_hash,
                                        "proposal_present": proposal_present})
            (dest / "manifest.jsonl").write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in new_rows), encoding="utf-8")
            shutil.copy2(source / "media_hashes.json", dest / "media_hashes.json")
            (dest / "instruction.txt").write_text(
                "Per-video diagnostic instruction is in manifest.jsonl.\n", encoding="utf-8")
    (args.out_root / "text_probe_manifest.json").write_text(
        json.dumps(info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"variants": variants, "jobs": len(info["members"]),
                      "source_suite_raw_sha256": info["source_suite_raw_sha256"]}))


if __name__ == "__main__":
    main()

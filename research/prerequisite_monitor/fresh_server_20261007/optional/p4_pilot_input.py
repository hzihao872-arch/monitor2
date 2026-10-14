"""Make one anonymous-video input for a P4 model-call smoke test."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from .p4_seal import expected_rows, sha256


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.output.name != "model_input":
        raise ValueError("pilot output must be a new model_input directory")
    rows = expected_rows(args.source)
    row = rows["0001.mp4"]
    media = json.loads((args.source / "media_hashes.json").read_text(encoding="utf-8"))
    clip = next(item for item in media["clips"] if item["video"] == row["video"])
    args.output.mkdir(parents=True)
    shutil.copy2(args.source / row["video"], args.output / row["video"])
    (args.output / "manifest.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    (args.output / "instruction.txt").write_text(row["instruction"] + "\n", encoding="utf-8")
    (args.output / "media_hashes.json").write_text(json.dumps({"clips": [clip]}, indent=2) + "\n", encoding="utf-8")
    if sha256(args.output / row["video"]) != row["sha256"]:
        raise ValueError("pilot video SHA differs")
    print(json.dumps({"video": row["video"], "sha256": row["sha256"]}))


if __name__ == "__main__":
    main()

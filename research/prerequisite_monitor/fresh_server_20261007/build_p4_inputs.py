"""Build frozen, truth-free TOPReward instruction interventions for development clips."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

from model_side.pilot_pkg.run_relation_endpoint_pilot import inspect_inputs

HERE = Path(__file__).resolve().parent
SCENES = HERE.parent / "fresh_scenes_20261006"
ARMS = ("access_gate", "support_surface")
SUFFIXES = {
    "neutral": {
        arm: "This short recording may end before the blue cube is placed. Judge the visible change in relation to the final goal."
        for arm in ARMS
    },
    "causal_fact": {
        "access_gate": "The box can be entered only through its top opening. That opening must be unobstructed before the blue cube can reach the box floor.",
        "support_surface": "The marked elevated landing can support the blue cube only when the yellow sliding board is fully deployed beneath it.",
    },
    "credit_rule": {
        "access_gate": "The box can be entered only through its top opening. Fully opening it is useful progress toward this goal even while the blue cube remains outside.",
        "support_surface": "The marked elevated landing needs the yellow sliding board fully deployed. Deploying it is useful progress even while the blue cube remains unmoved.",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def zip_input(source: Path, output: Path) -> None:
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(source.iterdir()):
            if not path.is_file():
                raise ValueError("model_input must contain files only")
            info = zipfile.ZipInfo(path.name, date_time=(2026, 10, 7, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())


def verify(out: Path) -> dict:
    report = json.loads((out / "build_manifest.json").read_text(encoding="utf-8"))
    if report["scope"] != "P4_TOPReward_instruction_intervention_exploratory":
        raise ValueError("wrong manifest scope")
    if set(report["cells"]) != {f"{variant}/{arm}" for variant in SUFFIXES for arm in ARMS}:
        raise ValueError("missing P4 cell")
    for key, item in report["cells"].items():
        variant, arm = key.split("/")
        source = SCENES / arm / "dev_v2" / "model_input"
        target = out / variant / arm / "model_input"
        rows = inspect_inputs(target)
        original = inspect_inputs(source)
        if len(rows) != 9 or [r["sha256"] for r in rows] != [r["sha256"] for r in original]:
            raise ValueError("video identity changed: " + key)
        original_goal = (source / "instruction.txt").read_text(encoding="utf-8").strip()
        goal = original_goal + " " + SUFFIXES[variant][arm]
        if any(row["instruction"] != goal for row in rows):
            raise ValueError("instruction differs: " + key)
        if (target / "instruction.txt").read_text(encoding="utf-8").strip() != goal:
            raise ValueError("instruction.txt differs: " + key)
        if sha256(target / "media_hashes.json") != sha256(source / "media_hashes.json"):
            raise ValueError("media hashes changed: " + key)
        for name, digest in item["files"].items():
            if sha256(target / name) != digest:
                raise ValueError("input SHA differs: " + key + "/" + name)
        if sha256(out / variant / arm / "model_input.zip") != item["zip_sha256"]:
            raise ValueError("ZIP SHA differs: " + key)
        with zipfile.ZipFile(out / variant / arm / "model_input.zip") as archive:
            if set(archive.namelist()) != set(item["files"]):
                raise ValueError("ZIP members differ: " + key)
            for name, digest in item["files"].items():
                if hashlib.sha256(archive.read(name)).hexdigest() != digest:
                    raise ValueError("ZIP member SHA differs: " + key + "/" + name)
    return report


def build(out: Path) -> dict:
    if out.exists():
        raise FileExistsError(out)
    report = {"scope": "P4_TOPReward_instruction_intervention_exploratory",
              "cells": {}, "truth_uploaded": False}
    for variant, suffixes in SUFFIXES.items():
        for arm in ARMS:
            source = SCENES / arm / "dev_v2" / "model_input"
            inspect_inputs(source)
            original = [json.loads(line) for line in (source / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
            goal = (source / "instruction.txt").read_text(encoding="utf-8").strip() + " " + suffixes[arm]
            target = out / variant / arm / "model_input"
            target.mkdir(parents=True)
            for name in ("media_hashes.json", *(row["video"] for row in original)):
                shutil.copy2(source / name, target / name)
            (target / "instruction.txt").write_text(goal + "\n", encoding="utf-8")
            for row in original:
                row["instruction"] = goal
            (target / "manifest.jsonl").write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in original), encoding="utf-8")
            package = target.parent / "model_input.zip"
            zip_input(target, package)
            report["cells"][f"{variant}/{arm}"] = {
                "instruction_sha256": hashlib.sha256(goal.encode()).hexdigest(),
                "source_manifest_sha256": sha256(source / "manifest.jsonl"),
                "files": {path.name: sha256(path) for path in sorted(target.iterdir())},
                "zip_sha256": sha256(package),
            }
    (out / "build_manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return verify(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "p4_inputs")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = verify(args.output) if args.verify else build(args.output)
    print(json.dumps({"scope": result["scope"], "cells": len(result["cells"]), "verified": True}))


if __name__ == "__main__":
    main()

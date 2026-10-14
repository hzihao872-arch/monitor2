"""Read-only verification of the P6/P5/P4 development evidence."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT.parent
SCENES = PACKAGE.parent / "fresh_scenes_20261006"
sys.path.insert(0, str(PACKAGE))

from optional.p4_seal import verify as verify_p4  # noqa: E402
from optional.seal_p5 import verify as verify_p5  # noqa: E402
from p6pkg.seal import verify as verify_p6  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_archive(stage: Path) -> None:
    expected = (stage / "evidence.tar.gz.sha256").read_text(encoding="utf-8").split()[0]
    assert sha256(stage / "evidence.tar.gz") == expected, stage


def main() -> None:
    inputs = {
        arm: SCENES / arm / "dev_v2" / "model_input"
        for arm in ("access_gate", "support_surface")
    }
    stages = [ROOT / "p6" / "direct"]
    report = verify_p6(stages[0] / "raw", stages[0] / "raw_seal.json", 18, inputs)
    assert report["status"] == "complete" and report["result_count"] == 18

    for name in ("visual", "necessity"):
        stage = ROOT / "p5" / name
        stages.append(stage)
        report = verify_p5(stage / "raw", stage / "raw_seal.json", 18, inputs)
        assert report["status"] == "complete" and report["stage"] == name
        assert report["result_count"] == 18 and report["failure_count"] == 0

    for name in ("neutral", "causal_fact"):
        stage = ROOT / "p4" / name
        stages.append(stage)
        p4_inputs = {arm: stage / "inputs" / arm / "model_input" for arm in inputs}
        for arm in inputs:
            frozen = PACKAGE / "p4_inputs" / name / arm / "model_input"
            actual = p4_inputs[arm]
            assert {p.name for p in frozen.iterdir()} == {p.name for p in actual.iterdir()}
            for source in frozen.iterdir():
                assert sha256(source) == sha256(actual / source.name), source
        report = verify_p4(stage / "raw", stage / "raw_seal.json", p4_inputs)
        assert report["status"] == "complete"
        assert sum(cell["results"] for cell in report["cells"].values()) == 18

    for stage in stages:
        verify_archive(stage)

    manifest_rows = 0
    with (ROOT / "ADDITIONAL_EVIDENCE_SHA256.tsv").open("r", encoding="utf-8-sig", newline="") as stream:
        for entry in csv.DictReader(stream, delimiter="\t"):
            path = ROOT / entry["relative_path"]
            assert path.is_file() and path.stat().st_size == int(entry["size_bytes"]), path
            assert sha256(path) == entry["sha256"], path
            manifest_rows += 1

    print(json.dumps({"stages_verified": len(stages), "archive_sha_verified": len(stages),
                      "manifest_file_rows_verified": manifest_rows,
                      "model_outputs": 90, "model_failures": 0}))


if __name__ == "__main__":
    main()

"""Fresh local verification of the downloaded research evidence and links."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path


RESULTS = Path(__file__).resolve().parent
PACKAGE = RESULTS.parent
WORKSPACE = RESULTS.parents[3]
SCENES = PACKAGE.parent / "fresh_scenes_20261006"
sys.path[:0] = [str(PACKAGE), str(PACKAGE / "model_side")]

from optional.seal_p1 import verify as verify_p1  # noqa: E402
from pilot_pkg.seal_fresh_batch import verify as verify_native  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    a = SCENES / "access_gate" / "dev_v2" / "model_input"
    b = SCENES / "support_surface" / "dev_v2" / "model_input"
    native_inputs = {"access_gate": a, "support_surface": b}
    seals = [
        (RESULTS / "p0" / "raw", RESULTS / "p0" / "raw_seal.json", native_inputs, 9, 36),
        (RESULTS / "p2" / "extra" / "p2" / "raw", RESULTS / "p2" / "extra" / "p2" / "raw_seal.json", native_inputs, 9, 36),
        (
            RESULTS / "p3" / "extra" / "p3" / "raw",
            RESULTS / "p3" / "extra" / "p3" / "raw_seal.json",
            {
                "access_gate": PACKAGE / "p3_static_input" / "access_gate" / "model_input",
                "support_surface": PACKAGE / "p3_static_input" / "support_surface" / "model_input",
            },
            4,
            16,
        ),
    ]
    for raw, seal, inputs, count, results in seals:
        report = verify_native(raw, seal, inputs, count)
        assert report["status"] == "complete" and report["total_results"] == results
        assert report["total_failures"] == 0
    for name, count in (("pilot_visual", 2), ("full_visual", 18), ("full_necessity", 18)):
        root = RESULTS / "p1" / "extra" / "p1" / name
        report = verify_p1(root / "raw", root / "raw_seal.json", count, native_inputs)
        assert report["status"] == "complete" and report["result_count"] == count
        assert report["failure_count"] == 0

    hash_count = 0
    with (RESULTS / "EVIDENCE_SHA256.tsv").open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            file = WORKSPACE / row["relative_path"]
            assert file.is_file() and file.stat().st_size == int(row["size_bytes"]), file
            assert sha256(file) == row["sha256"], file
            hash_count += 1

    link_count = 0
    reports = [
        RESULTS / "FINAL_REPORT_zh.md",
        RESULTS / "p0" / "P0_RESULTS_zh.md",
        RESULTS / "p1" / "BLIND_REVIEW_BEFORE_MAP_zh.md",
        RESULTS / "p1" / "P1_UNBLINDED_zh.md",
        RESULTS / "p2" / "P2_RESULTS_zh.md",
        RESULTS / "p3" / "P3_RESULTS_zh.md",
    ]
    for report in reports:
        assert report.is_file(), report
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", report.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("#"):
                continue
            path = (report.parent / target).resolve()
            assert path.exists(), (report, target)
            link_count += 1

    p2 = json.loads((RESULTS / "p2" / "analysis_p2.json").read_text(encoding="utf-8"))
    differences = []
    flips = []
    for arm in p2["cells"].values():
        for cell in arm.values():
            differences.extend(
                point for item in cell["by_condition"].values()
                for point in item["point_difference_repeat_minus_first"]
            )
            flips.extend(item["direction_flipped"] for item in cell["pairs"].values())
    assert len(differences) == 540 and all(point == 0 for point in differences)
    assert len(flips) == 24 and not any(flips)
    print(json.dumps({"native_seals_verified": 3, "p1_seals_verified": 3,
                      "hash_rows_verified": hash_count, "report_links_verified": link_count,
                      "p2_points_identical": len(differences), "p2_pair_flips": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()

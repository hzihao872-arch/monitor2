"""Export the sealed 15-prefix text diagnostic without changing its readout."""

import csv
import json
import statistics
from pathlib import Path


root = Path(__file__).resolve().parent
audit = json.loads((root / "audit_text_probe.json").read_text(encoding="utf-8"))

with (root / "text_curve_summary.csv").open("w", newline="", encoding="utf-8-sig") as f:
    fields = [
        "variant", "arm", "condition", "case_id", "video_sha256",
        "instruction_sha256", "early_median_t0_2", "mid_median_t6_8",
        "late_median_t12_14", "mid_minus_early", "late_minus_early",
        "elapsed_ms", *[f"prefix_t{i}" for i in range(15)],
    ]
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for case in audit["cases"]:
        points = case["points"]
        assert len(points) == 15, case["case_id"]
        early = statistics.median(points[0:3])
        mid = statistics.median(points[6:9])
        late = statistics.median(points[12:15])
        writer.writerow({
            "variant": case["variant"], "arm": case["arm"],
            "condition": case["condition"], "case_id": case["case_id"],
            "video_sha256": case["video_sha256"],
            "instruction_sha256": case["instruction_sha256"],
            "early_median_t0_2": early, "mid_median_t6_8": mid,
            "late_median_t12_14": late, "mid_minus_early": mid - early,
            "late_minus_early": late - early,
            "elapsed_ms": case["elapsed_ms"],
            **{f"prefix_t{i}": v for i, v in enumerate(points)},
        })

with (root / "text_pair_summary.csv").open("w", newline="", encoding="utf-8-sig") as f:
    fields = ["variant", "arm", "left", "right", "expected_operator", "difference", "outcome"]
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows({key: pair[key] for key in fields} for pair in audit["pairs"])

assert len(audit["cases"]) == 126
assert len(audit["pairs"]) == 84
print("text_curve_summary.csv: 126 rows, 15 prefixes each")
print("text_pair_summary.csv: 84 rows")

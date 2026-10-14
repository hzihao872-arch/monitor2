"""Index sealed development evidence without calling a model or changing P0 scoring.

All condition labels and expected fields are read only on the local analysis side.
The resulting JSONL is an audit artifact and must never be used as model input.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = ROOT / "research/prerequisite_monitor/fresh_server_20261007/local_results"
ARMS = ("access_gate", "support_surface")
CONDITIONS = ("E", "S", "I_b", "N_b", "R", "H", "I_o", "N_o", "G")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def log_rows(path: Path, kind: str):
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    return [row for row in rows if row.get("kind") == kind]


def indexed_outputs(path: Path):
    return {(r["arm"], r["video"]): r for r in log_rows(path, "model_output")}


def native_result(arm: str, method: str, video: str, stage: str = "p0", variant: str = ""):
    if stage == "p0":
        path = BASE / "p0/raw" / arm / method.lower() / "native_calls.jsonl"
    else:
        path = BASE / "p4" / variant / "raw" / arm / "topreward/native_calls.jsonl"
    matches = [r for r in log_rows(path, "native_result") if r["video"] == video]
    assert len(matches) == 1, (path, video, len(matches))
    result = matches[0]
    return result, path


def main():
    p0 = read_json(BASE / "p0/analysis_p0.json")
    p2 = read_json(BASE / "p2/analysis_p2.json")
    p3 = read_json(BASE / "p3/analysis_p3.json")
    p4 = {name: read_json(BASE / "p4" / name / f"analysis_p4_{name}.json")
          for name in ("neutral", "causal_fact")}
    p5 = read_json(BASE / "p5/analysis_p5.json")
    p6 = read_json(BASE / "p6/direct/analysis_p6_direct.json")
    logs = {
        "p1_visual": BASE / "p1/extra/p1/full_visual/raw/calls.jsonl",
        "p1_necessity": BASE / "p1/extra/p1/full_necessity/raw/calls.jsonl",
        "p5_visual": BASE / "p5/visual/raw/calls.jsonl",
        "p5_necessity": BASE / "p5/necessity/raw/calls.jsonl",
        "p6_direct": BASE / "p6/direct/raw/calls.jsonl",
    }
    outputs = {key: indexed_outputs(path) for key, path in logs.items()}
    assert all(len(items) == 18 for items in outputs.values())
    rows = []
    for arm in ARMS:
        for condition in CONDITIONS:
            p0_top = p0["cells"][arm]["TOPReward"]["by_condition"][condition]
            video = p0_top["video"]
            p0_robo = p0["cells"][arm]["Robometer"]["by_condition"][condition]
            assert p0_robo["video"] == video
            case = {
                "case_id": f"{arm}/{condition}",
                "scope": "exposed_development_not_G2",
                "arm": arm,
                "condition": condition,
                "video": video,
                "expected": {
                    "relation_at_0": p5["cases"][arm][condition]["expected_initial"],
                    "relation_at_14": p5["cases"][arm][condition]["expected_final"],
                    "continuation_at_14": p5["cases"][arm][condition]["expected_future"],
                    "direction": p6["cases"][arm][condition]["expected"],
                    "provenance": rel(BASE / "p5/analysis_p5.json"),
                },
                "audit_frames": rel(BASE / "p1" / f"{arm}_state_audit.png"),
                "p0": {},
                "p4": {},
                "qa": {},
                "p2": {"same_input_raw_values": True, "batch_exact_points": 540,
                       "source": rel(BASE / "p2/analysis_p2.json")},
            }
            p0_hashes = []
            for method, cell in (("TOPReward", p0_top), ("Robometer", p0_robo)):
                native, log_path = native_result(arm, method, video)
                assert native["video_sha256"]
                p0_hashes.append(native["video_sha256"])
                result_file = BASE / "p0/raw" / arm / method.lower() / video.replace(".mp4", ".json" if method == "TOPReward" else ".npy")
                assert result_file.exists()
                case["p0"][method] = {
                    "status": cell["status"], "points_t0_t14": cell["points_t0_t14"],
                    "delta_window": cell["delta_window"], "start_median": cell["start_median_t0_t2"],
                    "end_median": cell["end_median_t12_t14"],
                    "native_field": cell["native_field"],
                    "elapsed_ms": cell["elapsed_ms"],
                    "success_head_t14": cell.get("success_head_t14"),
                    "raw_log": rel(log_path), "raw_log_sha256": sha256(log_path),
                    "raw_result": rel(result_file), "raw_result_sha256": sha256(result_file),
                    "model_path": log_rows(log_path, "configuration")[0]["model_path"],
                }
            assert len(set(p0_hashes)) == 1
            case["video_sha256"] = p0_hashes[0]
            for variant, analysis in p4.items():
                cell = analysis["cells"][arm]["by_condition"][condition]
                assert cell["video"] == video
                native, log_path = native_result(arm, "TOPReward", video, "p4", variant)
                assert native["video_sha256"] == case["video_sha256"]
                assert log_rows(log_path, "configuration")[0]["model_path"] == case["p0"]["TOPReward"]["model_path"]
                result_file = BASE / "p4" / variant / "raw" / arm / "topreward" / video.replace(".mp4", ".json")
                instruction = BASE / "p4" / variant / "inputs" / arm / "model_input/instruction.txt"
                assert native["instruction"] == instruction.read_text(encoding="utf-8").strip()
                case["p4"][variant] = {
                    "status": cell["status"], "points_t0_t14": cell["points_t0_t14"],
                    "delta_window": cell["delta_window"], "instruction": native["instruction"],
                    "instruction_sha256": sha256(instruction),
                    "raw_log": rel(log_path), "raw_log_sha256": sha256(log_path),
                    "raw_result": rel(result_file), "raw_result_sha256": sha256(result_file),
                    "same_video_and_model_as_p0": True,
                }
            p5_case = p5["cases"][arm][condition]
            p6_case = p6["cases"][arm][condition]
            for key, path in logs.items():
                item = outputs[key][(arm, video)]
                assert item["parse_status"] in ("valid", "invalid")
                case["qa"][key] = {
                    "raw": item["raw"], "parse_status": item["parse_status"],
                    "input_tokens": item.get("input_tokens"), "output_tokens": item.get("output_tokens"),
                    "elapsed_ms": item.get("elapsed_ms"), "peak_vram_bytes": item.get("peak_vram_bytes"),
                    "raw_log": rel(path), "raw_log_sha256": sha256(path),
                }
            case["qa"]["p5_visual"].update({
                "initial": p5_case["visual_initial"], "middle": p5_case["visual_middle"],
                "final": p5_case["visual_final"],
                "initial_exact": p5_case["initial_exact"], "final_exact": p5_case["final_exact"],
            })
            case["qa"]["p5_necessity"].update({
                "answer": p5_case["future_answer"], "exact": p5_case["future_exact"]})
            case["qa"]["p6_direct"].update({
                "answer": p6_case["observed"], "label_match": p6_case["matches_label"],
                "evidence_seconds": p6_case.get("evidence_seconds")})
            if condition in ("N_b", "S", "N_o", "G"):
                case["p3_static"] = {
                    method: {"points_t0_t14": p3["cells"][arm][method]["by_condition"][condition]["points_t0_t14"],
                             "t14": p3["cells"][arm][method]["by_condition"][condition]["t14"]}
                    for method in ("TOPReward", "Robometer")
                }
            rows.append(case)
    assert len(rows) == 18 and len({r["case_id"] for r in rows}) == 18
    differences = [value for arm in ARMS for method in ("TOPReward", "Robometer")
                   for condition in CONDITIONS
                   for value in p2["cells"][arm][method]["by_condition"][condition]
                   ["point_difference_repeat_minus_first"]]
    assert len(differences) == 540 and all(value == 0 for value in differences)
    assert all(p2["cells"][arm][method]["pairs"][pair]["direction_flipped"] is False
               for arm in ARMS for method in ("TOPReward", "Robometer")
               for pair in p2["cells"][arm][method]["pairs"])
    out = HERE / "evidence_case_index.jsonl"
    out.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    manifest = {
        "scope": "exposed_development_not_G2",
        "rows": len(rows), "output": rel(out), "output_sha256": sha256(out),
        "source_analysis": {rel(p): sha256(p) for p in (
            BASE / "p0/analysis_p0.json", BASE / "p2/analysis_p2.json",
            BASE / "p3/analysis_p3.json", BASE / "p5/analysis_p5.json",
            BASE / "p6/direct/analysis_p6_direct.json",
            BASE / "p4/neutral/analysis_p4_neutral.json",
            BASE / "p4/causal_fact/analysis_p4_causal_fact.json")},
        "verified_seal_checkers": [rel(BASE / "verify_final.py"), rel(BASE / "verify_additional.py")],
    }
    (HERE / "evidence_index_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "output_sha256": manifest["output_sha256"],
                      "same_video_and_model_p4": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()

"""Build a read-only index of sealed development evidence.

This script never imports a Monitor runner or writes inside model_input/truth.
First-error annotations are human post-score audit labels, not model causes.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from experiments.prerequisite_probe.run_caption_slots import direction as caption_direction, parse_facts, progress as caption_progress


OUT = Path(__file__).resolve().parent
REPLAY = ROOT / "research/prerequisite_monitor/development/replay_saved_20261005.json"
NATIVE = ROOT / "experiments/prerequisite_probe/artifacts/unseen_analysis_native.json"
GOAL = "Put the blue cube in the green tray."
CONDS = ("B+", "B0", "U0", "H-", "G+", "N0")
FACTS = {
    "old": ["red cube in tray→out; blue outside", "red cube lifted→returned to tray", "red cube moved outside tray; opening unchanged", "red cube outside→tray center", "blue cube table→tray", "objects stationary"],
    "s01": ["bar across tray opening→removed", "bar lifted→returned across opening", "bar moved outside tray", "bar outside→across tray opening", "blue cube table→tray; gripper partly occludes", "objects stationary"],
    "s02": ["bar over blue grasp source→removed", "bar lifted→returned over blue source", "bar moved outside grasp source", "bar outside→over blue grasp source", "blue cube table→tray", "objects stationary"],
}
SCENE_STATUS = {
    "old": "policy_dependent_only; success predicate lacks support/release/stability",
    "s01": "strict_necessity_not_admitted; no-bar-move off-center valid endpoint candidate",
    "s02": "strict_necessity_not_admitted; side grasp route not excluded",
}

# Only observed earliest links. A blank annotation means the original text and
# audited frames do not support assigning that link as an error.
ISSUES = {
    "old": {
        "B+": {"D": "relevance_relation", "P": "relevance_relation", "F": "relevance_relation", "D2_review": "relevance_relation", "H0": "aggregation_abstention"},
        "B0": {"P": "endpoint_relation", "F": "endpoint_relation", "H0": "inherited_endpoint_relation"},
        "U0": {"P": "relevance_relation", "F": "relevance_relation", "H0": "inherited_relevance_relation"},
        "H-": {"D": "relevance_relation", "P": "endpoint_relation", "F": "relevance_relation", "D2_review": "relevance_relation", "H0": "aggregation_abstention"},
        "G+": {"P": "relevance_relation", "H0": "aggregation_abstention"},
        "N0": {"P": "relevance_relation", "F": "relevance_relation", "H0": "inherited_relevance_relation"},
    },
    "s01": {
        "B+": {"D": "relevance_relation", "P": "relevance_relation", "F": "relevance_relation", "D2_review": "relevance_relation", "H0": "inherited_relevance_relation"},
        "B0": {"P": "relevance_relation", "H0": "aggregation_abstention"},
        "U0": {"P": "relevance_relation", "H0": "aggregation_abstention"},
        "H-": {"D": "relevance_relation", "P": "relevance_relation", "F": "relevance_relation", "D2_review": "relevance_relation", "H0": "aggregation_abstention"},
        "G+": {"H0": "aggregation_abstention"},
    },
    "s02": {
        "B+": {"D": "relevance_relation", "D2_review": "relevance_relation"},
        "B0": {"P": "endpoint_relation", "F": "endpoint_relation", "H0": "inherited_endpoint_relation"},
        "U0": {"P": "endpoint_relation", "H0": "aggregation_abstention"},
        "H-": {"D": "relevance_relation", "P": "endpoint_relation", "F": "endpoint_relation", "D2_review": "relevance_relation", "H0": "inherited_endpoint_relation"},
        "G+": {"H0": "aggregation_abstention"},
    },
}
CAP_ISSUES = {
    "s01": ["visual_self_contradiction", "source_target_binding", "", "source_target_binding", "target_vs_non_goal_binding", "fact_extraction_gap"],
    "s02": ["spatial_relation_omission", "source_target_binding", "", "spatial_relation_omission", "target_vs_non_goal_binding", "fact_extraction_gap"],
}


def issue_reason(scene: str, condition: str, issue: str) -> str:
    if not issue:
        return "No first error supported by this output and audited endpoints; correct direction alone is not proof of necessity."
    if issue == "relevance_relation":
        relevant = "source grasp region" if scene == "s02" else "destination opening"
        return f"Output chose goal completion or arm proximity instead of the changed non-goal object at the {relevant}."
    if issue in ("endpoint_relation", "inherited_endpoint_relation"):
        return "Output/derived decision says access improved although the non-goal object returns or newly occupies the relevant endpoint."
    if issue == "inherited_relevance_relation":
        return "Derived H0 direction inherits P/F's irrelevant relation; agreement does not validate goal relevance."
    if issue == "aggregation_abstention":
        return "P/F endpoint or goal fields disagree, so deterministic H0 abstains; this is no new visual observation."
    if issue == "visual_self_contradiction":
        return "Visual caption calls the initial opening both occupied and unoccupied."
    if issue == "source_target_binding":
        return "Caption recognizes motion but canonical source/destination slots lose or invent the observed endpoint."
    if issue == "spatial_relation_omission":
        return "Caption names the moved bar but omits its crossing of the blue-object grasp region."
    if issue == "target_vs_non_goal_binding":
        return "Canonical non-goal slot treats the goal blue object as a non-goal obstacle."
    if issue == "fact_extraction_gap":
        return "Caption says static, but all four non-goal relation slots are unknown; string fallback masks missing facts."
    return issue


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def base(scene: str, i: int, method: str, path: Path) -> dict:
    mechanism = "source" if scene in ("s02", "unseen_pickup_gate_v2", "unseen_pickup_gate_shifted") else "target"
    return dict(scene=scene, mechanism=mechanism, condition=CONDS[i], video=f"{i+1:04}.mp4", method=method,
                goal=GOAL, visible_0_14=FACTS.get(scene, ["frame audit available in truth/contact_sheet.png"] * 6)[i],
                construct_status=SCENE_STATUS.get(scene, "policy_dependent_only; strict necessity not admitted"),
                raw_source=rel(path), raw_source_sha256=digest(path),
                raw_text="", object_binding="not exposed", candidate_relation="not exposed",
                before_satisfied="", after_satisfied="", goal_relevance="not independently established",
                alternative_route="not excluded", direction="", evidence_seconds="",
                structural_validity="not applicable", abstained="", input_tokens="", output_tokens="",
                elapsed_ms="", native_delta="", first_supported_issue="", later_issue="",
                reason="", attribution_limit="old fixed-policy direction is not strict necessity truth")


def main() -> None:
    replay = json.loads(REPLAY.read_text(encoding="utf-8"))
    native = json.loads(NATIVE.read_text(encoding="utf-8"))
    rows = []
    sources = []
    v12_names = {"old": "old_dev_v12_full.jsonl", "s01": "s01.monitor.jsonl", "s02": "s02.monitor.jsonl"}
    for scene, name in v12_names.items():
        group = replay["v12"][name]
        path = ROOT / group["source"]
        assert digest(path) == group["sha256"] and not group["differences"]
        sources.append({"source": rel(path), "sha256": group["sha256"], "replay_differences": 0})
        for i in range(6):
            video = f"{i+1:04}.mp4"
            for method, item in group["cases"][video].items():
                row = base(scene, i, method, path)
                issue = ISSUES.get(scene, {}).get(CONDS[i], {}).get(method, "")
                if method == "H0":
                    row.update(direction=item["replay"]["direction"], abstained=str(item["replay"]["direction"] == "uncertain"),
                               structural_validity="derived", first_supported_issue=issue,
                               reason=issue_reason(scene, CONDS[i], issue) + " " + item["replay"].get("reason", ""),
                               attribution_limit="derived from P/F; no new visual observation")
                else:
                    rec = item["record"]
                    row.update(raw_text=item["raw"], object_binding=rec.get("relation", ""),
                               candidate_relation=rec.get("relation", ""),
                               before_satisfied=rec.get("before_satisfied", ""), after_satisfied=rec.get("after_satisfied", ""),
                               goal_relevance=rec.get("alternative_route", ""), alternative_route=rec.get("alternative_route", ""),
                               direction=item["direction"], evidence_seconds="|".join(str(e["second"]) for e in rec.get("evidence", [])),
                               structural_validity=item["replay_validity"], abstained=str(item["direction"] == "uncertain"),
                               input_tokens=item["input_tokens"], output_tokens=item["output_tokens"],
                               first_supported_issue=issue,
                               reason=issue_reason(scene, CONDS[i], issue))
                    if issue and row["direction"] in ("positive", "negative", "zero"):
                        row["later_issue"] = "direction may inherit first relation error; no separate mapper fault established"
                rows.append(row)
    for scene in ("s01", "s02"):
        group = replay["caption"][scene]
        path = ROOT / group["source"]
        assert digest(path) == group["sha256"] and not group["differences"]
        sources.append({"source": rel(path), "sha256": group["sha256"], "replay_differences": 0})
        for i in range(6):
            item = group["cases"][f"{i+1:04}.mp4"]
            facts = item["replay_facts"]
            row = base(scene, i, "caption_slots", path)
            row.update(raw_text="visual: " + item["visual_raw"] + "\ncanonical: " + item["canonical_raw"],
                       object_binding=item["visual_raw"], candidate_relation="destination/source non-goal slots",
                       before_satisfied=f"dst={facts['destination_non_goal_0']};src={facts['source_non_goal_0']}",
                       after_satisfied=f"dst={facts['destination_non_goal_14']};src={facts['source_non_goal_14']}",
                       goal_relevance="fixed slot mapping; strict relevance not proved", direction=item["replay_direction"],
                       evidence_seconds="0|14 (caption; no explicit citation)", structural_validity="valid" if not item["replay_errors"] else "invalid",
                       abstained=str(item["replay_direction"] == "uncertain"),
                       input_tokens=item["visual_input_tokens"] + item["canonical_input_tokens"],
                       first_supported_issue=CAP_ISSUES[scene][i],
                       reason=issue_reason(scene, CONDS[i], CAP_ISSUES[scene][i]) + " " + item["replay_reason"],
                       attribution_limit="caption relation substitution in replay is privileged diagnostic only")
            rows.append(row)
    old_caption = ROOT / "research/prerequisite_monitor/new_test_candidates/cloud_results_20261005/server_results/old_dev_caption_slots_full.jsonl"
    old_calls = [json.loads(line) for line in old_caption.read_text(encoding="utf-8").splitlines() if line]
    grouped = {}
    for item in old_calls:
        if item.get("kind") in ("visual_call", "canonical_call", "result"):
            grouped.setdefault(item["video"], {})[item["kind"]] = item
    old_caption_differences = 0
    old_issues = ("", "endpoint_relation", "source_target_binding", "", "target_vs_non_goal_binding", "fact_extraction_gap")
    for i in range(6):
        group = grouped[f"{i+1:04}.mp4"]
        visual, canonical, saved = (group[k] for k in ("visual_call", "canonical_call", "result"))
        facts, errors = parse_facts(canonical["raw"])
        label, reason = caption_direction(facts, visual["raw"], errors)
        if (facts, errors, label, reason, caption_progress(facts, label)) != (
                saved["facts"], saved["errors"], saved["direction"], saved["reason"], saved["points"]):
            old_caption_differences += 1
        row = base("old", i, "caption_slots", old_caption)
        row.update(raw_text="visual: " + visual["raw"] + "\ncanonical: " + canonical["raw"],
                   object_binding=visual["raw"], candidate_relation="destination/source non-goal slots",
                   before_satisfied=f"dst={facts['destination_non_goal_0']};src={facts['source_non_goal_0']}",
                   after_satisfied=f"dst={facts['destination_non_goal_14']};src={facts['source_non_goal_14']}",
                   goal_relevance="fixed slot mapping; strict relevance not proved", direction=label,
                   evidence_seconds="0|14 (caption; no explicit citation)",
                   structural_validity="valid" if not errors else "invalid", abstained=str(label == "uncertain"),
                   input_tokens=visual.get("input_tokens", 0) + canonical.get("input_tokens", 0),
                   first_supported_issue=old_issues[i],
                   reason=issue_reason("old", CONDS[i], old_issues[i]) + " " + reason,
                   attribution_limit="post-score caption interpretation; no new model call")
        rows.append(row)
    sources.append({"source": rel(old_caption), "sha256": digest(old_caption),
                    "replay_differences": old_caption_differences})
    assert old_caption_differences == 0
    family_scene = {"unseen_offset_cell": "target", "unseen_mirror_cell": "target", "unseen_left_cell": "target",
                    "unseen_rear_cell": "target", "unseen_pickup_gate_v2": "source", "unseen_pickup_gate_shifted": "source"}
    for family, mechanism in family_scene.items():
        for method in ("topreward", "robometer_pr33_compat"):
            records = native["families"][family]["methods"][method]["videos"]
            for i in range(6):
                stem = f"{i+1:04}"
                ext = "json" if method == "topreward" else "npy"
                path = ROOT / f"experiments/prerequisite_probe/artifacts/{family}/model_results/{method}/{stem}.{ext}"
                row = base(family, i, method, path)
                row.update(visible_0_14=f"{mechanism}-end family; see truth/contact_sheet.png (post-score audit only)",
                           construct_status="policy_dependent_only; strict necessity not admitted",
                           native_delta=records[stem]["post_minus_pre"], direction="native_curve_delta_only",
                           structural_validity="15-point native output", abstained="not exposed",
                           reason="no entity/relation intermediate output; first internal link cannot be localized",
                           attribution_limit="native score is observable; internal perception/relevance/mapping cannot be assigned")
                rows.append(row)
    # Old/s01/s02 native outputs are preserved separately from six-family analysis.
    for scene, root in (("old", ROOT / "experiments/prerequisite_probe/artifacts/model_results"),
                        ("s01", ROOT / "research/prerequisite_monitor/new_test_candidates/cloud_results_20261005/server_results"),
                        ("s02", ROOT / "research/prerequisite_monitor/new_test_candidates/cloud_results_20261005/server_results")):
        for method in ("topreward", "robometer_pr33_compat"):
            for i in range(6):
                stem = f"{i+1:04}"
                if scene == "old":
                    path = root / method / (stem + (".json" if method == "topreward" else ".npy"))
                else:
                    path = root / f"{scene}.{method}" / (stem + (".json" if method == "topreward" else ".npy"))
                if not path.exists():
                    continue
                row = base(scene, i, method, path)
                row.update(direction="native_curve_only", structural_validity="native output present", abstained="not exposed",
                           reason="no entity/relation intermediate output; first internal link cannot be localized",
                           attribution_limit="native score is observable; internal perception/relevance/mapping cannot be assigned")
                rows.append(row)
    fields = list(rows[0])
    target = OUT / "case_attribution.csv"
    with target.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    manifest = {"rows": len(rows), "by_method": dict(Counter(x["method"] for x in rows)),
                "by_first_issue": dict(Counter(x["first_supported_issue"] or "none_or_not_localizable" for x in rows)),
                "sources": sources, "replay_source": {"path": rel(REPLAY), "sha256": digest(REPLAY)},
                "native_analysis_source": {"path": rel(NATIVE), "sha256": digest(NATIVE)},
                "case_csv_sha256": digest(target)}
    (OUT / "stage_A_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    grouped_counts = {
        "by_condition_issue": dict(Counter(f"{r['condition']}|{r['first_supported_issue'] or 'none_or_not_localizable'}" for r in rows)),
        "by_method_issue": dict(Counter(f"{r['method']}|{r['first_supported_issue'] or 'none_or_not_localizable'}" for r in rows)),
        "by_mechanism_issue": dict(Counter(f"{r['mechanism']}|{r['first_supported_issue'] or 'none_or_not_localizable'}" for r in rows)),
        "by_condition_mechanism_method_issue": dict(Counter(
            f"{r['condition']}|{r['mechanism']}|{r['method']}|{r['first_supported_issue'] or 'none_or_not_localizable'}"
            for r in rows)),
        "denominator_note": "Output rows, not independent mechanisms. Native no-trace rows are not internally attributable; old causal labels remain policy-dependent.",
    }
    (OUT / "stage_A_counts.json").write_text(json.dumps(grouped_counts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("rows", "by_method", "by_first_issue")}, ensure_ascii=False))


if __name__ == "__main__":
    main()

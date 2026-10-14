"""Read-only replay of sealed development outputs; never invokes a model.

The human substitutions below are diagnostic privileged information. They are
kept in this file, separate from Monitor runners and model input manifests.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from experiments.prerequisite_probe.monitor_contract import (
    combine_hybrid, event_direction, hybrid_progress, parse_and_validate,
    render_progress, unknown_progress,
)
from experiments.prerequisite_probe.run_caption_slots import (
    canonical_prompt, direction, parse_facts, progress,
)


ROOT = Path(__file__).resolve().parents[3]
SAVED = ROOT / "research/prerequisite_monitor/new_test_candidates/cloud_results_20261005/server_results"
OUT = Path(__file__).resolve().parent / "replay_saved_20261005.json"

# Post-score visual audit of the first and last frames; never a model score.
# Tuple: destination at 0/14, source at 0/14, goal at 0/14.
HUMAN_FACTS = {
    "s01": {
        "0001": ("true", "false", "false", "false", "false", "false"),
        "0002": ("true", "true", "false", "false", "false", "false"),
        "0003": ("false", "false", "false", "false", "false", "false"),
        "0004": ("false", "true", "false", "false", "false", "false"),
        "0005": ("false", "false", "false", "false", "false", "true"),
        "0006": ("false", "false", "false", "false", "false", "false"),
    },
    "s02": {
        "0001": ("false", "false", "true", "false", "false", "false"),
        "0002": ("false", "false", "true", "true", "false", "false"),
        "0003": ("false", "false", "false", "false", "false", "false"),
        "0004": ("false", "false", "false", "true", "false", "false"),
        "0005": ("false", "false", "false", "false", "false", "true"),
        "0006": ("false", "false", "false", "false", "false", "false"),
    },
}
HUMAN_CAPTIONS = {
    "s01": {
        "0001": "The robot moved the red bar from across the green tray opening to outside it. The blue cube stayed outside the tray. At second 14 the bar no longer crosses the opening.",
        "0002": "The robot lifted the red bar from across the green tray opening and returned it across the same opening by second 14. The blue cube stayed outside.",
        "0003": "The robot moved the red bar outside the green tray from one table location to another. The tray opening remained clear and the blue cube stayed outside.",
        "0004": "The robot moved the red bar from outside the green tray to across its opening. The blue cube stayed outside the tray.",
        "0005": "The robot moved the blue cube from the table into the green tray. The red bar remained outside the tray.",
        "0006": "No object moved. The blue cube remained outside the green tray and the red bar stayed outside its opening.",
    },
    "s02": {
        "0001": "The robot moved the red crossbar from the two gray supports above the blue cube to outside the blue cube's grasp area. The blue cube stayed on the table.",
        "0002": "The robot lifted the red crossbar from the supports above the blue cube and returned it to the same supports by second 14. The blue cube stayed on the table.",
        "0003": "The robot moved the red crossbar between locations outside the blue cube's grasp area. The area above the blue cube remained clear.",
        "0004": "The robot moved the red crossbar from outside the blue cube's grasp area onto the two supports above the blue cube. The blue cube stayed on the table.",
        "0005": "The robot moved the blue cube from the table into the green tray. The red crossbar stayed outside the blue cube's initial grasp area.",
        "0006": "No object moved. The blue cube remained on the table and the crossbar stayed outside its grasp area.",
    },
}
FACT_KEYS = (
    "destination_non_goal_0", "destination_non_goal_14",
    "source_non_goal_0", "source_non_goal_14",
    "goal_complete_0", "goal_complete_14",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def v12_replay(path: Path) -> dict:
    original = rows(path)
    cases: dict[str, dict] = {}
    differences = []
    for row in original:
        if row.get("kind") != "model_call":
            continue
        video, method = row["video"], row["method"]
        replay = parse_and_validate(row["raw"], {0, 2, 4, 6, 8, 10, 12, 14})
        direction_now = event_direction(replay["record"]) if replay["validity"] == "valid" else "invalid"
        cases.setdefault(video, {})[method] = {
            "raw": row["raw"], "record": replay["record"],
            "saved_validity": row.get("validity"), "replay_validity": replay["validity"],
            "saved_errors": row.get("errors", []), "replay_errors": replay["errors"],
            "direction": direction_now,
            "replay_points": render_progress(replay["record"]) if replay["validity"] == "valid" else None,
            "input_tokens": row.get("input_tokens"), "output_tokens": row.get("output_tokens"),
        }
        if row.get("validity") != replay["validity"] or row.get("errors", []) != replay["errors"]:
            differences.append(f"{video}:{method}:parse")
    for video, methods in cases.items():
        p = parse_and_validate(methods["P"]["raw"], {0, 2, 4, 6, 8, 10, 12, 14})
        f = parse_and_validate(methods["F"]["raw"], {0, 2, 4, 6, 8, 10, 12, 14})
        hybrid = combine_hybrid(p, f)
        saved = next(r for r in original if r.get("kind") == "hybrid" and r["video"] == video)
        methods["H0"] = {"replay": hybrid, "saved_direction": saved.get("direction")}
        if saved.get("direction") != hybrid["direction"]:
            differences.append(f"{video}:H0:direction")
        for method in ("D", "P", "F", "D2_review"):
            saved_points = next(r["points"] for r in original if r.get("kind") == "progress"
                                and r["video"] == video and r["method"] == method)
            replay_points = methods[method]["replay_points"] or unknown_progress()
            if saved_points != replay_points:
                differences.append(f"{video}:{method}:progress")
        saved_hybrid_points = next(r["points"] for r in original if r.get("kind") == "progress"
                                   and r["video"] == video and r["method"] == "H0")
        if saved_hybrid_points != hybrid_progress(hybrid):
            differences.append(f"{video}:H0:progress")
    return {"source": str(path.relative_to(ROOT)), "sha256": digest(path),
            "differences": differences, "cases": cases}


def caption_replay(path: Path, scene: str) -> dict:
    original = rows(path)
    by_video: dict[str, dict] = {}
    differences = []
    for row in original:
        if row.get("kind") in ("visual_call", "canonical_call", "result"):
            by_video.setdefault(row["video"], {})[row["kind"]] = row
    result = {}
    for video, group in sorted(by_video.items()):
        visual, canonical, saved = (group[k] for k in ("visual_call", "canonical_call", "result"))
        facts, errors = parse_facts(canonical["raw"])
        label, reason = direction(facts, visual["raw"], errors)
        points = progress(facts, label)
        if (label, reason, errors, points) != (saved["direction"], saved["reason"], saved["errors"], saved["points"]):
            differences.append(video)
        human = dict(zip(FACT_KEYS, HUMAN_FACTS[scene][video[:4]]))
        human_direction, human_reason = direction(human, visual["raw"], [])
        corrected_caption = HUMAN_CAPTIONS[scene][video[:4]]
        result[video] = {
            "visual_raw": visual["raw"], "canonical_raw": canonical["raw"],
            "saved_facts": saved["facts"], "replay_facts": facts,
            "replay_errors": errors, "saved_direction": saved["direction"],
            "replay_direction": label, "replay_reason": reason,
            "correct_relation_privileged": human,
            "direction_after_relation_substitution_diagnostic_only": human_direction,
            "relation_substitution_reason": human_reason,
            "corrected_caption_privileged": corrected_caption,
            "caption_only_canonical_prompt_unrun": canonical_prompt(
                "Put the blue cube in the green tray.", corrected_caption),
            "caption_only_result": "unrun: canonical LLM call would be required",
            "visual_input_tokens": visual.get("input_tokens"),
            "canonical_input_tokens": canonical.get("input_tokens"),
        }
    return {"source": str(path.relative_to(ROOT)), "sha256": digest(path),
            "differences": differences, "cases": result}


def main() -> None:
    output = {
        "scope": "post-score, development-only replay; no model inference and no Monitor input modification",
        "v12": {name: v12_replay(SAVED / name) for name in
                ("old_dev_v12_full.jsonl", "s01.monitor.jsonl", "s02.monitor.jsonl")},
        "caption": {scene: caption_replay(SAVED / f"{scene}.caption_slots.jsonl", scene)
                    for scene in ("s01", "s02")},
    }
    OUT.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT),
                      "differences": {f"{kind}/{name}": item["differences"]
                                      for kind, group in output.items() if isinstance(group, dict)
                                      for name, item in group.items() if isinstance(item, dict)}}, ensure_ascii=False))


if __name__ == "__main__":
    main()

"""Local-only P5 descriptive scoring after both raw answers are sealed."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from optional.seal_p5 import sha256, verify

ARMS = ("access_gate", "support_surface")
FINAL_STATE = {"E": "ready", "S": "partial", "I_b": "blocked", "N_b": "blocked",
               "R": "blocked", "H": "blocked", "I_o": "ready", "N_o": "ready", "G": "ready"}
INITIAL_STATE = {"E": "blocked", "S": "blocked", "I_b": "blocked", "N_b": "blocked",
                 "R": "blocked", "H": "ready", "I_o": "ready", "N_o": "ready", "G": "ready"}
FUTURE = {"E": "yes", "S": "no", "I_b": "no", "N_b": "no", "R": "no",
          "H": "no", "I_o": "yes", "N_o": "yes", "G": "already_done"}


def outcome_rows(path: Path) -> dict[tuple[str, str], dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {(row["arm"], row["video"]): row for row in rows if row.get("kind") in ("model_output", "model_failure")}


def score(visual_root: Path, visual_seal: Path, future_root: Path, future_seal: Path,
          inputs: dict[str, Path], truth_root: Path) -> dict:
    for raw, seal, stage in ((visual_root, visual_seal, "visual"),
                             (future_root, future_seal, "necessity")):
        report = verify(raw, seal, 18, inputs)
        if report["status"] == "incomplete" or report["stage"] != stage:
            raise ValueError("incomplete P5 stage; keep truth closed")
    visual = outcome_rows(visual_root / "calls.jsonl")
    future = outcome_rows(future_root / "calls.jsonl")
    cases = {}
    truth_hashes = {}
    for arm in ARMS:
        truth_path = truth_root / arm / "dev_v2" / "truth" / "condition_map.json"
        mapping = json.loads(truth_path.read_text(encoding="utf-8"))
        truth_hashes[arm] = sha256(truth_path)
        cases[arm] = {}
        for video, condition in mapping.items():
            v = visual[(arm, video)]
            f = future[(arm, video)]
            vp = v.get("parsed", {}) if v.get("parse_status") == "valid" else {}
            fp = f.get("parsed", {}) if f.get("parse_status") == "valid" else {}
            cases[arm][condition] = {
                "video": video, "expected_initial": INITIAL_STATE[condition],
                "expected_final": FINAL_STATE[condition], "expected_future": FUTURE[condition],
                "visual_initial": vp.get("state_initial"), "visual_middle": vp.get("state_middle"),
                "visual_final": vp.get("state_final"), "future_answer": fp.get("answer"),
                "initial_exact": vp.get("state_initial") == INITIAL_STATE[condition],
                "final_exact": vp.get("state_final") == FINAL_STATE[condition],
                "future_exact": fp.get("answer") == FUTURE[condition],
                "visual_raw": v.get("raw"), "future_raw": f.get("raw"),
                "visual_status": v.get("parse_status", v["kind"]),
                "future_status": f.get("parse_status", f["kind"]),
            }
    return {"scope": "P5_prompt_disambiguation_development_only_not_G2",
            "visual_seal_sha256": sha256(visual_seal), "future_seal_sha256": sha256(future_seal),
            "truth_map_sha256": truth_hashes, "cases": cases,
            "counts": {arm: {"initial_exact": sum(r["initial_exact"] for r in cases[arm].values()),
                              "final_exact": sum(r["final_exact"] for r in cases[arm].values()),
                              "future_exact": sum(r["future_exact"] for r in cases[arm].values()),
                              "open_unfinished_yes": sum(cases[arm][c]["future_answer"] == "yes" for c in ("E", "I_o", "N_o"))}
                       for arm in ARMS},
            "limits": "Keyword exactness is descriptive; raw visual claims and cited frames require human review. Prompt intervention is not native-method internals or G2."}


def main() -> None:
    parser = argparse.ArgumentParser()
    for name in ("visual_raw", "visual_seal", "future_raw", "future_seal", "access_input",
                 "support_input", "truth_root", "output"):
        parser.add_argument("--" + name.replace("_", "-"), required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    inputs = {"access_gate": args.access_input, "support_surface": args.support_input}
    report = score(args.visual_raw, args.visual_seal, args.future_raw, args.future_seal,
                   inputs, args.truth_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["counts"]))


if __name__ == "__main__":
    main()

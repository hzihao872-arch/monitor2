"""Label-side physical screening of a candidate scene; never runs the Monitor."""

from __future__ import annotations

import argparse
import copy
import json
import traceback
from pathlib import Path

from .probe import PandaIK, SCENE_LAYOUTS, make_env
from .produce import actor_pos, record_case, run_blue_continuation


def screen(scene: str, output: Path, seeds: range) -> None:
    if scene not in SCENE_LAYOUTS:
        raise ValueError(scene)
    output.parent.mkdir(parents=True, exist_ok=True)
    ik = PandaIK()
    with output.open("w", encoding="utf-8") as stream:
        for start, cases in (("blocked", ("B+", "B0")),
                             ("open", ("U0", "H-"))):
            env = make_env(scene, start)
            try:
                env.reset(seed=20261004)
                initial = copy.deepcopy(env.unwrapped.get_state_dict())
                no_action = record_case(env, "N0", output.parent, initial,
                                        render=False, ik=ik)
                control = copy.deepcopy(env.unwrapped.get_state_dict())
                baseline = [run_blue_continuation(env, control, ik, seed)
                            for seed in seeds]
                for condition in cases:
                    try:
                        result = record_case(env, condition, output.parent, initial,
                                             render=False, ik=ik)
                        post = copy.deepcopy(env.unwrapped.get_state_dict())
                        after = [run_blue_continuation(env, post, ik, seed)
                                 for seed in seeds]
                        entry = {
                            "scene": scene, "condition": condition, "start": start,
                            "baseline": baseline, "after": after,
                            "preparation": result,
                            "no_action_preparation": no_action,
                            "status": "complete",
                        }
                    except Exception as exc:
                        entry = {"scene": scene, "condition": condition,
                                 "start": start, "status": "runtime_failure",
                                 "error": str(exc), "traceback": traceback.format_exc()}
                    stream.write(json.dumps(entry) + "\n")
                    stream.flush()
                    print(f"{scene} {condition}: {entry['status']}", flush=True)
            finally:
                env.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", required=True, choices=tuple(SCENE_LAYOUTS))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=3)
    args = parser.parse_args()
    if args.seeds <= 0:
        parser.error("--seeds must be positive")
    screen(args.scene, args.output, range(args.seeds))


if __name__ == "__main__":
    main()

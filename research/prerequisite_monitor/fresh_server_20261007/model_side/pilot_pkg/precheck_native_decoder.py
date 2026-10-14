"""Read-only Robometer decoder pixel check before any new-scene model call."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from .run_relation_endpoint_pilot import inspect_inputs


def check_video(video: Path, expected: list[str], script: Path, python: Path, repo: Path,
                decoder_mode: str = "native_script") -> dict:
    if decoder_mode == "native_script":
        code = (
            "import hashlib,importlib.util,json,sys;"
            "s=importlib.util.spec_from_file_location('rbm_local',sys.argv[1]);"
            "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
            "f=m.load_frames_input(sys.argv[2],fps=1.0,max_frames=512);"
            "print(json.dumps([hashlib.sha256(x.tobytes()).hexdigest() for x in f]))"
        )
        command = [str(python), "-c", code, str(script), str(video)]
    elif decoder_mode == "extract_only":
        code = (
            "import hashlib,json,sys;from robometer.evals.eval_viz_utils import extract_frames;"
            "f=extract_frames(sys.argv[1],fps=1.0,max_frames=512);"
            "print(json.dumps([hashlib.sha256(x.tobytes()).hexdigest() for x in f]))"
        )
        command = [str(python), "-c", code, str(video)]
    else:
        raise ValueError("unknown decoder mode")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo)
    result = subprocess.run(command,
                            capture_output=True, text=True, env=env, timeout=90, check=False)
    try:
        hashes = json.loads(result.stdout.splitlines()[-1]) if result.returncode == 0 else []
    except (json.JSONDecodeError, IndexError):
        hashes = []
    return {"video": video.name, "decoder_mode": decoder_mode, "returncode": result.returncode, "frame_count": len(hashes),
            "decoded_rgb_sha256": hashes, "match": result.returncode == 0 and len(hashes) == 15 and hashes == expected,
            "stderr_excerpt": result.stderr[-1000:]}


def precheck(inputs: dict[str, Path], repo: Path, python: Path) -> dict:
    script = repo / "scripts/example_inference_local.py"
    if not script.is_file() or not python.is_file():
        raise FileNotFoundError("existing Robometer script and Python required")
    clips = []
    for arm, path in inputs.items():
        rows = inspect_inputs(path)
        if len(rows) != 9:
            raise ValueError("nine anonymous videos required")
        for row in rows:
            result = check_video(path / row["video"],
                                 [row["decoded_pixel_sha256"][str(t)] for t in range(15)],
                                 script, python, repo, decoder_mode="extract_only")
            clips.append({"arm": arm, **result})
    return {"status": "pass" if len(clips) == 18 and all(item["match"] for item in clips) else "fail",
            "scope": "read_only_native_decoder_precheck", "clips": clips}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--access-input", required=True, type=Path)
    parser.add_argument("--support-input", required=True, type=Path)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--python", required=True, type=Path)
    args = parser.parse_args()
    report = precheck({"access_gate": args.access_input, "support_surface": args.support_input}, args.repo, args.python)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "pass":
        raise SystemExit(2)


if __name__ == "__main__":
    main()

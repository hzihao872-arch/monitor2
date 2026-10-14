"""Run the frozen model on an explicitly synthetic engineering track.

H1 development data admission remains blocked pending independently reviewed labels.
"""

import argparse
import hashlib
from pathlib import Path

from experiments.monitor_eval import load_online_track, run_track
from experiments.qwen_backend import QwenBackend


def validate_media(track):
    for frame in track["frames"]:
        actual = hashlib.sha256(Path(frame["path"]).read_bytes()).hexdigest()
        if actual != frame["sha256"]:
            raise ValueError(f"frame hash mismatch: {frame['path']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--track", default="experiments/artifacts/fixture_chain_v2/online_track.json")
    parser.add_argument("--method", choices=["S0", "S1", "C1"], required=True)
    parser.add_argument("--model-dir", default=".models/qwen3-vl-2b-instruct")
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    track = load_online_track(args.track)
    if track.get("trajectory_id") != "synthetic-chain-v2":
        raise ValueError("this CLI is currently restricted to the synthetic engineering fixture")
    validate_media(track)
    backend = QwenBackend(args.model_dir)
    print(run_track(args.track, backend, args.method, args.outdir,
                    "experiments/run_ledger.csv", resume=args.resume))


if __name__ == "__main__":
    main()

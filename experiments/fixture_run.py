"""Exercise S0/S1/C1 persistence on a deterministic synthetic fixture, without model inference."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from experiments.monitor_eval import run_track


class FixtureBackend:
    def infer(self, method, instruction, objects, frames, memory, tick):
        value = "+" if tick == 0 else "?"
        raw = json.dumps({"judgments": [{"object_id": oid, "H": value, "C": value,
                                         "P": "?", "G": "?", "evidence_time": tick}
                                        for oid in objects],
                          "memory": f"Observed fixture through {tick} s" if method != "S0" else ""})
        return {"raw": raw, "input_tokens": 100 + len(memory), "output_tokens": 40,
                "memory_tokens": len(memory), "elapsed_ms": 0.0, "peak_vram_bytes": 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default="experiments/artifacts/fixture_chain_v2")
    args = parser.parse_args()
    root = Path(args.outdir)
    root.mkdir(parents=True, exist_ok=True)
    images = root / "images"
    images.mkdir(parents=True, exist_ok=True)
    frames = []
    for tick in range(2):
        path = images / f"synthetic_{tick}.png"
        if not path.exists():
            from PIL import Image
            Image.new("RGB", (256, 256), (tick * 40, 0, 0)).save(path)
        frames.append({"time": float(tick), "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    track = {"trajectory_id": "synthetic-chain-v2", "objects": ["fixture-object"],
             "instruction_versions": [{"version": "fixture-v1", "effective_at": 0,
                                       "text": "Keep the blue rectangle visible."}], "frames": frames}
    manifest = root / "online_track.json"
    manifest.write_text(json.dumps(track, ensure_ascii=False, indent=2), encoding="utf-8")
    for method in ("S0", "S1", "C1"):
        print(method, run_track(manifest, FixtureBackend(), method, root / method,
                                "experiments/run_ledger.csv"))


if __name__ == "__main__":
    main()

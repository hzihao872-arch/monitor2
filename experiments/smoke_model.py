"""Local BF16 single/four-image smoke; synthetic images are engineering fixtures only."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from experiments.monitor_eval import _append_ledger


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", default=".models/qwen3-vl-2b-instruct")
    parser.add_argument("--outdir", default="experiments/artifacts/model_smoke")
    args = parser.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    from PIL import Image, ImageDraw
    frames = []
    for i in range(4):
        path = outdir / f"synthetic_{i}.png"
        image = Image.new("RGB", (256, 256), (240, 240, 240))
        draw = ImageDraw.Draw(image)
        draw.rectangle((32 + i * 14, 60, 95 + i * 14, 125), fill=(30, 70, 170))
        draw.text((20, 180), f"fixture {i}", fill=(0, 0, 0))
        image.save(path)
        frames.append({"time": float(i), "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    backend = None
    for count in (1, 4):
        run_id = str(uuid.uuid4())
        started = time.perf_counter()
        status, error, result = "failed", "", {}
        try:
            if backend is None:
                from experiments.qwen_backend import QwenBackend
                backend = QwenBackend(args.model_dir, max_new_tokens=64)
            result = backend.infer(
                "S0", {"version": "fixture-v1", "effective_at": 0, "text": "Describe the visible blue rectangle only."},
                ["fixture-object"], frames[:count], "", count - 1,
            )
            status = "completed"
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        artifact = {"run_id": run_id, "status": status, "error": error, "image_count": count,
                    "model_dir": str(Path(args.model_dir).resolve()), "weight_dtype": "bfloat16",
                    "frames": frames[:count], "result": result,
                    "wall_elapsed_ms": (time.perf_counter() - started) * 1000}
        (outdir / f"smoke_{count}.json").write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
        _append_ledger("experiments/run_ledger.csv", {
            "run_id": run_id, "utc": datetime.now(timezone.utc).isoformat(), "kind": "model_smoke",
            "track": "synthetic_fixture_v1", "method": f"S0_{count}image", "backend": "Qwen3-VL-2B-Instruct BF16",
            "status": status, "ticks_recorded": 1 if status == "completed" else 0,
            "call_attempts": 1, "input_tokens_known": result.get("input_tokens", ""),
            "output_tokens_known": result.get("output_tokens", ""),
            "elapsed_ms_known": result.get("elapsed_ms", ""),
            "peak_vram_bytes": result.get("peak_vram_bytes", ""), "error": error,
        })
        print(json.dumps({"image_count": count, "status": status, "error": error,
                          "input_tokens": result.get("input_tokens"),
                          "output_tokens": result.get("output_tokens"),
                          "elapsed_ms": result.get("elapsed_ms"),
                          "peak_vram_bytes": result.get("peak_vram_bytes")}, ensure_ascii=False))
        if status != "completed":
            break


if __name__ == "__main__":
    main()

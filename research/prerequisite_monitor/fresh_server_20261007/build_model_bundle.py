"""Build a deterministic, model-side-only code ZIP and source hash inventory."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from model_side.pilot_pkg.seal_fresh_batch import sha256

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "model_side" / "pilot_pkg"
NAMES = (
    "__init__.py", "monitor_contract.py", "monitor_relation_endpoint_v1.py",
    "run_monitor_qwen.py", "run_relation_endpoint_pilot.py", "run_native_single_scene_pilot.py",
    "preflight_fresh_server.py", "precheck_native_decoder.py", "seal_fresh_batch.py",
    "smoke_old_input.py", "official_weight_hashes.json",
)


def build() -> dict:
    actual = {path.name for path in SOURCE.iterdir() if path.is_file()}
    if actual != set(NAMES):
        raise ValueError(f"model-side allowlist differs: extra={actual - set(NAMES)}, missing={set(NAMES) - actual}")
    output = ROOT / "model_side_code.zip"
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(NAMES):
            info = zipfile.ZipInfo("pilot_pkg/" + name, date_time=(2026, 10, 7, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, (SOURCE / name).read_bytes())
    report = {"code_zip_sha256": sha256(output), "files": {name: sha256(SOURCE / name) for name in sorted(NAMES)},
              "excluded": ["truth", "condition_map", "prototype videos", "old scores", "local scorer"]}
    (ROOT / "model_side_code_manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))

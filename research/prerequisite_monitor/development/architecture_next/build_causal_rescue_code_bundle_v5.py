"""Extend sealed v3 model-side code with L1/L2 read-only preflight and sealer."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
V3 = HERE / "single_scene_pilot_code_v3.zip"
V3_SHA256 = "244ef6bdbeb93bc3360149a9801d929dc10c793345e443192bd77141290ea5c5"
EXTRA = {
    "pilot_pkg/preflight_causal_rescue_server.py": ROOT / "experiments/prerequisite_probe/preflight_causal_rescue_server.py",
    "pilot_pkg/seal_causal_rescue_batch.py": ROOT / "experiments/prerequisite_probe/seal_causal_rescue_batch.py",
    "pilot_pkg/official_weight_hashes.json": ROOT / "experiments/prerequisite_probe/artifacts/model_results/official_weight_hashes.json",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    output = HERE / "causal_rescue_20261006/code_v5.zip"
    manifest_path = HERE / "causal_rescue_20261006/code_v5_manifest.json"
    if output.exists() or manifest_path.exists():
        raise FileExistsError("v5 code package already exists")
    if digest(V3.read_bytes()) != V3_SHA256:
        raise ValueError("sealed v3 code ZIP changed")
    with zipfile.ZipFile(V3) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    for name, source in EXTRA.items():
        if name in members:
            raise ValueError(f"unexpected v3 member: {name}")
        members[name] = source.read_bytes()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w") as archive:
        for name, data in sorted(members.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    report = {
        "scope": "causal_rescue_first_batch_model_side_only",
        "base_v3_zip_sha256": V3_SHA256,
        "zip_sha256": digest(output.read_bytes()),
        "files": [{"name": name, "sha256": digest(data), "size": len(data)}
                  for name, data in sorted(members.items())],
        "excluded": ["truth", "condition_map", "continuation", "old_scores", "local_scorer"],
    }
    manifest_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"zip_sha256": report["zip_sha256"], "member_count": len(members)}))


if __name__ == "__main__":
    main()

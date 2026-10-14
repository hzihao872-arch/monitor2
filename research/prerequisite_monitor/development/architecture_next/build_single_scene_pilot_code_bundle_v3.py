"""Make a deterministic, model-side-only pilot package; never include truth."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
SOURCES = (
    "monitor_contract.py", "run_monitor_qwen.py", "monitor_relation_endpoint_v1.py",
    "run_relation_endpoint_pilot.py", "run_native_single_scene_pilot.py",
    "run_semantic_checkpoint_probe.py", "seal_single_scene_pilot.py",
    "monitor_contract_v2.py", "monitor_relation_endpoint_v1_contract_v2.py",
    "run_relation_endpoint_pilot_contract_v2.py",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    output = HERE / "single_scene_pilot_code_v3.zip"
    manifest_path = HERE / "single_scene_pilot_code_v3_manifest.json"
    if output.exists() or manifest_path.exists():
        raise FileExistsError("code bundle already exists")
    source_dir = ROOT / "experiments/prerequisite_probe"
    members = {"pilot_pkg/__init__.py": b""}
    for name in SOURCES:
        members[f"pilot_pkg/{name}"] = (source_dir / name).read_bytes()
    members["pilot_pkg/preflight_single_scene_server.py"] = (
        HERE / "preflight_single_scene_server.py").read_bytes()
    with zipfile.ZipFile(output, "w") as archive:
        for name, data in sorted(members.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    manifest = {"scope": "single_scene_model_side_code_only", "zip_sha256": digest(output.read_bytes()),
                "files": [{"name": name, "sha256": digest(data), "size": len(data)}
                          for name, data in sorted(members.items())],
                "excluded": ["truth", "condition_map", "continuation", "old_scores",
                             "analyze_single_scene_pilot.py"]}
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"zip": str(output), "sha256": manifest["zip_sha256"],
                      "member_count": len(members)}))


if __name__ == "__main__":
    main()

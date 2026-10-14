"""Build deterministic model-side package with inputs and frozen runner only."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FRESH = ROOT / "research/prerequisite_monitor/fresh_server_20261007"
SOURCE = (FRESH / "local_transfer_p0/access_gate.zip",
          FRESH / "local_transfer_p0/support_surface.zip")
CODE = ("monitor_contract_v0.py", "one_session_suite_v0_2.py", "seal_one_session_v0_2.py",
        "build_text_probe_inputs_v0_2.py", "seal_text_probe_v0_2.py",
        "native_topreward_probe_v0_2.py", "run_existing_instance_v0_2.sh")
STAMP = (2026, 10, 8, 0, 0, 0)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def add(z: zipfile.ZipFile, name: str, data: bytes, compression: int = zipfile.ZIP_DEFLATED) -> None:
    info = zipfile.ZipInfo(name, STAMP)
    info.compress_type = compression
    info.external_attr = 0o644 << 16
    z.writestr(info, data)


def main() -> None:
    contents = {}
    for number, path in enumerate(SOURCE, 1):
        data = path.read_bytes()
        with zipfile.ZipFile(path) as z:
            expected = {f"{i:04d}.mp4" for i in range(1, 10)} | {
                "instruction.txt", "manifest.jsonl", "media_hashes.json"}
            if set(z.namelist()) != expected:
                raise ValueError("source input ZIP contains unexpected file")
        contents[f"group_{number:02d}.zip"] = data
    for name in CODE:
        contents[name] = (HERE / name).read_bytes()
    readme = ("Development comparison package v0.2.0-preflight. No truth, condition mapping, "
              "case audit, old scores, model weights, or endpoint.\n"
              "Unpack each group ZIP into group_01/model_input and group_02/model_input.\n"
              "Run one_session_suite_v0_2.py --dry-run first; then a separate two-video pilot; "
              "then the full 18-video matrix after verifying model identity and lease budget.\n"
              "The same model, nine frames and max_new_tokens=896 apply to every Qwen stage.\n"
              "Optional task-text diagnostics use native_topreward_probe_v0_2.py "
              "and the unchanged official TOPReward checkout. They are separate from the Qwen method comparison.\n"
              "Do not interpret any raw output until sealed and downloaded.\n")
    contents["README.txt"] = readme.encode("utf-8")
    manifest = {"scope": "development_model_side_no_truth_not_G2",
                "suite_version": "0.2.0-preflight", "members": {name: sha(data) for name, data in sorted(contents.items())},
                "video_count": 18, "model_calls_full_matrix": 162}
    contents["bundle_manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    output = HERE / "one_session_model_side_v0.2.0.zip"
    with zipfile.ZipFile(output, "w") as z:
        for name, data in sorted(contents.items()):
            add(z, name, data, zipfile.ZIP_STORED if name.endswith(".zip") else zipfile.ZIP_DEFLATED)
    report = {"path": output.relative_to(ROOT).as_posix(),
              "sha256": sha(output.read_bytes()), "size_bytes": output.stat().st_size,
              **manifest}
    (HERE / "one_session_package_manifest.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sha256": report["sha256"], "size_bytes": report["size_bytes"],
                      "model_calls_full_matrix": 162}))


if __name__ == "__main__":
    main()

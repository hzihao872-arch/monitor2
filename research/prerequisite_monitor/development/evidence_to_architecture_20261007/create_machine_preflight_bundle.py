"""Build a deterministic, input-only review bundle; do not contact a server."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FRESH = ROOT / "research/prerequisite_monitor/fresh_server_20261007"
STAMP = (2026, 10, 7, 0, 0, 0)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def member(name: str, data: bytes, compression: int = zipfile.ZIP_DEFLATED):
    info = zipfile.ZipInfo(name, STAMP)
    info.compress_type = compression
    info.external_attr = 0o644 << 16
    return info, data


def main():
    source = [FRESH / "local_transfer_p0/access_gate.zip",
              FRESH / "local_transfer_p0/support_surface.zip"]
    parts = []
    manifest = {"scope": "development_input_only_preflight_not_method_freeze_not_G2",
                "protocol_version": "0.1.1", "groups": []}
    for index, path in enumerate(source, start=1):
        data = path.read_bytes()
        with zipfile.ZipFile(path) as z:
            names = set(z.namelist())
            expected = {f"{i:04d}.mp4" for i in range(1, 10)} | {
                "instruction.txt", "manifest.jsonl", "media_hashes.json"}
            assert names == expected, path
            assert len(z.read("manifest.jsonl").splitlines()) == 9
            instr_hash = sha(z.read("instruction.txt"))
        name = f"group_{index:02d}.zip"
        parts.append(member(name, data, zipfile.ZIP_STORED))
        manifest["groups"].append({"name": name, "sha256": sha(data),
                                   "video_count": 9, "instruction_sha256": instr_hash})
    contract = (HERE / "monitor_contract_v0.py").read_bytes()
    parts.append(member("monitor_contract_v0.py", contract))
    manifest["contract_sha256"] = sha(contract)
    guide = ("Development input-only preflight bundle, not a frozen model method or G2.\n"
             "Only group_01.zip and group_02.zip contain allowed model inputs: anonymous RGB videos,\n"
             "one final-goal instruction per group, manifest and media hashes.\n"
             "No truth, condition mapping, scene answer, model output, weight or endpoint is included.\n"
             "Do not upload until the user provides the existing instance endpoint and lease.\n"
             "Before any model call, verify this outer ZIP and each inner ZIP against bundle_manifest.json.\n"
             "monitor_contract_v0.py is a no-model output validator, not an inference method.\n")
    parts.append(member("README.txt", guide.encode("utf-8")))
    parts.append(member("bundle_manifest.json", (json.dumps(manifest, indent=2) + "\n").encode("utf-8")))
    output = HERE / "machine_preflight_input_only_v0.1.1.zip"
    with zipfile.ZipFile(output, "w") as z:
        for info, data in parts:
            z.writestr(info, data)
    summary = {"path": output.relative_to(ROOT).as_posix(), "sha256": sha(output.read_bytes()),
               "size_bytes": output.stat().st_size, "groups": manifest["groups"],
               "contract_sha256": manifest["contract_sha256"]}
    (HERE / "machine_preflight_bundle.sha256.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"size_bytes": summary["size_bytes"], "sha256": summary["sha256"]}))


if __name__ == "__main__":
    main()

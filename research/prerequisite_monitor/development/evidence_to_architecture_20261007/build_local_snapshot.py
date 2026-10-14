"""Hash the current local research checkpoint; this is not METHOD_FREEZE."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
NAMES = (
    "README.md", "evidence_atlas.md", "hypothesis_register.md",
    "prior_work_to_design.md", "architecture_decision_record.md",
    "architecture_spec.md", "G2_sampling_plan.md", "RUN_CARD_PRE_MACHINE.md",
    "verification_log.md", "build_evidence_index.py", "evidence_case_index.jsonl",
    "evidence_index_manifest.json", "monitor_contract_v0.py", "run_local_dry_run.py",
    "local_dry_run.json", "create_machine_preflight_bundle.py",
    "machine_preflight_input_only_v0.1.1.zip", "machine_preflight_bundle.sha256.json",
    "ONE_SESSION_EXPERIMENT_FREEZE_v0.2.md", "RUN_CARD_ONE_SESSION_v0.2.md",
    "one_session_suite_v0_2.py", "audit_one_session_v0_2.py",
    "seal_one_session_v0_2.py", "build_text_probe_inputs_v0_2.py",
    "native_topreward_probe_v0_2.py", "seal_text_probe_v0_2.py",
    "audit_text_probe_v0_2.py", "run_existing_instance_v0_2.sh",
    "build_one_session_package.py", "one_session_model_side_v0.2.0.zip",
    "one_session_package_manifest.json",
    "build_local_snapshot.py",
)


def main():
    files = []
    for name in NAMES:
        path = HERE / name
        content = path.read_bytes()
        files.append({"path": name, "size_bytes": len(content),
                      "sha256": hashlib.sha256(content).hexdigest()})
    out = HERE / "local_research_snapshot_manifest.json"
    out.write_text(json.dumps({"scope": "local_research_checkpoint_not_method_freeze_not_G2",
                               "files": files}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"files": len(files), "manifest_sha256": hashlib.sha256(out.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()

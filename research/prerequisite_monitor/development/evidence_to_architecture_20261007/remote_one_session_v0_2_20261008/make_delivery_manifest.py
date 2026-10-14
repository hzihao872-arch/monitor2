"""Hash the local delivery set; text_seal.json inventories individual native files."""

import hashlib
import json
from pathlib import Path


root = Path(__file__).resolve().parent
relpaths = [
    "../one_session_model_side_v0.2.0.zip",
    "qwen_evidence.tar.gz",
    "text_evidence.tar.gz",
    "supplement_evidence.tar.gz",
    "qwen_evidence/raw.jsonl",
    "qwen_evidence/qwen_seal.json",
    "text_evidence/text_inputs/text_probe_manifest.json",
    "text_evidence/text_seal.json",
    "audit_qwen/case_results.jsonl",
    "audit_qwen/pair_results.jsonl",
    "audit_qwen/readout_ablations.jsonl",
    "audit_qwen/summary.json",
    "audit_text_probe.json",
    "text_curve_summary.csv",
    "text_pair_summary.csv",
    "semantic_review_notes.md",
    "core_case_semantic_review.csv",
    "RESULTS_REPORT_zh.md",
    "execution_failure_log.md",
    "chain_verification.json",
]

files = []
for relpath in relpaths:
    path = root / relpath
    data = path.read_bytes()
    files.append({
        "path": relpath,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    })

result = {
    "scope": "development_only_not_G2",
    "individual_native_file_hashes": "text_evidence/text_seal.json",
    "files": files,
}
(root / "delivery_manifest.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(f"delivery_manifest.json: {len(files)} files hashed")

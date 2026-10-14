"""Freeze only model-side P4/P5 code; no truth, scores, or old outputs."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = (
    "optional/__init__.py", "optional/p4_seal.py", "optional/p4_pilot_input.py",
    "optional/p5_qwen.py", "optional/seal_p5.py",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    path = ROOT / "p4_p5_model_code.zip"
    if path.exists():
        raise FileExistsError(path)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in FILES:
            if not (ROOT / name).is_file():
                raise FileNotFoundError(name)
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 7, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, (ROOT / name).read_bytes())
    report = {"scope": "P4_P5_model_side_only", "zip_sha256": sha256(path),
              "files": {name: sha256(ROOT / name) for name in FILES},
              "contains_truth_or_condition_map": False}
    (ROOT / "p4_p5_model_code_manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

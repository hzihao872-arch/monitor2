"""Build a deterministic truth-free model-side ZIP for P6."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = ("p6pkg/__init__.py", "p6pkg/run.py", "p6pkg/seal.py")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    output = ROOT / "p6_model_code.zip"
    if output.exists():
        raise FileExistsError(output)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in FILES:
            source = ROOT / name
            if not source.is_file():
                raise FileNotFoundError(source)
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 7, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, source.read_bytes())
    report = {"scope": "P6_model_side_only", "zip_sha256": sha256(output),
              "files": {name: sha256(ROOT / name) for name in FILES},
              "contains_truth_or_condition_map": False}
    (ROOT / "p6_model_code_manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

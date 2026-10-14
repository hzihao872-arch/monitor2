"""Create one small upload package for the prepared P4/P5 server runs."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    code_manifest = json.loads((HERE / "p4_p5_model_code_manifest.json").read_text(encoding="utf-8"))
    inputs = json.loads((HERE / "p4_inputs" / "build_manifest.json").read_text(encoding="utf-8"))
    if sha256(HERE / "p4_p5_model_code.zip") != code_manifest["zip_sha256"]:
        raise ValueError("model code ZIP changed")
    paths = {"p4_p5_model_code.zip": HERE / "p4_p5_model_code.zip"}
    for key, cell in inputs["cells"].items():
        variant, arm = key.split("/")
        name = f"p4_inputs/{variant}/{arm}/model_input.zip"
        path = HERE / name
        if sha256(path) != cell["zip_sha256"]:
            raise ValueError("P4 input ZIP changed: " + key)
        paths[name] = path
    output = HERE / "p4_p5_upload.zip"
    if output.exists():
        raise FileExistsError(output)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, path in sorted(paths.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 7, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    report = {"scope": "P4_P5_model_side_upload_only", "upload_sha256": sha256(output),
              "members": {name: sha256(path) for name, path in sorted(paths.items())},
              "contains_truth_or_condition_map": False}
    (HERE / "p4_p5_upload_manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

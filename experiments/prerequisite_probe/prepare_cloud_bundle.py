"""Package only frozen, label-free inputs and the Monitor runner for an old cloud VM."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from .run_monitor_qwen import collect_inputs, sha256


CODE_FILES = ("monitor_contract.py", "run_monitor_qwen.py",
              "cloud_preflight_new_monitor.sh", "cloud_run_new_monitor.sh")


def create_bundle(roots: list[Path], output: Path,
                  method_freeze: Path | None = None) -> dict:
    if output.exists():
        raise FileExistsError(output)
    project = Path(__file__).resolve().parents[2]
    if method_freeze is not None:
        method_freeze = method_freeze.resolve()
        if sha256(method_freeze) != method_freeze.with_suffix(".sha256").read_text().strip():
            raise ValueError("method freeze hash mismatch")
        frozen_method = json.loads(method_freeze.read_text(encoding="utf-8"))
        for name, expected in frozen_method["file_sha256"].items():
            if sha256(project / name) != expected:
                raise ValueError(f"method code hash mismatch: {name}")
    if len(roots) != 2:
        raise ValueError("exactly two complete frozen mechanisms are required")
    files: list[tuple[str, Path]] = []
    private_mapping = {}
    for code in CODE_FILES:
        path = project / "experiments" / "prerequisite_probe" / code
        files.append((f"experiments/prerequisite_probe/{code}", path))
    video_count = 0
    for index, root in enumerate(roots, start=1):
        root = root.resolve()
        frozen = root / "truth" / "frozen_test.json"
        expected_freeze_hash = (root / "truth" / "frozen_test.sha256").read_text().strip()
        if sha256(frozen) != expected_freeze_hash:
            raise ValueError(f"freeze hash mismatch: {root}")
        freeze = json.loads(frozen.read_text(encoding="utf-8"))
        input_dir = root / "model_input"
        rows = collect_inputs(input_dir)
        if {row["video"][:-4] for row in rows} != set(freeze["cases"]):
            raise ValueError(f"frozen video set mismatch: {root}")
        alias = f"s{index:02d}"
        private_mapping[alias] = {"local_root": str(root),
                                  "frozen_test_sha256": expected_freeze_hash}
        files.append((f"new_tests/{alias}/model_input/manifest.jsonl",
                      input_dir / "manifest.jsonl"))
        for row in rows:
            stem = row["video"][:-4]
            if freeze["cases"][stem]["video_sha256"] != row["sha256"]:
                raise ValueError(f"frozen video hash mismatch: {root}/{stem}")
            files.append((f"new_tests/{alias}/model_input/{row['video']}",
                          input_dir / row["video"]))
            video_count += 1
    if len({name for name, _ in files}) != len(files):
        raise ValueError("duplicate archive entry")
    manifest = {"format": "monitor_input_only_v1", "files": [
        {"path": name, "sha256": sha256(path)} for name, path in files]}
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6) as archive:
        for name, path in files:
            archive.write(path, arcname=name)
        archive.writestr("new_tests/bundle_manifest.json",
                         json.dumps(manifest, indent=2) + "\n")
    audit = {"archive": str(output.resolve()), "archive_sha256": sha256(output),
             "video_count": video_count, "private_mapping": private_mapping,
             "allowed_members": [*map(lambda item: item[0], files),
                                 "new_tests/bundle_manifest.json"]}
    output.with_suffix(".private_audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    return audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--method-freeze", type=Path, required=True)
    args = parser.parse_args()
    audit = create_bundle(args.root, args.output, args.method_freeze)
    print(json.dumps({key: audit[key] for key in
                      ("archive", "archive_sha256", "video_count")}))


if __name__ == "__main__":
    main()

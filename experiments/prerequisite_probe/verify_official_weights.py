"""Verify every pinned checkpoint shard against official Hub file metadata."""

import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()
    records = json.loads(args.manifest.read_text(encoding="utf-8"))
    record = next((item for item in records if item["repo"] == args.repo), None)
    if record is None:
        parser.error("model missing from manifest")
    snapshot = args.cache / "hub" / ("models--" + args.repo.replace("/", "--")) / "snapshots" / record["revision"]
    for expected in record["files"]:
        path = snapshot / expected["name"]
        if path.stat().st_size != expected["size"]:
            raise RuntimeError(f"Wrong byte count: {path}")
        actual = sha256_file(path)
        if actual != expected["sha256"]:
            raise RuntimeError(f"SHA-256 mismatch: {path}")
        print(f"VERIFIED {path} {actual}", flush=True)
    print(f"VERIFIED_MODEL {args.repo}@{record['revision']}", flush=True)


if __name__ == "__main__":
    main()

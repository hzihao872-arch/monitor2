"""Resume pinned Hugging Face safetensors over HTTP ranges, with SHA-256 checks.

This handles proxy connections that stall on full-file/Xet transfers. It does not
transform the checkpoint. Run once per model, then point loaders to the snapshot.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from huggingface_hub import HfApi, snapshot_download


CHUNK = 32 * 1024 * 1024


def download_one(repo: str, revision: str, name: str, cache: Path, endpoint: str,
                 alternate_weights_url_base: str | None = None,
                 expected_file: dict | None = None) -> tuple[str, int]:
    url = (f"{alternate_weights_url_base.rstrip('/')}/{name}" if alternate_weights_url_base
           else f"{endpoint.rstrip('/')}/{repo}/resolve/{revision}/{name}")
    response = requests.head(url, allow_redirects=False, timeout=40)
    response.raise_for_status()
    digest = response.headers["x-linked-etag"].strip('"')
    if expected_file is not None:
        if digest != expected_file["sha256"]:
            raise RuntimeError(f"Alternate source SHA-256 differs from pinned file: {name}")
        size = int(expected_file["size"])
    else:
        size = int(response.headers["x-linked-size"])
    blob_dir = cache / "hub" / ("models--" + repo.replace("/", "--")) / "blobs"
    blob_dir.mkdir(parents=True, exist_ok=True)
    blob = blob_dir / digest
    partial = blob_dir / (digest + ".incomplete")
    if not blob.exists() or blob.stat().st_size != size:
        downloaded = partial.stat().st_size if partial.exists() else 0
        if downloaded > size:
            raise RuntimeError(f"Partial file too large: {partial}")
        stalled_attempts = 0
        while downloaded < size:
            first = downloaded
            last = min(first + CHUNK - 1, size - 1)
            try:
                with requests.get(
                    url,
                    headers={"Range": f"bytes={first}-{last}"},
                    stream=True,
                    timeout=(40, 90),
                ) as transfer:
                    transfer.raise_for_status()
                    expected = f"bytes {first}-{last}/{size}"
                    if transfer.status_code != 206 or transfer.headers.get("Content-Range") != expected:
                        raise RuntimeError(f"Unexpected range response: {transfer.status_code} {transfer.headers.get('Content-Range')}")
                    with partial.open("ab") as output:
                        for piece in transfer.iter_content(chunk_size=1024 * 1024):
                            output.write(piece)
                if partial.stat().st_size != last + 1:
                    raise RuntimeError("Short range download")
            except (requests.RequestException, RuntimeError) as error:
                retained = min(partial.stat().st_size, last + 1)
                if partial.stat().st_size > retained:
                    with partial.open("r+b") as output:
                        output.truncate(retained)
                if retained > first:
                    stalled_attempts = 0
                    print(f"RETAIN {name} {retained - first} bytes after interruption", flush=True)
                else:
                    stalled_attempts += 1
                if stalled_attempts >= 10:
                    raise
                print(f"RETRY {name} {retained}/{size}: {error}", flush=True)
                downloaded = retained
                time.sleep(min(2 ** max(stalled_attempts - 1, 0), 30))
                continue
            downloaded = last + 1
            stalled_attempts = 0
            if downloaded == size or downloaded // (256 * 1024 * 1024) != first // (256 * 1024 * 1024):
                print(f"PROGRESS {name}: {downloaded}/{size}", flush=True)
        with partial.open("rb") as source:
            actual_digest = hashlib.file_digest(source, "sha256").hexdigest()
        if actual_digest != digest:
            raise RuntimeError(f"SHA-256 mismatch for {name}: {actual_digest} != {digest}")
        os.replace(partial, blob)
    snapshot = cache / "hub" / ("models--" + repo.replace("/", "--")) / "snapshots" / revision
    target = snapshot / name
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        os.link(blob, target)
    print(f"COMPLETE {name}: {size} bytes sha256={digest}", flush=True)
    return name, size


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--endpoint", default="https://huggingface.co")
    parser.add_argument("--alternate-weights-url-base")
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    expected_files = {}
    if args.alternate_weights_url_base:
        if args.manifest is None:
            parser.error("--manifest is required for alternate weight transport")
        records = json.loads(args.manifest.read_text(encoding="utf-8"))
        record = next((r for r in records if r["repo"] == args.repo and r["revision"] == args.revision), None)
        if record is None:
            parser.error("repo and revision missing from pinned hash manifest")
        expected_files = {f["name"]: f for f in record["files"]}
    info = HfApi(endpoint=args.endpoint).model_info(args.repo, revision=args.revision)
    names = [s.rfilename for s in info.siblings if s.rfilename.endswith(".safetensors")]
    if args.alternate_weights_url_base and set(names) != set(expected_files):
        raise RuntimeError("Pinned Hub file list differs from hash manifest")
    print(f"Pinned {args.repo}@{args.revision}; weights={names}", flush=True)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(download_one, args.repo, args.revision, name, args.cache,
                               args.endpoint, args.alternate_weights_url_base,
                               expected_files.get(name)) for name in names]
        for future in as_completed(futures):
            future.result()
    path = snapshot_download(
        args.repo,
        revision=args.revision,
        allow_patterns=["*.json", "*.yaml", "*.txt", "*.model", "*.jinja"],
        cache_dir=str(args.cache / "hub"),
        endpoint=args.endpoint,
        max_workers=4,
    )
    print(f"SNAPSHOT {path}", flush=True)


if __name__ == "__main__":
    main()

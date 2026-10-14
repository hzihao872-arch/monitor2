"""Fetch a bounded, revision-pinned ContextProgress-Bench episode slice."""

import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REVISION = "0eb2e2e61f89c499de94a31264c704735b52900c"
BASE = f"https://huggingface.co/datasets/Sterzhang/ContextProgress-Bench/resolve/{REVISION}/"
PATHS = [
    "README.md",
    "LICENSE.md",
    "episodes.jsonl",
    "subtasks.jsonl",
    "episode_id_mapping.json",
    "RMBench/cover_blocks/demo_clean/episodes/episode1/manifest.json",
    "RMBench/cover_blocks/demo_clean/episodes/episode1/subtasks/subtask00/instruction.json",
    "RMBench/place_block_mat/demo_clean/episodes/episode1/manifest.json",
    "RMBench/place_block_mat/demo_clean/episodes/episode1/subtasks/subtask00/instruction.json",
    "RMBench/place_block_mat/demo_clean/episodes/episode1/subtasks/subtask01/instruction.json",
    "RMBench/place_block_mat/demo_clean/episodes/episode1/full_video.mp4",
]
MAX_FILE = 700_000
MAX_BATCH = 1_300_000


def main() -> None:
    plan = []
    for name in PATHS:
        url = BASE + name
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=30) as response:
            size = int(response.headers["Content-Length"])
            head_status = response.status
        if size > MAX_FILE:
            raise RuntimeError(f"File exceeds bound: {name} ({size})")
        plan.append((name, url, head_status, size))
    if sum(row[3] for row in plan) > MAX_BATCH:
        raise RuntimeError("Batch exceeds bound")

    entries = []
    for name, url, head_status, size in plan:
        dest = ROOT / "contextprogress" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            body = dest.read_bytes()
        else:
            with urllib.request.urlopen(url, timeout=30) as response:
                body = response.read(MAX_FILE + 1)
        if len(body) != size:
            raise RuntimeError(f"Byte count mismatch: {name}")
        dest.write_bytes(body)
        entries.append({
            "path": str(dest.relative_to(ROOT)).replace("\\", "/"),
            "url": url,
            "head_status": head_status,
            "revision": REVISION,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
        })
    manifest_path = ROOT / "fetch_manifest.json"
    prior = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
    timestamp = prior["retrieved_utc"] if prior and prior.get("files") == entries else datetime.now(timezone.utc).isoformat()
    manifest_path.write_text(json.dumps({
        "retrieved_utc": timestamp,
        "bounds": {"per_file_bytes": MAX_FILE, "batch_bytes": MAX_BATCH},
        "files": entries,
        "media_downloaded": ["RMBench/place_block_mat/demo_clean/episodes/episode1/full_video.mp4"],
        "weights_downloaded": False,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"files": len(entries), "bytes": sum(x["bytes"] for x in entries)}))


if __name__ == "__main__":
    main()

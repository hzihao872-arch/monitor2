"""Record official Hugging Face LFS hashes for the frozen model revisions."""

import json
from pathlib import Path

from huggingface_hub import HfApi


MODELS = [
    ("Qwen/Qwen3-VL-8B-Instruct", "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b"),
    ("robometer/Robometer-4B", "beef63bc914c5c189329d49c6d712d96d632aa34"),
    ("Qwen/Qwen3-VL-4B-Instruct", "ebb281ec70b05090aa6165b016eac8ec08e71b17"),
]


def main() -> None:
    api = HfApi()
    result = []
    for repo, revision in MODELS:
        info = api.model_info(repo, revision=revision, files_metadata=True)
        files = [
            {"name": sibling.rfilename, "size": sibling.lfs.size, "sha256": sibling.lfs.sha256}
            for sibling in info.siblings
            if sibling.rfilename.endswith(".safetensors") and sibling.lfs is not None
        ]
        result.append({"repo": repo, "revision": revision, "files": files})
    path = Path(__file__).parent / "artifacts/model_results/official_weight_hashes.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()

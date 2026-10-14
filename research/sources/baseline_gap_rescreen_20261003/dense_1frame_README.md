---
base_model: Qwen/Qwen3-VL-4B-Instruct
library_name: transformers
pipeline_tag: image-text-to-text
tags:
- qwen3-vl
- reward-model
- robot-manipulation
- vlm
license: apache-2.0
---

# densereward-1frame

🌐 [Project page](https://dense-reward.github.io/) · 📄 [Paper (arXiv:2607.13033)](https://arxiv.org/abs/2607.13033)

This is the **single-frame reward model** from **DenseReward: Dense Reward
Learning via Failure Synthesis for Robotic Manipulation**. It is a
vision-language reward model for robot manipulation. Given a
single image of a manipulation scene, it outputs a single scalar in
`[0.000, 1.000]` estimating **task progress** (0 = no progress / failed,
1 = task complete).

**Variants:**
- [`densereward-1frame`](https://huggingface.co/densereward/densereward-1frame): single-frame reward model — given one RGB frame + task text, outputs a scalar reward in `[0.000, 1.000]`.
- [`densereward-3frame-thinking`](https://huggingface.co/densereward/densereward-3frame-thinking): 3-frame reward model with reasoning — given 3 chronological frames + task text, emits a `<think>` reasoning word then a scalar reward. Warm-started from the 1-frame checkpoint.

## Intended use & scope

- **Input:** one RGB frame of a robot manipulation scene (+ the task text in the
  user turn).
- **Output:** exactly one float with three decimals, e.g. `0.374`.
- **Not** a chat model. It is trained to emit only a reward value under the
  system prompt below. It has no other instruction-following guarantees.

## Output contract

The model was trained with a fixed system prompt and a strict output
format. Use the same system prompt at inference (`system_prompt.txt` in this
directory). It instructs the model to emit exactly a single float in
`[0.000, 1.000]` (three decimals).

> The **user turn** should contain the scene image plus the task description, in
> the same format used during training (image + short task text).

## Quickstart

Requires `transformers>=4.57`, `qwen_vl_utils>=0.0.14`, `torch`, `accelerate`.

> **Tested environment**:
> Python 3.12, CUDA 12.8, `torch==2.8.0+cu128`, `torchvision==0.23.0+cu128`,
> `transformers==5.2.0`, `accelerate==1.13.0`, `qwen-vl-utils==0.0.14`.
>
>
> ```bash
> conda create -n densereward python=3.12 -y
> conda activate densereward
> pip install torch==2.8.0 torchvision==0.23.0 --index-url https://download.pytorch.org/whl/cu128
> pip install "transformers==5.2.0" "accelerate==1.13.0" "qwen-vl-utils==0.0.14" pillow numpy
> ```

```python
import re
import torch
from transformers import AutoModelForImageTextToText, AutoProcessor
from qwen_vl_utils import process_vision_info

MODEL_DIR = "densereward/densereward-1frame"  # or a local path to this checkpoint

# The exact system prompt used in training ships with the model:
SYSTEM_PROMPT = open(f"{MODEL_DIR}/system_prompt.txt").read().strip()

model = AutoModelForImageTextToText.from_pretrained(
    MODEL_DIR, torch_dtype=torch.bfloat16, device_map="auto"
)
processor = AutoProcessor.from_pretrained(MODEL_DIR)

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {
        "role": "user",
        "content": [
            {"type": "image", "image": "file:///path/to/frame.png"},
            {"type": "text", "text": "Task: put the black bowl on the plate."},
        ],
    },
]

text = processor.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True
)
image_inputs, video_inputs = process_vision_info(messages)
inputs = processor(
    text=[text],
    images=image_inputs,
    videos=video_inputs,
    padding=True,
    return_tensors="pt",
).to(model.device)

with torch.no_grad():
    out = model.generate(**inputs, max_new_tokens=8, do_sample=False)  # greedy

gen = out[:, inputs.input_ids.shape[1]:]
raw = processor.batch_decode(gen, skip_special_tokens=True)[0].strip()
reward = float(re.search(r"[01](?:\.\d+)?", raw).group())
print(raw, "->", reward)
```

Notes:
- `max_new_tokens` only needs to be a handful of tokens (a float is short).
- Always guard the parse: clip to `[0, 1]` and handle non-float output.

## Loading with ms-swift

The release includes a minimal `args.json` (`{model_type: qwen3_vl, swift_version}`)
so ms-swift's `PtEngine` / `TransformersEngine` can auto-detect the model type for
this local directory (its architecture otherwise matches several swift registry
entries). Load it as the base model with **no** adapter:

```python
from swift import TransformersEngine, RequestConfig, InferRequest
engine = TransformersEngine("densereward/densereward-1frame")  # no adapters
```

Pass the system prompt above as a `{"role": "system", ...}` message and the task
as the user turn (`<image>{task}`), matching training.

> Compatibility note: ms-swift 4.2.x targets `transformers>=4.57,<5`. Under a much
> newer transformers (e.g. 5.x) the swift template/prompt composition can
> misbehave even though weights load fine — prefer the `transformers` path above,
> or a swift-matched transformers version, for swift-based inference.

## License

Apache License 2.0 (see `LICENSE`). The base model
[`Qwen/Qwen3-VL-4B-Instruct`](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct)
is also Apache-2.0. This fine-tune was produced at the University of North
Carolina at Chapel Hill.

## Citation

```bibtex
@article{fang2026densereward,
    title={DenseReward: Dense Reward Learning via Failure Synthesis for Robotic Manipulation},
    author={Fang, Yu and Dong, Wanxi and Liu, Jiaqi and Yang, Yue and Huo, Mingxiao and Mu, Yao and Yao, Huaxiu and Li, Li Erran and Szafir, Daniel and Ding, Mingyu},
    journal={arXiv preprint arXiv:2607.13033},
    year={2026}
}
```

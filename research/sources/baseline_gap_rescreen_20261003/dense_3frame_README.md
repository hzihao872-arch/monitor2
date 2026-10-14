---
base_model: Qwen/Qwen3-VL-4B-Instruct
library_name: transformers
pipeline_tag: image-text-to-text
tags:
- qwen3-vl
- reward-model
- robot-manipulation
- multi-frame
- thinking
- vlm
license: apache-2.0
---

# densereward-3frame-thinking

🌐 [Project page](https://dense-reward.github.io/) · 📄 [Paper (arXiv:2607.13033)](https://arxiv.org/abs/2607.13033)

This is the **3-frame, reasoning ("thinking") reward model** from **DenseReward:
Dense Reward Learning via Failure Synthesis for Robotic Manipulation**. It is a
vision-language reward model for robot manipulation that reasons
over a **short sequence of frames**. Given the last **3 frames** of an episode
(chronological: two history frames + the current frame) plus the task text, it
emits **one reasoning word** in a `<think>...</think>` block, then a scalar reward
in `[0.000, 1.000]` estimating task progress **at the current (last) frame**.

**Variants:**
- [`densereward-1frame`](https://huggingface.co/densereward/densereward-1frame): single-frame reward model — given one RGB frame + task text, outputs a scalar reward in `[0.000, 1.000]`.
- [`densereward-3frame-thinking`](https://huggingface.co/densereward/densereward-3frame-thinking): 3-frame reward model with reasoning — given 3 chronological frames + task text, emits a `<think>` reasoning word then a scalar reward. Warm-started from the 1-frame checkpoint.

## Intended use & scope

- **Input:** exactly 3 RGB frames in chronological order (oldest → current)
  plus the task text in the user turn.
- **Output:** a `<think>WORD</think>` block followed by one float with three
  decimals, e.g. `<think>\ncorrect\n</think>\n\n0.374`.
- **Not** a chat model. It only emits the reward-with-reasoning format under the
  system prompt below.

## Output contract

The model was trained with a fixed system prompt and a strict output
format. Use the same system prompt at inference (`system_prompt.txt` in this
directory). It instructs:

1. Emit exactly one reasoning word inside `<think>...</think>`, from this
   vocabulary:
   - `correct` — progress on track (reward increasing/holding)
   - `miss` — gripper missed the grasp and reward just dropped
   - `collision` — an unintended collision just dropped the reward
   - `fall` — the held object fell and reward just dropped
   - `smooth` — motion stalled / non-smooth behaviour dropped the reward
   - `failure` — an unclassified failure event just dropped the reward
2. Then a single float in `[0.000, 1.000]` (three decimals).

Canonical output (note the blank line after `</think>`):

```text
<think>
correct
</think>

0.374
```

> The **user turn** must contain the **3 images** followed by the task text, in
> the same format used during training (`<image><image><image>{task}`).

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

MODEL_DIR = "densereward/densereward-3frame-thinking"  # or a local path to this checkpoint

# The exact thinking system prompt used in training ships with the model:
SYSTEM_PROMPT = open(f"{MODEL_DIR}/system_prompt.txt").read().strip()

model = AutoModelForImageTextToText.from_pretrained(
    MODEL_DIR, torch_dtype=torch.bfloat16, device_map="auto"
)
processor = AutoProcessor.from_pretrained(MODEL_DIR)

# 3 chronological frames: oldest -> current
frames = [
    "file:///path/to/frame_t-2.png",
    "file:///path/to/frame_t-1.png",
    "file:///path/to/frame_t.png",
]
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {
        "role": "user",
        "content": [
            {"type": "image", "image": frames[0]},
            {"type": "image", "image": frames[1]},
            {"type": "image", "image": frames[2]},
            {"type": "text", "text": "put the black bowl on the plate"},
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
    out = model.generate(**inputs, max_new_tokens=32, do_sample=False)  # greedy

gen = out[:, inputs.input_ids.shape[1]:]
raw = processor.batch_decode(gen, skip_special_tokens=True)[0].strip()
print(raw)

word = re.search(r"<think>\s*(\w+)\s*</think>", raw)
reward = re.search(r"</think>\s*([01](?:\.\d+)?)", raw)
print("reason:", word.group(1) if word else None,
      "| reward:", float(reward.group(1)) if reward else None)
```

Notes:
- Provide the **3 frames in chronological order** (oldest first, current last).
- Use `max_new_tokens>=32`: the output includes the `<think>` block *and* the
  reward.
- Always guard the parse: clip reward to `[0, 1]` and handle malformed output.

## About "thinking" here

The `<think>WORD</think>` block is part of the trained assistant output,
driven by the system prompt and thinking-labelled training data — it is **not**
ms-swift's native `--enable_thinking` mode (`enable_thinking` was `false` for this
run). At inference you only need the bundled system prompt; the model produces the
`<think>...</think>` block itself.

## Loading with ms-swift

The release includes a minimal `args.json` (`{model_type: qwen3_vl, swift_version}`)
so ms-swift's `PtEngine` / `TransformersEngine` can auto-detect the model type for
this local directory. Load it as the base model with no adapter; pass the
bundled system prompt and a 3-image user turn.

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

"""Frozen local Qwen3-VL inference adapter for engineering checks.

No network access, reference labels, or task-specific training occurs here.
"""

from __future__ import annotations

import time
from pathlib import Path

from experiments.monitor_eval import build_prompt


def compose_messages(prompt, frames, image_loader):
    content = [{"type": "text", "text": prompt}]
    for frame in frames:
        content.append({"type": "text", "text": f"Frame at {float(frame['time']):.1f} s"})
        content.append({"type": "image", "image": image_loader(frame["path"])})
    return [{"role": "user", "content": content}]


class QwenBackend:
    def __init__(self, model_dir, max_input_tokens=4096, max_new_tokens=256):
        import torch
        from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

        self.torch = torch
        self.model_dir = Path(model_dir).resolve()
        self.max_input_tokens = max_input_tokens
        self.max_new_tokens = max_new_tokens
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is required for the frozen BF16 configuration")
        if not torch.cuda.is_bf16_supported():
            raise RuntimeError("CUDA device does not support BF16")
        self.processor = AutoProcessor.from_pretrained(self.model_dir, local_files_only=True)
        self.model = Qwen3VLForConditionalGeneration.from_pretrained(
            self.model_dir,
            dtype=torch.bfloat16,
            attn_implementation="sdpa",
            local_files_only=True,
        ).to("cuda").eval()

    def _image(self, path):
        from PIL import Image

        with Image.open(path) as source:
            return source.convert("RGB").resize((256, 256), Image.Resampling.BICUBIC)

    def infer(self, method, instruction, objects, frames, memory, tick):
        torch = self.torch
        start = time.perf_counter()
        prompt = build_prompt(method, instruction, objects, memory, tick)
        messages = compose_messages(prompt, frames, self._image)
        inputs = self.processor.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=True,
            return_dict=True, return_tensors="pt",
        )
        input_tokens = int(inputs["input_ids"].shape[-1])
        memory_tokens = len(self.processor.tokenizer.encode(memory, add_special_tokens=False))
        if input_tokens > self.max_input_tokens:
            return {
                "raw": "", "input_tokens": input_tokens, "output_tokens": 0,
                "memory_tokens": memory_tokens,
                "elapsed_ms": (time.perf_counter() - start) * 1000,
                "peak_vram_bytes": torch.cuda.max_memory_allocated(),
            }
        inputs = inputs.to("cuda")
        torch.cuda.reset_peak_memory_stats()
        with torch.inference_mode():
            generated = self.model.generate(
                **inputs, max_new_tokens=self.max_new_tokens, do_sample=False,
            )
        output_ids = generated[:, inputs["input_ids"].shape[-1]:]
        raw = self.processor.batch_decode(output_ids, skip_special_tokens=True)[0]
        torch.cuda.synchronize()
        return {
            "raw": raw,
            "input_tokens": input_tokens,
            "output_tokens": int(output_ids.shape[-1]),
            "memory_tokens": memory_tokens,
            "elapsed_ms": (time.perf_counter() - start) * 1000,
            "peak_vram_bytes": torch.cuda.max_memory_allocated(),
        }

"""Post-score visual diagnostic; never count as frozen Monitor evaluation."""

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import torch
from PIL import Image
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', required=True, type=Path)
    parser.add_argument('--model-path', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    processor = AutoProcessor.from_pretrained(args.model_path, local_files_only=True)
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        args.model_path, dtype=torch.bfloat16, attn_implementation='flash_attention_2',
        local_files_only=True).to('cuda').eval()
    prompt = (
        'Visual geometry check only. Is a red horizontal bar visibly spanning over the blue cube '
        'between the two gray supports in this single image? Do not infer from previous or future '
        'frames. Answer compact JSON with overlap "true", "false", or "unknown" and one short '
        'visible evidence sentence. No task progress judgment.'
    )
    for number in ('0001', '0004'):
        capture = cv2.VideoCapture(str(args.input_dir / f'{number}.mp4'))
        frames = []
        try:
            while True:
                okay, frame = capture.read()
                if not okay:
                    break
                frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        finally:
            capture.release()
        if len(frames) != 15:
            raise ValueError((number, len(frames)))
        for second in (0, 14):
            full = Image.fromarray(frames[second]).resize((512, 384))
            crop_box = (170, 260, 365, 430)
            crop = Image.fromarray(frames[second]).crop(crop_box).resize((512, 384))
            for view, image in (('full', full), ('source_crop', crop)):
                content = [{'type': 'text', 'text': prompt}, {'type': 'image', 'image': image}]
                inputs = processor.apply_chat_template(
                    [{'role': 'user', 'content': content}], tokenize=True,
                    add_generation_prompt=True, return_dict=True,
                    return_tensors='pt').to('cuda')
                with torch.inference_mode():
                    output = model.generate(**inputs, max_new_tokens=128, do_sample=False)
                raw = processor.batch_decode(
                    output[:, inputs['input_ids'].shape[-1]:], skip_special_tokens=True)[0]
                row = {'video': number + '.mp4', 'second': second, 'view': view,
                       'crop_box': list(crop_box) if view == 'source_crop' else None,
                       'full_frame_pixel_sha256': hashlib.sha256(frames[second].tobytes()).hexdigest(),
                       'prompt': prompt, 'raw': raw, 'posthoc': True}
                with args.output.open('a', encoding='utf-8') as stream:
                    stream.write(json.dumps(row) + '\n')
                    stream.flush()
                print(number, second, view, raw, flush=True)


if __name__ == '__main__':
    main()

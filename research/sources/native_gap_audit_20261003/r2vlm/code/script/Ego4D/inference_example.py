import argparse
import base64
import io
import json
import os
import re
from typing import Optional

from openai import OpenAI
from qwen_vl_utils import fetch_image


PROMPT = """You are a professional assistant skilled in understanding temporal videos and estimating task progress.
You will be given a history chain of thought (CoT) summarizing completed and remaining steps, along with incremental egocentric video frames.
Your task is to:
1. Analyze the new frames to detect any completed actions or state changes.
2. Update the list of completed steps and revise the remaining steps accordingly. (Merge, split, or reorder steps if necessary)
3. Estimate the overall task completion progress as a percentage, based on the proportion of completed steps made toward the full task. (eg. finish 1 of 3 tasks, progress is 33~66)
Use the following output format:
<think>
[Updated chain of thought: clearly list revised completed steps and remaining steps.]
</think>
<answer>
[Task completion percentage based on the proportion of completed steps, an integer between 0 and 100]
</answer>

History CoT: {history_cot}
Images:
"""


def encode_image(image_path: str) -> str:
    image_pil = fetch_image({"image": image_path})
    buffer = io.BytesIO()
    image_pil.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def load_data(data_path: str):
    if data_path.endswith(".jsonl"):
        with open(data_path, "r") as f:
            return [json.loads(line) for line in f if line.strip()]

    with open(data_path, "r") as f:
        return json.load(f)


def resolve_turn_images(image_root: str, item_id: int, step_id: int, frame_count: int):
    image_dir = os.path.join(image_root, str(item_id), str(step_id), "images_4")
    image_paths = [
        os.path.join(image_dir, f"{frame_idx:03d}.jpg")
        for frame_idx in range(frame_count)
    ]

    missing = [image_path for image_path in image_paths if not os.path.exists(image_path)]
    if missing:
        raise FileNotFoundError(
            "Missing input images for this turn:\n" + "\n".join(missing)
        )

    return image_paths


def run_single_sample(
    client: OpenAI,
    sample: dict,
    model_name: str,
    image_root: str,
    question_prefix: Optional[str] = None,
    frame_count: int = 4,
    max_tokens: int = 1024,
):
    question = sample["question"]
    if question_prefix:
        question = question_prefix + question

    history = (
        "This is the initial step, with no history CoT available. "
        "Please generate an initial task decomposition based on your understanding "
        "of the task and the observed video content, identifying completed and "
        "incomplete steps. Output in the format specified above."
    )

    outputs = {
        "item_id": sample["item_id"],
        "question": question,
        "turns": [],
    }

    for turn_idx, turn in enumerate(sample["turns"]):
        image_paths = resolve_turn_images(
            image_root=image_root,
            item_id=sample["item_id"],
            step_id=turn["step_id"],
            frame_count=frame_count,
        )
        content = [{"type": "text", "text": PROMPT.format(history_cot=history)}]
        content.extend(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{encode_image(image_path)}"},
            }
            for image_path in image_paths
        )
        content.append(
            {"type": "text", "text": f"\nQuestion: {question}\nOutput: "}
        )

        completion = client.chat.completions.create(
            model=model_name,
            temperature=0.1,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": content}],
        ).choices[0].message.content.strip()

        think_match = re.search(r"<think>(.*?)</think>", completion, re.DOTALL)
        if think_match:
            history = think_match.group(1).strip()
        else:
            history = completion

        answer_match = re.search(r"<answer>(.*?)</answer>", completion, re.DOTALL)
        answer_text = answer_match.group(1).strip() if answer_match else completion
        answer_text = answer_text.lstrip("[").rstrip("]").strip().strip(".").strip()

        outputs["turns"].append(
            {
                "turn_index": turn_idx,
                "step_id": turn["step_id"],
                "image_paths": image_paths,
                "raw_output": completion,
                "history_cot": history,
                "model_answer": answer_text,
            }
        )

        print(f"\n===== Turn {turn_idx} | step_id={turn['step_id']} =====")
        print(f"Images: {image_paths}")
        print(completion)

    return outputs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=str, required=True)
    parser.add_argument("--model_name", type=str, required=True)
    parser.add_argument("--data_path", type=str, required=True)
    parser.add_argument("--image_root", type=str, required=True)
    parser.add_argument("--sample_index", type=int, default=0)
    parser.add_argument("--prompt", type=str, default=None)
    parser.add_argument("--frame_count", type=int, default=4)
    parser.add_argument("--max_tokens", type=int, default=1024)
    parser.add_argument("--output_json", type=str, default=None)
    args = parser.parse_args()

    data = load_data(args.data_path)
    if not 0 <= args.sample_index < len(data):
        raise IndexError(
            f"sample_index={args.sample_index} is out of range for {len(data)} samples"
        )

    client = OpenAI(api_key="EMPTY", base_url=f"http://0.0.0.0:{args.port}/v1")
    outputs = run_single_sample(
        client=client,
        sample=data[args.sample_index],
        model_name=args.model_name,
        image_root=args.image_root,
        question_prefix=args.prompt,
        frame_count=args.frame_count,
        max_tokens=args.max_tokens,
    )

    if args.output_json:
        with open(args.output_json, "w") as f:
            json.dump(outputs, f, indent=2, ensure_ascii=False)
        print(f"\nSaved output to {args.output_json}")


if __name__ == "__main__":
    main()

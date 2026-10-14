# VLAC-Cut: Video Progress Estimation for Process-Level Robot Rollout Segmentation

<div align="center">

[Paper](https://arxiv.org/abs/2607.09776) ·
[Code](https://github.com/InternRobotics/VLAC-cut) ·
[Model](https://huggingface.co/InternRobotics/VLAC-Cut) ·
[Benchmark](https://huggingface.co/datasets/InternRobotics/VLAC-Cut-Benchmark) ·
[Full Data](https://huggingface.co/datasets/InternRobotics/VLAC-Cut-FullData)

</div>

## Overview

**VLAC-Cut** is a process-level multimodal trajectory critic model. Given a natural-language task instruction, an optional task plan, and a robot rollout video, VLAC-Cut estimates signed task progress over time and identifies temporal segments associated with task advancement or degradation.

Unlike methods that assume task progress increases monotonically over time, VLAC-Cut models non-monotonic execution dynamics, including advancement, stagnation, regression, and recovery. This formulation supports process-level analysis of partial completion, temporary failure, subsequent recovery, and rollout segmentation for post-training data selection.

This repository provides the official VLAC-Cut model inference code, example rollouts, and Video Progress Benchmark evaluation code. The model weights and benchmark data are hosted separately:

* Model weights: [`InternRobotics/VLAC-Cut`](https://huggingface.co/InternRobotics/VLAC-Cut)
* Benchmark data: [`InternRobotics/VLAC-Cut-Benchmark`](https://huggingface.co/datasets/InternRobotics/VLAC-Cut-Benchmark)

## Highlights

* **Video-level temporal reasoning:** Analyzes robot execution videos rather than isolated images or image pairs and identifies temporal segments associated with task advancement or degradation.
* **Non-monotonic progress estimation:** Captures advancement, stagnation, regression, and recovery without imposing a monotonically increasing progress assumption.
* **Zero-shot generalization:** Generalizes across manipulation tasks, scenes, object configurations, and camera viewpoints.
* **Flexible temporal resolution:** Supports configurable video sampling frequencies for both coarse- and fine-grained progress estimation.

## Model Overview

| Property | Description |
|---|---|
| Base model | `Qwen/Qwen3-VL-30B-A3B-Instruct` |
| Input | Task instruction, optional task plan, and sampled video frames |
| Output | Timestamped task-progress estimates |
| Sampling rate | `2 Hz`-`20 Hz` |
| Default sampling rate | `2.0 Hz` |

## Repository Structure

```text
examples/
  example_01/episode.mp4
  example_02/episode.mp4
  example_03/episode.mp4
  reference_outputs/

scripts/
  run_example.py
  build_vpb_manifest.py
  run_vpb_inference.py
  evaluate_vpb_predictions.py
  utils/

docs/
  evaluate_on_vpb.md

real_robot_rl/
  README.md
  client/
  server/
```

## Installation

The instructions below install standalone model inference and benchmark tools.

Clone the repository and install the required dependencies:

```bash
git clone https://github.com/InternRobotics/VLAC-cut
cd VLAC-cut
pip install -r requirements.txt
```

The default model identifier is `InternRobotics/VLAC-Cut`. A local checkpoint directory can also be specified using `--model-path`.

## Quick Start

The repository includes three example robot manipulation episodes.

![VLAC-Cut example predictions](examples/reference_outputs/vlac_cut_examples.gif)

### Example 1

```bash
python scripts/run_example.py \
  --model-path InternRobotics/VLAC-Cut \
  --video-path examples/example_01/episode.mp4 \
  --task-instruction "抓取紫色方块使其从方形洞口落入积木桶中" \
  --task-plan $'爪夹开始移动：0%\n爪夹接近紫色方块：20%\n爪夹抓紧紫色方块：40%\n爪夹抓紧紫色方块接近方形洞口：60%\n爪夹将紫色方块对准方形洞口：80%\n紫色方块从方形洞口落入积木桶中，爪夹移开：100%' \
  --output-jsonl outputs/example_01.jsonl
```

### Example 2

```bash
python scripts/run_example.py \
  --model-path InternRobotics/VLAC-Cut \
  --video-path examples/example_02/episode.mp4 \
  --task-instruction "把洋葱放进快递箱里。" \
  --task-plan $'开始移动:0%\n爪夹靠近洋葱:20%\n爪夹抓取洋葱:40%\n爪夹抓住洋葱接近快递箱:60%\n爪夹将洋葱放入快递箱:80%\n爪夹松开,洋葱落入快递箱:100%' \
  --output-jsonl outputs/example_02.jsonl
```

### Example 3

```bash
python scripts/run_example.py \
  --model-path InternRobotics/VLAC-Cut \
  --video-path examples/example_03/episode.mp4 \
  --task-instruction "将三角烧杯放在三脚架上。" \
  --task-plan $'爪夹准备移动：0%\n爪夹开始移动：10%\n爪夹靠近三角烧杯：20%\n爪夹抓取三角烧杯：40%\n爪夹合拢并靠近三脚架：60%\n爪夹移动到三脚架的正上方：80%\n爪夹松开，三角烧杯落在三脚架上：100%' \
  --output-jsonl outputs/example_03.jsonl
```

### Arguments

* `--model-path`: Hugging Face model identifier or local checkpoint directory.
* `--video-path`: Path to the input execution video.
* `--task-instruction`: Natural-language description of the manipulation task.
* `--task-plan`: Optional step-by-step task plan with progress annotations.
* `--sample-hz`: Video sampling frequency in Hz. The default value is `2.0`.
* `--prompt`: Optional override for the complete model prompt.
* `--output-jsonl`: Optional output path. If omitted, the model response is printed to standard output.

### Prediction Visualization

Render a prediction JSONL file as an annotated video:

```bash
python scripts/utils/render_prediction_video.py \
  --input-jsonl outputs/example_01.jsonl \
  --output-video outputs/example_01_pred_progress.mp4
```

Use the corresponding input and output paths to visualize predictions for `example_02` or `example_03`.

Reference outputs for the bundled examples are available under `examples/reference_outputs/`.

## Video Progress Benchmark

The **Video Progress Benchmark (VPB)** evaluates process-level task progress estimation for robot manipulation. It measures whether a model can capture advancement, stagnation, regression, and recovery throughout an execution video.

Download the benchmark from Hugging Face:

```bash
huggingface-cli download InternRobotics/VLAC-Cut-Benchmark \
  --repo-type dataset \
  --local-dir /path/to/VLAC-Cut-Benchmark
```

The dataset repository contains the official benchmark splits and video archives. This repository provides the corresponding preprocessing, inference, and evaluation code.

## Evaluation on VPB

### 1. Extract the Benchmark Videos

```bash
mkdir -p /path/to/vpb_videos
tar -xf /path/to/VLAC-Cut-Benchmark/data/test_videos.tar \
  -C /path/to/vpb_videos
```

### 2. Extract Video Frames

```bash
python scripts/utils/extract_vpb_frames.py \
  --benchmark-root /path/to/VLAC-Cut-Benchmark/splits \
  --data-root /path/to/vpb_videos \
  --frames-root /path/to/vpb_frames
```

### 3. Build the Evaluation Manifest

```bash
python scripts/build_vpb_manifest.py \
  --benchmark-root /path/to/VLAC-Cut-Benchmark/splits \
  --frames-root /path/to/vpb_frames \
  --out manifests/vlac_cut_vpb_eval.jsonl
```

### 4. Run Inference

```bash
python scripts/run_vpb_inference.py \
  --model-path InternRobotics/VLAC-Cut \
  --manifest manifests/vlac_cut_vpb_eval.jsonl \
  --out predictions/vlac_cut_predictions.jsonl
```

### 5. Evaluate Predictions

```bash
python scripts/evaluate_vpb_predictions.py \
  --benchmark-root /path/to/VLAC-Cut-Benchmark/splits \
  --predictions predictions/vlac_cut_predictions.jsonl \
  --out-json reports/vlac_cut_vpb_eval.json \
  --out-md reports/vlac_cut_vpb_eval.md
```

See [`docs/evaluate_on_vpb.md`](docs/evaluate_on_vpb.md) for prediction formats and metric definitions.

## Real-Robot Reinforcement Learning

For ARX single-arm training with DSRL and VLAC-Cut rewards, follow
[the real-robot installation and launch guide](real_robot_rl/README.md).
It provides separate client, training and reward environments.

Download the [Tube OpenPI checkpoint](https://drive.google.com/file/d/1iRg5cK4lrqFR99WyuRlZh9WR4bFbSOot/view)
(Google Drive, 7.23 GB). See the [checkpoint setup instructions](real_robot_rl/server/README.md#models-and-local-configuration)
for checksum verification, extraction and `CHECKPOINT_PATH` configuration.

Human-labelled success rates use trailing windows of 15 rollouts for Tube and
10 for Tape and Tennis ball, including warmup. Each curve starts at its first
full window.
Each video shows one successful rollout with its saved VLAC-Cut progress prediction.

| Task | Success rate | Rollout and VLAC-Cut prediction |
| --- | --- | --- |
| Tube transfer | ![Tube success rate](real_robot_rl/assets/tube/success_rate.png) | [![Tube rollout with VLAC-Cut progress](real_robot_rl/assets/tube/preview.gif)](real_robot_rl/assets/tube/annotated.mp4)<br>[Rollout](real_robot_rl/assets/tube/rollout.mp4) · [Annotated video](real_robot_rl/assets/tube/annotated.mp4) · [Prediction](real_robot_rl/assets/tube/prediction.jsonl) |
| Tape in box | ![Tape success rate](real_robot_rl/assets/tape/success_rate.png) | [![Tape rollout with VLAC-Cut progress](real_robot_rl/assets/tape/preview.gif)](real_robot_rl/assets/tape/annotated.mp4)<br>[Rollout](real_robot_rl/assets/tape/rollout.mp4) · [Annotated video](real_robot_rl/assets/tape/annotated.mp4) · [Prediction](real_robot_rl/assets/tape/prediction.jsonl) |
| Tennis ball in box | ![Tennis ball success rate](real_robot_rl/assets/tennis_ball/success_rate.png) | [![Tennis ball rollout with VLAC-Cut progress](real_robot_rl/assets/tennis_ball/preview.gif)](real_robot_rl/assets/tennis_ball/annotated.mp4)<br>[Rollout](real_robot_rl/assets/tennis_ball/rollout.mp4) · [Annotated video](real_robot_rl/assets/tennis_ball/annotated.mp4) · [Prediction](real_robot_rl/assets/tennis_ball/prediction.jsonl) |

Curve data: [Tube](real_robot_rl/assets/tube/success_rate.csv) · [Tape](real_robot_rl/assets/tape/success_rate.csv) · [Tennis ball](real_robot_rl/assets/tennis_ball/success_rate.csv).

## Citation

Please cite the following paper when using VLAC-Cut, the released model, or the Video Progress Benchmark:

```bibtex
@misc{zhai2026helphumanefficientlargescalerobot,
      title={HELP: Human-Efficient Large-Scale Robot Post-Training with Rollout Segmentation}, 
      author={Shaopeng Zhai and Qi Zhang and Tianyi Zhang and Haoran Zhang and Fuxian Huang and Zhanhui Lin and Zijun Xu and Weinan Zhang},
      year={2026},
      eprint={2607.09776},
      archivePrefix={arXiv},
      primaryClass={cs.RO},
      url={https://arxiv.org/abs/2607.09776}, 
}
```

## License

The source code in this repository is released under the [MIT License](LICENSE).

The model weights, benchmark videos, and third-party source data may be subject to additional licenses or terms of use. Please refer to the corresponding Hugging Face repositories for details.

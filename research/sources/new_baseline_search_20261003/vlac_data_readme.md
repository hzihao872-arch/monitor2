---
pretty_name: Video Progress Benchmark
tags:
  - robotics
  - embodied-ai
  - video-progress
  - progress-estimation
  - reward-modeling
  - benchmark
license: other
---

# Video Progress Benchmark

<div align="center">

[Paper](https://arxiv.org/abs/2607.09776) ·
[Code](https://github.com/InternRobotics/VLAC-cut) ·
[Model](https://huggingface.co/InternRobotics/VLAC-Cut) ·
[Benchmark](https://huggingface.co/datasets/InternRobotics/VLAC-Cut-Benchmark)

</div>

## Overview

The **Video Progress Benchmark (VPB)** evaluates process-level task progress estimation for robot manipulation. It measures whether a model can capture advancement, stagnation, regression, and recovery throughout an execution video.

VPB is built from the held-out portion of the Progress Annotation Dataset. Unlike endpoint-only evaluations, VPB focuses on temporal task progress and supports analysis of partial completion, temporary failure, and subsequent recovery.

This Hugging Face repository contains the official benchmark splits and video archives. The corresponding preprocessing, inference, and evaluation code is maintained in the GitHub repository.

## Dataset Scale

| Inventory | Records | Episodes | Tasks | Keyframe progress points |
|---|---:|---:|---:|---:|
| Full annotation inventory | 35,230 | 26,615 | 15,206 | 464,446 |
| Curated train/evaluation inventory | 28,167 | 22,978 | 15,206 | 375,172 |

## Official Splits

VPB is organized along two axes: whether the semantic task unit appears in the training split, and whether the annotated trajectory contains a regressive progress transition.

| Split | Records | Episodes | Keyframe progress points |
|---|---:|---:|---:|
| Train | 24,652 | 20,479 | 331,762 |
| Expert seen | 1,043 | 1,033 | 11,769 |
| Expert unseen | 1,043 | 1,035 | 12,333 |
| Non-expert seen | 713 | 706 | 9,458 |
| Non-expert unseen | 716 | 706 | 9,850 |

All views from the same physical execution are assigned to the same split. Held-out progress annotations are excluded from prompt construction, augmentation, in-context demonstration selection, fine-tuning, and checkpoint selection.

## Repository Contents

```text
splits/
  train.json
  test_expert_seen.json
  test_expert_unseen.json
  test_nonexpert_seen.json
  test_nonexpert_unseen.json

data/
  train_videos.tar
  test_videos.tar

checksums.sha256
LICENSE
THIRD_PARTY_LICENSES.md
```

## Data Format

Each split file is a JSON list. Each record includes the trajectory id, task metadata, frame index, dense progress values, semantic anchors, and optional reference context.

The split files use the portable frame prefix:

```text
__VLAC2_FRAMES_ROOT__/
```

Resolve this prefix to the absolute extracted-frame directory when running the GitHub tools.

## Evaluation Protocol

Annotated semantic keyframes are converted into a canonical reference trajectory by piecewise-linear interpolation. This interpolation is an evaluation convention and does not assume that physical progress changes linearly between events.

Global and terminal metrics are computed on the official `1 Hz` evaluation grid. Local direction metrics are computed directly on adjacent annotated semantic anchors. Global metrics are first computed per record and then averaged over metric-valid records so that long videos do not dominate the result.

| Scope | Metrics | What they measure |
|---|---|---|
| Global trajectory | MAE, PRC, VOC | Absolute calibration and ordering of progress states; VOC is reported only for expert trajectories |
| Terminal state | TSA, successful F1, failed/incomplete F1, Macro-F1 | Whether the final state is complete using the common `>= 90` threshold |
| Local direction | AP+, AP-, MacroAP | Whether adjacent semantic events are correctly ranked as improvement or regression |

Detailed running commands and the complete metric implementation are provided in the GitHub repository:

```bash
git clone https://github.com/InternRobotics/VLAC-cut
cd VLAC-cut

python scripts/evaluate_vpb_predictions.py \
  --benchmark-root /path/to/VLAC-Cut-Benchmark/splits \
  --predictions predictions/vlac_cut_predictions.jsonl \
  --out-json reports/vlac_cut_vpb_eval.json \
  --out-md reports/vlac_cut_vpb_eval.md
```

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

The benchmark videos and third-party source data may be subject to additional licenses or terms of use. The source code in the GitHub repository is released under the MIT License.

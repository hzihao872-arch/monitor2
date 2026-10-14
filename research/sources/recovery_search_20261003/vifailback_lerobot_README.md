---
license: mit
language:
- en
task_categories:
- robotics
pretty_name: ViFailback Dataset — LeRobot
size_categories:
- 1M<n<10M
tags:
- LeRobot
- robotics
- aloha
- robot-learning
- manipulation
- failure-recovery
- video
- arxiv:2512.02787
configs:
- config_name: default
  data_files: data/*/*.parquet
---

# ViFailback Dataset — LeRobot

This repository is a [LeRobot](https://github.com/huggingface/lerobot) v2.1 conversion of the trajectory portion of [sii-rhos-ai/ViFailback-Dataset](https://huggingface.co/datasets/sii-rhos-ai/ViFailback-Dataset), introduced in the CVPR 2026 paper [*Diagnose, Correct, and Learn from Manipulation Failures via Visual Symbols*](https://arxiv.org/abs/2512.02787).

<p align="center">
  <a href="https://x1nyuzhou.github.io/vifailback.github.io/">
    <img src="https://img.shields.io/badge/Project-Page-4285F4?logo=googlechrome&logoColor=white" alt="Project Page">
  </a>
  <a href="https://arxiv.org/abs/2512.02787">
    <img src="https://img.shields.io/badge/arXiv-2512.02787-b31b1b?logo=arxiv&logoColor=white" alt="arXiv">
  </a>
  <a href="https://huggingface.co/sii-rhos-ai/ViFailback-8B">
    <img src="https://img.shields.io/badge/🤗_Model-ViFailback--8B-ffc107" alt="HuggingFace Model">
  </a>
  <a href="https://huggingface.co/datasets/sii-rhos-ai/ViFailback-Dataset">
    <img src="https://img.shields.io/badge/🤗_Dataset-ViFailback--Dataset-ffc107" alt="HuggingFace Dataset">
  </a>
  <a href="https://github.com/x1nyuzhou/ViFailback">
    <img src="https://img.shields.io/badge/GitHub-Code-181717?logo=github&logoColor=white" alt="GitHub">
  </a>
</p>

ViFailback contains real-world ALOHA dual-arm manipulation trajectories designed for studying failure diagnosis, failure localization, corrective guidance, recovery, and learning from failed demonstrations. This conversion keeps the robot trajectories in the standard LeRobot layout and preserves the ViFailback annotations in both frame-level features and episode-level metadata.

## Dataset Summary

| Statistic | Value |
|---|---:|
| Episodes | 5,202 |
| Frames | 1,297,146 |
| Tasks | 100 |
| Successful episodes | 657 |
| Failed episodes | 4,545 |
| Avoid keyframes | 4,545 |
| Correct keyframes | 4,545 |
| RGB cameras | 3 |
| Videos | 15,606 |
| Frame rate | 25 FPS |
| Approximate trajectory duration | 14.41 hours |
| Local converted size | approximately 28 GiB |

Each failed episode has one annotated avoid keyframe and one annotated correct keyframe. The failure distribution is:

| Episode outcome / failure type | Episodes | Percentage of all episodes |
|---|---:|---:|
| Success | 657 | 12.63% |
| Task Planning | 645 | 12.40% |
| Gripper 6D-Pose | 2,771 | 53.27% |
| Gripper State | 988 | 18.99% |
| Human Intervention | 141 | 2.71% |

## What Is Included

This repository contains:

- all 5,202 ALOHA trajectories as episode-level Parquet files;
- three synchronized RGB streams per episode, encoded as AV1 MP4 video;
- joint state, joint velocity, joint effort, target joint action, end-effector action, and base action;
- the English task instruction associated with every frame through `task_index` and `meta/tasks.jsonl`;
- frame-level failure and keyframe flags;
- the complete source episode annotations in `meta/vifailback_annotations.jsonl`.

Depth maps, `action_leader`, standalone annotation images, and the ViFailback-Bench/VQA samples are not represented as LeRobot features in this conversion. Fields in the preserved annotations that point to source images or videos are provenance paths relative to the original ViFailback repository; those files are not duplicated here.

## Dataset Structure

```text
vifailback-dataset-lerobot/
├── data/
│   └── chunk-{episode_chunk:03d}/
│       └── episode_{episode_index:06d}.parquet
├── videos/
│   └── chunk-{episode_chunk:03d}/
│       ├── observation.images.cam_high/
│       │   └── episode_{episode_index:06d}.mp4
│       ├── observation.images.cam_left_wrist/
│       │   └── episode_{episode_index:06d}.mp4
│       └── observation.images.cam_right_wrist/
│           └── episode_{episode_index:06d}.mp4
└── meta/
    ├── info.json
    ├── tasks.jsonl
    ├── episodes.jsonl
    ├── episodes_stats.jsonl
    └── vifailback_annotations.jsonl
```

The dataset uses six chunks with up to 1,000 episodes per chunk and a single `train` split covering episodes `0:5202`. No evaluation split is imposed so users can construct task-level, trajectory-level, or failure-type-specific splits appropriate for their experiments.

## LeRobot Features

| Feature | Type and shape | Description |
|---|---|---|
| `observation.state` | `float32[14]` | Current ALOHA puppet-arm joint positions (`qpos`). |
| `action` | `float32[14]` | Target joint positions; the source dataset defines this as `qpos` at the next step. |
| `observation.velocity` | `float32[14]` | Joint velocities (`qvel`). |
| `observation.effort` | `float32[14]` | Joint effort values. |
| `complementary_info.action_eef` | `float32[16]` | Target end-effector poses and gripper states for the two arms. |
| `complementary_info.base_action` | `float32[2]` | Robot base commands `[base_x, base_y]`. |
| `complementary_info.vifailback_flags` | `bool[3]` | Episode failure and annotated keyframe flags described below. |
| `observation.images.cam_high` | video `[3, 480, 640]` | High-view RGB camera, AV1/yuv420p at 25 FPS. |
| `observation.images.cam_left_wrist` | video `[3, 480, 640]` | Left wrist RGB camera, AV1/yuv420p at 25 FPS. |
| `observation.images.cam_right_wrist` | video `[3, 480, 640]` | Right wrist RGB camera, AV1/yuv420p at 25 FPS. |
| `timestamp` | `float32[1]` | Time within the episode in seconds. |
| `frame_index` | `int64[1]` | Zero-based frame index within the episode. |
| `episode_index` | `int64[1]` | Zero-based episode index. |
| `index` | `int64[1]` | Global frame index. |
| `task_index` | `int64[1]` | Index into `meta/tasks.jsonl`. |

For each 14-dimensional joint vector, indices `0:7` describe the left arm and indices `7:14` describe the right arm. Each arm uses six joints followed by one gripper value. The 16-dimensional end-effector vector contains `[x, y, z, qx, qy, qz, qw, gripper]` for the left arm followed by the same values for the right arm.

### Frame-Level ViFailback Flags

`complementary_info.vifailback_flags` is ordered as:

```text
[is_failure_episode, is_avoid_keyframe, is_correct_keyframe]
```

- `is_failure_episode` is true for every frame of a failed episode and false for every frame of a successful episode.
- `is_avoid_keyframe` is true only at the source annotation's avoid keyframe.
- `is_correct_keyframe` is true only at the source annotation's correct keyframe.

This representation supports direct frame-level sampling without parsing JSON metadata.

## ViFailback Episode Metadata

`meta/vifailback_annotations.jsonl` contains one JSON object per episode, ordered by `episode_index`. Every object has the following top-level fields:

| Field | Description |
|---|---|
| `episode_index` | Episode index in this LeRobot dataset. |
| `source_hdf5` | Relative path of the original HDF5 trajectory. |
| `source_task` | Original task-directory name. |
| `source_episode` | Original episode name. |
| `source_repo_id` | `sii-rhos-ai/ViFailback-Dataset`. |
| `num_frames` | Number of frames in the episode. |
| `episode_success` | Normalized value: `success` or `failure`. |
| `avoid_keyframe_indices` | Normalized zero-based avoid-keyframe indices. |
| `correct_keyframe_indices` | Normalized zero-based correct-keyframe indices. |
| `annotation` | Complete original annotation object. |

The nested `annotation` object preserves the original fields `task`, `failure_detection`, `subtasks`, `failure_subtask`, `failure_type`, `keyframe`, `avoidance`, `correction`, `images`, `video`, and `source_index`. In particular, the `avoidance` and `correction` entries retain the low-level natural-language guidance and visual-symbol annotation code.

## Loading the Dataset

The metadata reports LeRobot dataset format `v2.1`. Use a LeRobot release that can read v2.1 datasets.

```python
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset

dataset = LeRobotDataset(
    repo_id="sii-rhos-ai/vifailback-dataset-lerobot",
    download_videos=True,
)

print(dataset)
sample = dataset[0]

state = sample["observation.state"]
action = sample["action"]
cam_high = sample["observation.images.cam_high"]
is_failure, is_avoid, is_correct = sample[
    "complementary_info.vifailback_flags"
]
```

The episode-level annotations can be read after the repository metadata has been downloaded:

```python
import json

annotation_path = dataset.root / "meta" / "vifailback_annotations.jsonl"
with annotation_path.open(encoding="utf-8") as f:
    annotations = [json.loads(line) for line in f]

episode_0_annotation = annotations[0]
print(episode_0_annotation["episode_success"])
print(episode_0_annotation["annotation"]["failure_type"])
```

AV1 decoding support is required to read the RGB videos. If video decoding fails, check that the selected LeRobot video backend and the system FFmpeg installation support AV1.

## Conversion Notes

- Episode ordering is deterministic: task directories are sorted lexicographically and episode numbers are sorted numerically within each task.
- The complete annotations are retained without rewriting their nested contents; normalized outcome and keyframe fields are added at the top level for convenient access.
- RGB frames are decoded without an additional BGR/RGB channel swap, following the storage note in the original ViFailback dataset card.
- Depth data was intentionally omitted from this conversion. The original dataset notes that RGB images and depth maps from Dabai cameras are not spatially aligned and require preprocessing before RGB-D fusion or point-cloud generation.
- Video encoding is lossy AV1. Users requiring the original compressed frames or raw depth should use the source dataset.

## Intended Uses

This dataset is intended for research on:

- robot imitation learning and task-conditioned manipulation;
- manipulation failure detection and classification;
- temporal failure and keyframe localization;
- failure-aware sampling and representation learning;
- corrective-guidance and recovery-policy learning;
- multimodal reasoning over robot state, action, language, and video.

## Limitations and Responsible Use

- The data comes from a particular ALOHA setup, camera configuration, workspace, object distribution, and collection procedure. Results may not transfer directly to other robots or environments.
- Failed trajectories substantially outnumber successful trajectories, and Gripper 6D-Pose failures are the dominant category. Account for this imbalance during training and evaluation.
- `is_failure_episode` is an episode-level label repeated on all frames; it does not mean that every frame visually depicts the failure.
- Avoid and correct keyframes are sparse annotations and should not be interpreted as exhaustive temporal boundaries of a failure event.
- The actions are recorded robot commands/targets, not guarantees of safe execution. Policies trained on this dataset require independent safety validation before deployment on physical hardware.
- This conversion focuses on robot trajectories. Refer to the original ViFailback repository for benchmark-specific and VQA assets.

## Source, License, and Citation

This is a format conversion of [sii-rhos-ai/ViFailback-Dataset](https://huggingface.co/datasets/sii-rhos-ai/ViFailback-Dataset). The source dataset is released under the MIT License. Please follow the source repository's terms and cite the original work when using this conversion.

```bibtex
@inproceedings{zeng2026diagnose,
  title={Diagnose, Correct, and Learn from Manipulation Failures via Visual Symbols},
  author={Zeng, Xianchao and Zhou, Xinyu and Li, Youcheng and Shi, Jiayou and Li, Tianle and Chen, Liangming and Ren, Lei and Li, Yong-Lu},
  booktitle={Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition},
  pages={42386--42395},
  year={2026}
}
```


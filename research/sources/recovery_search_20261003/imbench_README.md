---
license: apache-2.0
pretty_name: "PB Puzzle Stack Collapse Recovery V1"
tags:
  - lerobot
  - robotics
  - imbench
task_categories:
  - robotics
size_categories:
  - n<1K
---
# PB Puzzle Stack Collapse Recovery V1

This dataset is part of the **[IMBench](https://huggingface.co/imbench)** suite,
distributed in the [LeRobot](https://github.com/huggingface/lerobot) **v3.0** format.

## Overview

| | |
|---|---|
| **Episodes** | 10 |
| **Total frames** | 11325 |
| **FPS** | 100 |
| **Robot** | Panda |
| **Cameras** | 3 (rgb_ego_cam, rgb_exo_bird_cam, rgb_gripper_cam) |

## Visualize

Browse episodes interactively in the LeRobot Visualizer:

→ https://lerobot-visualize-dataset.hf.space/imbench/pb-puzzle-stack-collapse-recovery-v1/episode_0

## Load with LeRobot

```python
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset

dataset = LeRobotDataset("imbench/pb-puzzle-stack-collapse-recovery-v1")
```

## Features

- `action` — float32, shape=[7]
- `frame_index.rgb_ego_cam` — int64, shape=[1]
- `frame_index.rgb_exo_bird_cam` — int64, shape=[1]
- `frame_index.rgb_gripper_cam` — int64, shape=[1]
- `observation.ee_poses` — float32, shape=[9]
- `observation.force_torque` — float32, shape=[6]
- `observation.force_torque_world` — float32, shape=[3]
- `observation.joint_positions` — float32, shape=[9]
- `observation.object_pos` — float32, shape=[3]
- `observation.object_quat` — float32, shape=[4]
- `observation.object_state` — float32, shape=[31]
- `observation.rgb_ego_cam` — video, shape=[480, 640, 3]
- `observation.rgb_exo_bird_cam` — video, shape=[480, 640, 3]
- `observation.rgb_gripper_cam` — video, shape=[480, 640, 3]
- `observation.robot0_eef_pos` — float32, shape=[3]
- `observation.robot0_eef_quat` — float32, shape=[4]
- `observation.robot0_gripper_qpos` — float32, shape=[2]
- `observation.robot0_joint_pos` — float32, shape=[7]
- `observation.robot0_joint_vel` — float32, shape=[7]
- `observation.robot0_tactile_left` — float32, shape=[8, 8]
- `observation.robot0_tactile_right` — float32, shape=[8, 8]
- `reward` — float32, shape=[1]
- `task_score` — float32, shape=[1]

## Files

```
data/chunk-000/file-000.parquet            # frame data, all episodes aggregated
videos/observation.<cam>/chunk-000/...     # per-camera video shards
meta/
  info.json
  stats.json
  tasks.parquet
  episodes_extra.json
  episodes/chunk-000/file-000.parquet
```

## License

Released under the APACHE-2.0 license.

---
pretty_name: RoboPulse++
license: other
task_categories:
- video-classification
tags:
- robotics
- progress-estimation
- process-reward-model
- arxiv:2608.14284
size_categories:
- n<1K
configs:
- config_name: default
  data_files:
  - split: test
    path: RoboPulsePlusPlus.jsonl
---

# RoboPulse++

RoboPulse++ is an interval-level benchmark introduced in [PRM-as-a-Judge 1.5: A Toolkit for Robot Process Assessment](https://arxiv.org/abs/2608.14284) for evaluating progress judge models throughout complete robot manipulation trajectories.

This Hugging Face release contains `700` episodes with natural-language task instructions, temporally ordered observations, and human-annotated progress intervals.

## Overview

RoboPulse++ extends progress judging from isolated state pairs to temporal intervals. It covers atomic manipulation skills, compositional tasks, and long-horizon execution across diverse embodiments, environments, and viewpoints.

The figure below shows the task-semantic coverage reported in Appendix C of the paper.

![RoboPulse++ task-semantic coverage](./assets/robopulsepp_task_coverage.png)

## Files

- `RoboPulsePlusPlus.jsonl`: benchmark annotations, one episode per line
- `images/`: PNG observations organized by episode
- `assets/robopulsepp_task_coverage.png`: task-semantic coverage from the paper
- `assets/robopulsepp_results.png`: main RoboPulse++ results table from the paper
- `.gitattributes`: Git LFS configuration for PNG files
- `README.md`: dataset overview and field definitions

All paths stored in `image_dir` are relative to the release root.

## Dataset Summary

- Episodes: `700`
- Logical trajectory frames: `17052`
- Human-annotated intervals: `2244`
- PNG observations: `26731`
- Total PNG size: `5.53 GB`
- Stored view tracks: `514` one-view, `107` two-view, and `79` three-view episodes

## Results

The figure below shows the progress-direction results reported in Appendix C of the paper.

![RoboPulse++ benchmark results](./assets/robopulsepp_results.png)

The table reports the binary Rising/Falling evaluation used in the paper.

## Data Format

Each line in `RoboPulsePlusPlus.jsonl` is a JSON object with the following fields:

- `episode_id`: unique episode identifier from `1` to `700`
- `image_dir`: release-relative path to the episode image directory
- `total_frames`: number of logical frames in the trajectory
- `num_segments`: number of annotated progress intervals
- `segments`: ordered list of progress intervals
- `task_instruction`: natural-language task instruction

Each item in `segments` contains:

- `start_frame`: zero-based start boundary in logical-frame coordinates
- `end_frame`: zero-based end boundary in logical-frame coordinates
- `reward_label`: progress-direction annotation for the interval

### Image Naming

Each episode is stored under `images/ep001` through `images/ep700`. Images follow this format:

```text
<zero-based-frame-index>_view<track-index>.png
```

For example, logical frame `0` is stored as `000_view1.png`, while logical frame `16` is stored as `016_view1.png`. The `view1`, `view2`, and `view3` suffixes enumerate stored view tracks.

## Directory Layout

```text
RoboPulsePlusPlus/
├── .gitattributes
├── README.md
├── RoboPulsePlusPlus.jsonl
├── assets/
│   ├── robopulsepp_results.png
│   └── robopulsepp_task_coverage.png
└── images/
    ├── ep001/
    │   ├── 000_view1.png
    │   └── ...
    ├── ep002/
    └── ...
```

## Usage

```python
import json
from pathlib import Path

root = Path(".")  # dataset repository root
with (root / "RoboPulsePlusPlus.jsonl").open(encoding="utf-8") as handle:
    episode = json.loads(next(handle))

episode_dir = root / episode["image_dir"]
image_paths = sorted(episode_dir.glob("*.png"))

print(episode["episode_id"], episode["task_instruction"])
print(image_paths[:3])
```

## Usage Notes

- Resolve `image_dir` relative to the dataset root.
- Segment indices and PNG filename prefixes are both zero-based.

## Related Links

- Project page: [PRM-as-a-Judge](https://prm-as-a-judge.github.io/)
- Project repository: [YuyangLiu2003/PRM-as-a-Judge](https://github.com/YuyangLiu2003/PRM-as-a-Judge)
- Paper: [PRM-as-a-Judge 1.5](https://arxiv.org/abs/2608.14284)

## Citation

If RoboPulse++ or PRM-as-a-Judge 1.5 helps your work, please cite:

```bibtex
@article{ji2026prmjudge,
  title   = {PRM-as-a-Judge: A Dense Evaluation Paradigm for Fine-Grained Robotic Auditing},
  author  = {Ji, Yuheng and Liu, Yuyang and Tan, Huajie and Huang, Xuchuan and Huang, Fanding and Xu, Yijie and Chi, Cheng and Zhao, Yuting and Lyu, Huaihai and Co, Peterson and Cao, Mingyu and Zhang, Qiongyu and Li, Zhe and Zhou, Enshen and Wang, Pengwei and Wang, Zhongyuan and Zhang, Shanghang and Zheng, Xiaolong},
  journal = {arXiv preprint arXiv:2603.21669},
  year    = {2026},
  url     = {https://arxiv.org/abs/2603.21669}
}

@article{liu2026prmjudge15,
  title   = {PRM-as-a-Judge 1.5: A Toolkit for Robot Process Assessment},
  author  = {Liu, Yuyang and Shen, Yanqing and Chen, Ruike and Zhao, Jifan and Tian, Yuxuan and Zhang, Yichi and Long, Tianfeng and Yin, Zixuan and Wang, Yipu and Qin, Ziheng and Tan, Wenxing and Shi, Yang and Cao, Mingyu and Xiao, Runze and Wang, Ziqi and Yin, Zhixin and Chu, Shiwei and Zhang, Yi-Fan and Mu, Yao and Ji, Yuheng and Wang, Yihao and Yan, Jun and Wang, Zhongyuan and Wang, Pengwei and Zheng, Xiaolong},
  journal = {arXiv preprint arXiv:2608.14284},
  year    = {2026},
  url     = {https://arxiv.org/abs/2608.14284}
}
```

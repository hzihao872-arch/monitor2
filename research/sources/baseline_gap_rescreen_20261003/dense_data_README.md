---
license: apache-2.0
task_categories:
- robotics
- image-to-text
- reinforcement-learning
tags:
- robot-manipulation
- reward-model
- vision-language
- vlm
- dense-reward
pretty_name: DenseReward
size_categories:
- 500K<n<1M
---

# DenseReward Dataset

🌐 [Project page](https://dense-reward.github.io/) · 📄 [Paper (arXiv:2607.13033)](https://arxiv.org/abs/2607.13033)

This is the dataset for **DenseReward: Dense Reward Learning via Failure Synthesis for Robotic Manipulation**. It pairs single robot-manipulation frames (and short chronological frame windows) with a scalar task-progress reward in `[0.000, 1.000]`, used to finetune a vision-language reward model.

**Models trained on this data:**
- [`densereward/densereward-1frame`](https://huggingface.co/densereward/densereward-1frame): single-frame reward model — one RGB frame + task text → scalar reward.
- [`densereward/densereward-3frame-thinking`](https://huggingface.co/densereward/densereward-3frame-thinking): 3-frame reward model with reasoning — 3 chronological frames + task text → a `<think>` reasoning word, then a scalar reward.

## Dataset structure

```
data/
  droid.zip
  isaac.zip
  robosuite.zip
  libero.zip
splits/
  1frame/{train,val,test}.json          # 1 image per sample -> reward
  3frame-thinking/{train,val,test}.json # 3 chronological images per sample -> <think>reason</think> + reward
  manifest.json                          # trajectory-level train/val/test assignment
```

Each source's images ship as a zip in `data/`. Unzip each one in place so it expands to `data/droid/*.jpg`, matching the paths referenced in `splits/*/*.json`.


## Data format

Each split file is a JSON list of samples in a simple SFT conversation format:

**`splits/1frame/*.json`**: one image, plain reward target
```json
{
  "conversation": [
    {"from": "human", "value": "<image>put the alcohol on the plate"},
    {"from": "assistant", "value": "0.327"}
  ],
  "images": ["data/isaac/isaac_alcohol_0_collision_000_frame_000300.jpg"]
}
```

**`splits/3frame-thinking/*.json`** : 3 chronological images (oldest → current; early frames in a trajectory repeat the first frame to pad the window), a reasoning word, then the reward for the last frame. Here the reward drops (0.341 → 0.327) as the robot collides with the object, and the reasoning word reflects it:
```json
{
  "conversation": [
    {"from": "human", "value": "<image><image><image>put the alcohol on the plate"},
    {"from": "assistant", "value": "<think>\ncollision\n</think>\n\n0.327"}
  ],
  "images": [
    "data/isaac/isaac_alcohol_0_collision_000_frame_000240.jpg",
    "data/isaac/isaac_alcohol_0_collision_000_frame_000270.jpg",
    "data/isaac/isaac_alcohol_0_collision_000_frame_000300.jpg"
  ]
}
```

The `<think>` vocabulary is `correct | miss | collision | fall | not smooth |
failure`.


## License

Released under Apache License 2.0 for this repository.

## Citation

```bibtex
@article{fang2026densereward,
    title={DenseReward: Dense Reward Learning via Failure Synthesis for Robotic Manipulation},
    author={Fang, Yu and Dong, Wanxi and Liu, Jiaqi and Yang, Yue and Huo, Mingxiao and Mu, Yao and Yao, Huaxiu and Li, Li Erran and Szafir, Daniel and Ding, Mingyu},
    journal={arXiv preprint arXiv:2607.13033},
    year={2026}
}
```

---
license: cc-by-4.0
task_categories:
  - robotics
tags:
  - robot-manipulation
  - failure-detection
  - failure-diagnosis
configs:
  - config_name: failtime_short
    data_files:
      - split: train
        path: failtime_short/train.json
      - split: test
        path: failtime_short/test.json
  - config_name: failtime_long
    data_files:
      - split: test
        path: failtime_long/test.json
---

# FailTime

Failure annotations for robot manipulation rollouts, from the paper
**ProTracer: Proprioception-Guided Failure Diagnosis in Robot Manipulation**.
Each episode is labelled as a success or a failure, and every failure carries
the moment it went wrong, its failure type, the reason, and how it could have
been avoided.

- **FailTime-Short** — annotations for [ViFailback](https://github.com/OpenHelix-Team/ViFailback) recordings (AgileX Piper). Download ViFailback separately for the episodes themselves.
- **FailTime-Long** — long-horizon bimanual recordings (ALOHA and SO-101), included here as self-contained HDF5 files.

## Layout

```
failtime_short/    train.json  test.json  tasks/
failtime_long/     test.json   tasks/     episodes/*.hdf5
```

`tasks/` holds one XML per task: instruction, objects and substages.

## Annotations

```json
{"sample": "pour_ball_transfer_cup_episode_19", "task_id": "pour_ball_transfer_cup", "episode": "episode_19",
 "robot": "aloha", "hdf5": "episodes/pour_ball_transfer_cup_episode_19.hdf5", "verdict": "fail",
 "onset": 1.146, "type": ["wrong_object"], "reason": "Expected: ...", "avoidance": "..."}
```

`onset` (seconds), `type`, `reason` and `avoidance` are given for failures only.

## Episodes

Every FailTime-Long HDF5 holds one episode:

| | |
|---|---|
| `observation.state_eef` | both end-effectors: xyz, quaternion xyzw, gripper |
| `observation.state`, `action` | joint states and actions (`observation.effort` on ALOHA) |
| `observation.images.<camera>/mp4_bytes` | three camera videos: left wrist, right wrist, overhead |
| `timestamp`, `frame_index`, `episode_index`, `next.done` | frame bookkeeping |

## Usage

```bash
hf download ChangUoA/FailTime --repo-type dataset --local-dir data
ln -s /path/to/ViFailback/raw_data data/failtime_short/episodes
```

The code is at [github.com/Chang-AIML/ProTracer](https://github.com/Chang-AIML/ProTracer).

## Citation

```bibtex
@article{dong2026protracer,
  title  = {ProTracer: Proprioception-Guided Failure Diagnosis in Robot Manipulation},
  author = {Dong, Chang and Hosseinzadeh, Mehdi and Wong, King Hang and Liu, Lingqiao and Fraysse, Francois and Dayoub, Feras and Nguyen, Minh Hoai},
  year   = {2026}
}
```

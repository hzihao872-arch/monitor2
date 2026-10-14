---
license: other
license_name: mixed-research-use
license_link: LICENSE.md
pretty_name: ContextProgress-Bench
language:
- en
task_categories:
- video-classification
- robotics
tags:
- robotics
- progress-estimation
- reward-modeling
- progress-reward-model
- embodied-ai
- video
- benchmark
size_categories:
- n<1K
configs:
- config_name: episodes
  data_files:
  - split: test
    path: episodes.jsonl
  default: true
- config_name: subtasks
  data_files:
  - split: test
    path: subtasks.jsonl
---

# ContextProgress-Bench

**ContextProgress-Bench** is the benchmark of
[*ProgressCompass: Embodied Progress Reward Models Are Lost Without the Right Context*](https://andyzworks.github.io/progresscompass/).
It tests **context-dependent progress estimation**: robot-manipulation episodes in which the current
frame alone cannot tell how far the task has come, because progress depends on what happened earlier.

[🌐 Project page](https://andyzworks.github.io/progresscompass/) ·
[📄 Paper (arXiv)](https://arxiv.org/pdf/2609.36684) ·
💻 Code: coming soon

![Three moments of one task that need context](assets/teaser.png)

Every task needs at least one of three forms of context:

- **State Recall**: a fact needed for progress, such as which mat a block came from, was visible
  earlier and has left the frame.
- **Sequence Tracking**: steps follow a fixed order, and one frame does not show which are done.
- **Recurrence Disambiguation**: repeated actions produce look-alike frames at very different progress.

| | |
|:--|--:|
| Tasks (hand-selected) | 24 |
| Episodes (5 sampled at random per task) | 120 |
| Annotated ground-truth subtask clips | 552 |
| Frames | 71,708 |
| Duration | 45.1 min |
| Sources | RMBench, RoboDojo, LIBERO-Mem |

![Benchmark statistics](assets/stats.png)

## What is in the paper

The paper runs a paired diagnosis of five Progress Reward Models (PRMs) on this benchmark. Each PRM
keeps its own input format in both runs; **without context** it scores the full episode under the
episode instruction, and **with context** it scores each annotated subtask clip under that subtask's
instruction. Without context, every PRM is far off (MAE 15.6–31.0 on a 0–100 scale), even those that
read the whole history; with the right context, each cuts its error by 77–82%.
ProgressCompass then supplies that context to a frozen PRM with general-purpose VLMs, and cuts the
error of RoboMeter-4B from 25.4 to 9.3.

## Quick start

```python
from datasets import load_dataset
from huggingface_hub import snapshot_download

episodes = load_dataset("Sterzhang/ContextProgress-Bench", "episodes", split="test")   # 120 rows
subtasks = load_dataset("Sterzhang/ContextProgress-Bench", "subtasks", split="test")   # 552 rows
print(episodes[0]["instruction"], episodes[0]["subtask_boundaries"])

root = snapshot_download("Sterzhang/ContextProgress-Bench", repo_type="dataset")       # videos, ~225 MB
video_path = f"{root}/{episodes[0]['video']}"
```

`episodes.jsonl` and `subtasks.jsonl` are flat indexes over the per-episode `manifest.json` files
described below; the `video` field is a path relative to the repository root.

### Ground-truth progress

For an episode with subtasks `[s_k, e_k)`, k = 0 … K−1, the progress of frame `f` in subtask `k` is

```
p(f) = (k + (f - s_k) / (e_k - 1 - s_k)) / K          # 0 at the first frame, 1 at the last
```

so progress rises linearly within each subtask and every subtask has the same weight. The ten
episodes with a `gt_progress` field (all of `RMBench/observe_and_pickup` and
`RoboDojo/match_and_pick_from_conveyor`) use `delayed_linear` progress instead: 0 until
`start_frame`, then linear to 1 at `end_frame`. See [`gt_progress`](#gt_progress--read-this-before-computing-ground-truth).
Scores are reported on a 0–100 scale.

---

This repository holds the task data of the benchmark. It contains no
baseline predictions and no model outputs.

The data is stored in its final, ready-to-read form: using the benchmark
requires no build, copy, or instruction-processing step.

Everything needed to use the benchmark is in this directory and described
below.

## Scope

| | |
|:--|--:|
| Tasks | 24 |
| Episodes per task | 5 |
| Full-task videos | 120 |
| Ground-truth subtask clips | 552 |
| Frames | 71,708 |
| Duration | 2,705.67 s (45.09 min) |

## Where the videos come from

None of the videos were recorded for this benchmark. Every episode is taken
from one of three publicly released robot-manipulation datasets and re-cut into
ground-truth subtask clips here. Tasks are grouped by that source dataset,
which is the one partition every episode belongs to exactly once.

| Source | Tasks | Episodes | GT clips | Frames | Duration | FPS | What it is |
|:--|--:|--:|--:|--:|--:|--:|:--|
| RMBench | 9 | 45 | 224 | 29,018 | 967.27 s | 30 | Memory-dependent robotic manipulation benchmark; simulated manipulation tasks. |
| RoboDojo | 13 | 65 | 308 | 39,610 | 1584.40 s | 25 | Unified sim-and-real benchmark for generalist robot manipulation policies. |
| Liberomem | 2 | 10 | 20 | 3,080 | 154.00 s | 20 | Memory-sensitive task suite built on LIBERO, a lifelong robot-learning benchmark. |

Citations for the three sources are in [References](#references) at the end of
this file.

What this benchmark adds on top of the source videos:

- the selection of which episodes to include;
- the ground-truth subtask boundaries, derived per source as described in
  [Ground-truth subtask boundaries](#ground-truth-subtask-boundaries) and
  reviewed by hand;
- rewritten per-subtask and main instructions; and
- the per-task inventory and statistics tabulated here.

The video frames themselves are unmodified. Anyone redistributing this
directory is also redistributing data from the three datasets above, so check
their terms before publishing it.

## Directory structure

```text
ContextProgress-Bench/
├── RMBench/
├── RoboDojo/
└── Liberomem/
```

Each holds its tasks:

```text
<Source>/<Task>/demo_clean/episodes/<Episode>/
```

`cover_blocks` and `swap_blocks` each exist under both RMBench and RoboDojo.
They are different tasks with different recordings, and the source directory
keeps them apart.

## What each task tests

Progress in these tasks cannot be read off the current frame alone; something
earlier in the episode is needed. The column below names the form of context
a task *primarily* demands:

- **State Recall** — a fact needed for progress was visible earlier and is no
  longer observable in the current frame.
- **Sequence Tracking** — steps follow a fixed order, so progress requires
  knowing which steps are done and which comes next.
- **Recurrence Disambiguation** — look-alike frames sit at very different
  progress, so a repeated event must be told apart from its earlier
  occurrences.

**This label is the primary demand, not an exclusive one.** Most episodes
require more than one of the three, and a single instruction can give rise to
all three at once. The label records which form a task was selected to stress;
it does not mean the other two are absent. Counts of tasks or episodes *per
form* therefore do not partition the benchmark and will sum to more than 24 and
120 respectively. Earlier versions of this directory encoded the label as a
top-level `Count/`, `Sequence/`, `State/` split, which wrongly implied a
partition; the split has been removed and the label kept here.

Each `manifest.json` also carries the label in its `primary_setting` field.

### RMBench

| Task | Primary setting | What the task is | GT clips |
|:--|:--|:--|--:|
| `classify_blocks` | Recurrence Disambiguation | Sort two colour classes of blocks into the left and right baskets, completing the first colour before the second and moving one block at a time. | 30 |
| `cover_blocks` | State Recall | Cover three coloured blocks from left to right, then uncover them in red-to-green-to-blue colour order. | 30 |
| `observe_and_pickup` | State Recall | Remember the reference object on a shelf and, after it is occluded, pick up the matching object from a set on the table. | 10 |
| `place_block_mat` | State Recall | Move each red block onto the green mat and return it to its original blue mat, processing the blocks from left to right. | 30 |
| `press_button` | Recurrence Disambiguation | Press the left and middle buttons according to two visible counts, then press the right confirmation button once. Every press is an independent event. | 45 |
| `put_back_block` | State Recall | Move a block from its starting mat to the space between two mats, press the button, then return the same block to its original mat. | 15 |
| `rearrange_blocks` | Sequence Tracking | Move the block between two blue mats onto the empty mat, press the button, then move the block that started on a mat into the space between the mats. | 15 |
| `storage_blocks` | Recurrence Disambiguation | Store all blocks in a basket. Two arms may handle two blocks simultaneously, followed by any remaining single block. | 29 |
| `swap_blocks` | State Recall | Use the empty mat to complete three block transfers, then press the button. | 20 |

### RoboDojo

| Task | Primary setting | What the task is | GT clips |
|:--|:--|:--|--:|
| `classify_objects` | Sequence Tracking | Sort the episode's object classes into three baskets in the specified category order, moving one object at a time. | 33 |
| `cover_blocks` | State Recall | Cover three coloured blocks with cups from left to right, then uncover them in the colour order given by the instruction. | 30 |
| `fill_egg_holder` | Recurrence Disambiguation | Place four eggs into the holder one at a time, then close the holder lid. | 25 |
| `fill_pen_holder` | Sequence Tracking | Insert five pens into the pen holder in the colour order given by the instruction. | 25 |
| `hang_mugs` | Sequence Tracking | Hang three mugs on the rack in right-to-middle-to-left spatial order. | 15 |
| `insert_tubes` | Sequence Tracking | Insert three matching pieces in the specified middle-to-right-to-left order. | 15 |
| `match_and_pick_from_conveyor` | State Recall | Remember the first reference object on the conveyor and pick up its later matching instance after distractor objects appear. | 5 |
| `organize_table` | Sequence Tracking | Place an alarm clock, figurine, mouse and keyboard at their destinations in the required order. | 20 |
| `pack_objects_into_box` | Sequence Tracking | Put four distinct objects into a box in the order given by the instruction. | 20 |
| `play_stacking_toy` | Sequence Tracking | Place all ten toy pieces onto the corresponding pegs according to shape and colour priority. | 50 |
| `sort_nesting_dolls_by_size` | Sequence Tracking | Arrange five nesting dolls from smallest to largest. | 25 |
| `store_laptop_and_headphones` | Sequence Tracking | Place the headphones on their stand, close the laptop, then place the laptop in the vertical stand. | 15 |
| `swap_blocks` | State Recall | Track the changing source and destination states across three block transfers and press the button after each transfer. | 30 |

### Liberomem

| Task | Primary setting | What the task is | GT clips |
|:--|:--|:--|--:|
| `cream_cheese_empty_basket` | State Recall | Put the cream-cheese block into the specified basket, then pick up the other basket, which remains empty. | 10 |
| `cream_cheese_filled_basket` | State Recall | Put the cream-cheese block into the specified basket, then pick up that same basket, which now contains the block. | 10 |

Task counts by primary setting — again, these are primary labels, not a
partition:

| Primary setting | Tasks | Episodes |
|:--|--:|--:|
| State Recall | 10 | 50 |
| Sequence Tracking | 10 | 50 |
| Recurrence Disambiguation | 4 | 20 |

## Episode structure

```text
<Source>/<Task>/demo_clean/episodes/<Episode>/
├── full_video.mp4
├── manifest.json
└── subtasks/
    └── subtaskNN/
        ├── video.mp4
        └── instruction.json
```

- **`full_video.mp4`** — the complete task video.
- **`manifest.json`** — identifiers, the main instruction, frame count, fps,
  the provenance of the subtask boundaries, and one entry per ground-truth
  subtask giving its frame range and instruction.
- **`subtasks/subtaskNN/`** — one ground-truth subtask clip cut from the full
  video, with the instruction for that segment.

Every task has exactly five episodes, `episode1` through `episode5`. Subtask
directories are consecutive and zero-padded from `subtask00`. Episodes carry
between 1 and 11 ground-truth subtasks.

Frame rates differ by source: RMBench 30 fps, RoboDojo 25 fps, Liberomem
20 fps. Code that samples by time rather than by frame index must read `fps`
from the manifest.

## Episode numbering

`episode1`–`episode5` are benchmark IDs assigned here. The source datasets use
their own non-contiguous IDs, which earlier versions of this directory used
directly. The original ID is preserved in two places:

- the `original_episode` field of every `manifest.json` and every
  `subtasks/*/instruction.json`; and
- [`episode_id_mapping.json`](episode_id_mapping.json), a machine-readable map
  for all 24 tasks.

| Source | Task | Original IDs for episode1 … episode5 |
|:--|:--|:--|
| Liberomem | `cream_cheese_empty_basket` | 1 , 2 , 4 , 7 , 8 |
| Liberomem | `cream_cheese_filled_basket` | 1 , 2 , 5 , 7 , 9 |
| RMBench | `classify_blocks` | 7 , 9 , 11 , 14 , 18 |
| RMBench | `cover_blocks` | 6 , 12 , 16 , 17 , 19 |
| RMBench | `observe_and_pickup` | 0 , 2 , 4 , 12 , 19 |
| RMBench | `place_block_mat` | 4 , 10 , 14 , 15 , 16 |
| RMBench | `press_button` | 1 , 5 , 13 , 18 , 19 |
| RMBench | `put_back_block` | 2 , 8 , 9 , 11 , 18 |
| RMBench | `rearrange_blocks` | 0 , 7 , 14 , 16 , 19 |
| RMBench | `storage_blocks` | 0 , 1 , 13 , 16 , 18 |
| RMBench | `swap_blocks` | 0 , 7 , 12 , 15 , 17 |
| RoboDojo | `classify_objects` | 0 , 1 , 3 , 4 , 5 |
| RoboDojo | `cover_blocks` | 1 , 2 , 5 , 8 , 12 |
| RoboDojo | `fill_egg_holder` | 1 , 5 , 6 , 7 , 10 |
| RoboDojo | `fill_pen_holder` | 1 , 2 , 9 , 11 , 12 |
| RoboDojo | `hang_mugs` | 1 , 3 , 7 , 8 , 15 |
| RoboDojo | `insert_tubes` | 0 , 1 , 3 , 9 , 16 |
| RoboDojo | `match_and_pick_from_conveyor` | 5 , 7 , 12 , 15 , 19 |
| RoboDojo | `organize_table` | 0 , 4 , 6 , 7 , 10 |
| RoboDojo | `pack_objects_into_box` | 8 , 12 , 13 , 16 , 19 |
| RoboDojo | `play_stacking_toy` | 1 , 3 , 5 , 7 , 13 |
| RoboDojo | `sort_nesting_dolls_by_size` | 0 , 6 , 8 , 9 , 19 |
| RoboDojo | `store_laptop_and_headphones` | 3 , 9 , 10 , 16 , 19 |
| RoboDojo | `swap_blocks` | 9 , 10 , 14 , 17 , 18 |

The source datasets, and any analysis produced before this renumbering, refer
to episodes by their original IDs.

## Manifest fields

| Field | Meaning |
|:--|:--|
| `dataset`, `task` | source dataset and task name |
| `primary_setting` | the form of context this task primarily demands (see above); not exclusive |
| `episode` | the benchmark ID, `episode1`–`episode5` |
| `original_episode` | the episode ID in the source dataset |
| `main_instruction` | the instruction for the full video |
| `source_video` | always `full_video.mp4` |
| `source_frame_count`, `fps` | length and frame rate of the full video |
| `boundary_source` | how the ground-truth subtask boundaries were derived |
| `subtasks` | one entry per ground-truth subtask: `subtask_id`, `start_frame`, `end_frame_exclusive`, `instruction` |
| `source` | Liberomem only: the originating LIBERO-Mem task, episode, HDF5 file and demo ID |

Subtask ranges are half-open: `start_frame` is included and
`end_frame_exclusive` is not. The ranges tile the full video without gaps, so
the last subtask's `end_frame_exclusive` equals `source_frame_count`.

### `gt_progress` — read this before computing ground truth

Ten episodes carry an extra `gt_progress` object, and evaluation code must
honour it: all five episodes of `RoboDojo/match_and_pick_from_conveyor` and all
five of `RMBench/observe_and_pickup`. No other task uses the field:

```json
"gt_progress": {
  "mode": "delayed_linear",
  "start_frame": 366,
  "end_frame": 442,
  "value_before_start": 0.0,
  "reason": "Observation and memorization are not physical progress. Progress starts when the robot begins the final pickup."
}
```

Both tasks open with a phase in which the robot only observes and memorises —
watching a reference object pass on the conveyor, or waiting for the target to
be occluded — and that waiting is not physical progress. Ground-truth progress
therefore stays at `value_before_start` (0.0) for every frame before
`start_frame`, then rises linearly to 1.0 at `end_frame`.

Code that derives ground truth from the `subtasks` boundaries alone will score
these ten episodes against the wrong curve. The other 110 episodes have no
`gt_progress` field and use the subtask boundaries directly.

## Ground-truth subtask boundaries

Every episode stores its full video, main instruction, manifest, and segmented
ground-truth subtask videos. Boundary provenance differs by source:

- **RMBench** — most tasks use cumulative frame lengths from the original
  language annotation. `storage_blocks` uses placement events followed by video
  review of basket visibility. `place_block_mat` uses video-validated action
  midpoints derived from the original segment boundaries.
- **RoboDojo** — candidate boundaries are aligned from LeRobot gripper and
  action signals, then reviewed episode by episode. A fixed action order is
  reused only after cross-episode endpoint review.
- **Liberomem** — boundaries begin from HDF5 gripper-release transitions, are
  shifted to the first frame in which the block is visibly separated from the
  gripper or begins falling, and are then human-reviewed.

The number of clips under `subtasks/`, the boundaries in `manifest.json`, and
the clip counts tabulated above can therefore be cross-checked per episode.

## References

[1] T. Chen et al., "RMBench: Memory-Dependent Robotic Manipulation Benchmark
with Insights into Policy Design," *arXiv preprint arXiv:2603.01229*, 2026.
DOI: [10.48550/arXiv.2603.01229](https://doi.org/10.48550/arXiv.2603.01229).

[2] T. Chen et al., "RoboDojo: A Unified Sim-and-Real Benchmark for
Comprehensive Evaluation of Generalist Robot Manipulation Policies," *arXiv
preprint arXiv:2607.04434*, 2026.
DOI: [10.48550/arXiv.2607.04434](https://doi.org/10.48550/arXiv.2607.04434).

[3] B. Liu et al., "LIBERO: Benchmarking Knowledge Transfer for Lifelong Robot
Learning," *Advances in Neural Information Processing Systems 36, Datasets and
Benchmarks Track*, 2023.
DOI: [10.52202/075280-1939](https://doi.org/10.52202/075280-1939).

[4] N. Chung et al., "Rethinking Progression of Memory State in Robotic
Manipulation: An Object-Centric Perspective," *Proceedings of the AAAI
Conference on Artificial Intelligence*, vol. 40, no. 5, pp. 3407-3415, 2026.
DOI: [10.1609/aaai.v40i5.37337](https://doi.org/10.1609/aaai.v40i5.37337).


## License

The videos are re-cut, unmodified frames from three public datasets and keep the terms of their
sources: [RMBench](https://github.com/robotwin-Platform/rmbench),
[RoboDojo](https://huggingface.co/datasets/RoboDojo-Benchmark/RoboDojo) and
[LIBERO-Mem](https://arxiv.org/abs/2511.11478) (built on [LIBERO](https://libero-project.github.io/)).
Use them for research, and check each source's terms before any other use.
Our annotations (episode selection, subtask boundaries, rewritten instructions, manifests and
indexes) are released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
See [LICENSE.md](LICENSE.md).

## Citation

```bibtex
@article{zhang2026progresscompass,
  title   = {ProgressCompass: Embodied Progress Reward Models Are Lost Without the Right Context},
  author  = {Zhang, Jianshu and Wu, Keliang and Qian, Chengxuan and Yang, Xiyuan and Zhang, Ce
             and Tian, Ariel and Liu, Anbang and Lu, Haoran and Liu, Han},
  journal = {arXiv preprint arXiv:2609.36684},
  year    = {2026}
}
```

Please also cite the source datasets listed in [References](#references).

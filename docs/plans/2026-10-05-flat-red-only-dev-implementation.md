# Flat Red Only Development Package Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Produce an audited six-class, no-yellow flat-square development candidate where U0 moves the red cube outside the green square without changing its open status.

**Architecture:** Reuse the existing no-yellow `FlatSquareDevEnv`, v2 instruction/predicate, 15 s renderer, and physical contact checks. Add an isolated route/package module so old yellow versions and old scored experiments remain unchanged. Keep anonymous candidate media separate from condition mapping and trajectories.

**Tech Stack:** Python, ManiSkill/SAPIEN, NumPy, ffmpeg, unittest, SHA-256.

---

### Task 1: Contract tests

**Files:** Create `experiments/prerequisite_probe/tests/test_flat_red_only_video_package.py`.

1. Write tests that require U0 to start/end outside the square, move red substantially, keep blue fixed, and leave the goal incomplete; test rejection of U0 red stillness or red entering the target.
2. Run the focused test and record the expected failure from missing implementation.
3. Implement the minimum route selector and physical audit in `experiments/prerequisite_probe/flat_red_only_video_package.py`.
4. Re-run focused tests and existing flat-scene tests.

### Task 2: Route and video generation

**Files:** Extend `experiments/prerequisite_probe/flat_red_only_video_package.py`; create a new output directory under `research/prerequisite_monitor/development/scene_video_next/`.

1. Write a test for exact six-class branch membership, refusal to overwrite prior output, and input/truth file segregation; observe it fail.
2. Implement six-class generation by two captured no-yellow snapshots. Reuse existing keyframe/ffmpeg helpers; save any failed attempt rather than hiding it.
3. Probe U0 first without model inference. If the route fails physical or IK admission, record the failure and adjust only the new route before full generation.
4. Generate six anonymous candidate clips, full truth trajectories, and raw/decoded frame hashes. Check each terminal and B+/B0/open branch signature.

### Task 3: Review and packaging

**Files:** Create reader-only packet and stage note under `research/prerequisite_monitor/development/scene_video_next/flat_red_only_*`; update `stage_S2_video.md`, `admission_log.md`, `artifact_hashes.sha256`.

1. Independently decode all candidate MP4s and compare actual pixels, count, frame indices, file hashes, allowed input fields, and geometry/route checks.
2. Prepare a reader-only packet with anonymous videos and the same final goal; do not include mapping, truth, old scores, or controller outcomes.
3. Reuse the earlier no-yellow B+/N0 reader result only for its stated relation; mark new final-six independent review pending until a new reader submits first answers.
4. Only after that review passes, create runner-compatible numeric `model_input/` and input-only ZIP, run existing runner `--dry-run`, and write a single-scene development handoff. Do not issue `SCENE_READY.json` or new blind tests.

The workspace root is not a Git repository, so a Git commit is unavailable here; save immutable versioned artifacts and SHA-256 evidence instead. User approval for this design and implementation was given by “可以你做吧”.

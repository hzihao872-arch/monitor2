# Evaluating VLAC-Cut on Video Progress Benchmark

This document describes the public VLAC-Cut evaluation workflow for the Video Progress Benchmark (VPB). It uses:

- code from this GitHub repository;
- model weights from `InternRobotics/VLAC-Cut`;
- benchmark splits and videos from `InternRobotics/VLAC-Cut-Benchmark`.

## Evaluation Scope

Official VPB metrics are computed on the released 1 Hz evaluation grid reconstructed from each dense video timeline:

- split scope: `test_expert_seen`, `test_expert_unseen`, `test_nonexpert_seen`, `test_nonexpert_unseen`;
- view scope: the `metadata.main_path` view only;
- global metrics: `MAE`, `PRC`, and `VOC` for expert buckets;
- terminal metrics: final progress threshold `90%`;
- local direction metrics: `AP+`, `AP-`, and `MacroAP_D` on adjacent `semantic_anchors` with `tau=0`;
- coverage: complete predictions are required by default.

VLAC-Cut inference samples model input frames at 2 Hz. This is a model inference setting, not a benchmark-wide requirement. Metrics are still computed on the released 1 Hz evaluation frames.

## 1. Download VPB

```bash
huggingface-cli download InternRobotics/VLAC-Cut-Benchmark \
  --repo-type dataset \
  --local-dir /path/to/VLAC-Cut-Benchmark
```

If the dataset release includes video tar archives, unpack them before frame extraction:

```bash
mkdir -p /path/to/vpb_videos
tar -xf /path/to/VLAC-Cut-Benchmark/data/test_videos.tar -C /path/to/vpb_videos
```

Unpack `train_videos.tar` only if you need training videos or want to extract all splits.

## 2. Extract Frames

```bash
python scripts/utils/extract_vpb_frames.py \
  --benchmark-root /path/to/VLAC-Cut-Benchmark/splits \
  --data-root /path/to/vpb_videos \
  --frames-root /path/to/vpb_frames
```

The split files use portable frame paths. `--frames-root` is the absolute root used to resolve those paths during manifest building.

By default, frame extraction inspects only the four official test buckets. Add `--buckets train` or an explicit bucket list only when you have unpacked the corresponding videos.

## 3. Build the Evaluation Manifest

```bash
python scripts/build_vpb_manifest.py \
  --benchmark-root /path/to/VLAC-Cut-Benchmark/splits \
  --frames-root /path/to/vpb_frames \
  --out manifests/vlac_cut_vpb_eval.jsonl
```

The manifest stores:

- `frames` and `image_paths`: the 2 Hz model input frames;
- `eval_frames`: the public 1 Hz evaluation frames;
- `vlac_cut_prompt`: the exact prompt passed to VLAC-Cut;
- `global_episode_id`: the key used to match predictions with ground truth.

For a small smoke test:

```bash
python scripts/build_vpb_manifest.py \
  --benchmark-root /path/to/VLAC-Cut-Benchmark/splits \
  --frames-root /path/to/vpb_frames \
  --out /tmp/vlac_cut_vpb_manifest_smoke.jsonl \
  --limit-trajectories 2
```

## 4. Run VLAC-Cut Inference

```bash
python scripts/run_vpb_inference.py \
  --model-path InternRobotics/VLAC-Cut \
  --manifest manifests/vlac_cut_vpb_eval.jsonl \
  --out predictions/vlac_cut_predictions.jsonl
```

Use a local checkpoint path instead of `InternRobotics/VLAC-Cut` if the model has already been downloaded.

Each prediction row has this public evaluator schema:

```json
{
  "global_episode_id": "ARX-data/.../episode_000000",
  "frames": [0, 15, 30, 45, 60],
  "response": "时间: 0.0s, 进度: 0%\n时间: 2.0s, 进度: 30%"
}
```

Keep the manifest's original `frames` list in each prediction row. The evaluator aligns parsed progress points back to original frame ids.

## 5. Evaluate Predictions

```bash
python scripts/evaluate_vpb_predictions.py \
  --benchmark-root /path/to/VLAC-Cut-Benchmark/splits \
  --predictions predictions/vlac_cut_predictions.jsonl \
  --out-json reports/vlac_cut_vpb_eval.json \
  --out-md reports/vlac_cut_vpb_eval.md
```

The evaluator is strict by default. If any selected trajectory lacks required curve points, terminal predictions, or local-direction anchor predictions, the command exits before writing reports. Use `--allow-missing` only for diagnostic incomplete runs.

Run the evaluator self-test:

```bash
python scripts/evaluate_vpb_predictions.py --self-test
```

## Metrics

Global progress metrics compare predictions against released `dense_kinematic_progress` values at the selected 1 Hz frames:

- `MAE`: per-trajectory mean absolute error, then averaged equally over trajectories;
- `PRC`: per-trajectory Spearman correlation between ground-truth and predicted progress;
- `VOC`: per-trajectory Spearman correlation between predicted progress and chronological frame order, reported for expert buckets.

Terminal success uses the final selected 1 Hz frame:

- ground-truth success: final GT progress `>= 90`;
- predicted success: final predicted progress `>= 90`;
- reported metrics: `TSA`, `F1_S`, `F1_F`, `MacroF1_T`, and confusion counts.

Local direction AP is computed on adjacent released semantic anchors:

```text
Delta_gt   = gt_anchor_progress_end - gt_anchor_progress_start
Delta_pred = pred_progress_end - pred_progress_start
```

`AP+` ranks positive transitions by `Delta_pred`; `AP-` ranks regressive transitions by `-Delta_pred`; `MacroAP_D` is their average.

# Existing-server runbook for the one-mechanism pilot

This runbook does not authorize renting, purchasing, installing or downloading. Use only the user's existing SSH endpoint if still accessible. No remote command has been run for this pilot as of this file's creation. The server receives exactly two ZIPs: the [input-only package](../scene_video_next/flat_red_only_six_candidate_v1/flat_red_only_development_model_input.zip) and `single_scene_pilot_code_v2.zip`. The latter contains only `pilot_pkg` model-side modules; no scorer or truth file. Verify the two local bundle manifests before transfer.

On the existing host, reserve a **new** directory such as `/root/autodl-tmp/monitor2/single_scene_pilot/flat_red_v1`. Place the two ZIPs there without overwriting an earlier run. Verify their SHA-256 values against `FLAT_DEV_READY.json` and `single_scene_pilot_code_v2_manifest.json` before extracting. Extract code under `code/` and nine input files under `model_input/`. The directory name `model_input` is enforced by every runner.

The following are the pinned paths from the completed earlier cloud run. First check they still exist; do not download them if missing:

```text
BASE=/root/autodl-tmp/monitor2
PY8=$BASE/.venv-topreward/bin/python
PY4=$BASE/.venv-robometer/bin/python
MODEL8=/root/autodl-tmp/hf/hub/models--Qwen--Qwen3-VL-8B-Instruct/snapshots/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b
MODEL4=/root/autodl-tmp/hf/hub/models--robometer--Robometer-4B/snapshots/beef63bc914c5c189329d49c6d712d96d632aa34
TOP=$BASE/research/sources/TOPReward
ROBO=$BASE/research/sources/robometer_pr33_compat
```

Run `pilot_pkg.preflight_single_scene_server` with `--base`, both ZIP paths, `--model8` and `--model4` using the existing Python. Save its JSON output to `raw/server_preflight.json`. It checks GPU, disk, exact commits, the Robometer compatibility patch, local configs, ZIP integrity and allowed file names without model inference. A failed check stops the run. Record package/environment versions and exact weight file hashes with the existing `verify_official_weights.py`/manifest if still present. Do not create a new environment.

Use the isolated code root in `PYTHONPATH`; the TOPReward wrapper also needs its existing repo on `PYTHONPATH`. Keep `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `WANDB_MODE=disabled`. First run `pilot_pkg.run_relation_endpoint_pilot` on **one old development input** with `--limit 1` into `smoke_old.jsonl` outside the primary raw tree, only for format/memory. If old input is absent, stop and record that fact; do not replace the smoke with a completed old full run.

Then use these module/argument combinations on the six new anonymous inputs. Each output path must not already exist:

```text
$PY8 -m pilot_pkg.run_relation_endpoint_pilot --input-dir $RUN/model_input --model-path $MODEL8 --output $RUN/raw/paired.jsonl
$PY8 -m pilot_pkg.run_native_single_scene_pilot --method TOPReward --input-dir $RUN/model_input --repo $TOP --model-path $MODEL8 --output-dir $RUN/raw/topreward
$PY4 -m pilot_pkg.run_native_single_scene_pilot --method Robometer --input-dir $RUN/model_input --repo $ROBO --model-path $MODEL4 --output-dir $RUN/raw/robometer
```

Each runner validates all MP4 and decoded-pixel hashes and reads only `model_input/`. Keep stdout/stderr for the top-level commands outside the raw tree or add them before sealing. The Robometer wrapper saves its six per-video stdout/stderr files under `raw/robometer/`. Do not retry a failed clip under the same run ID. Save failures as failures.

After all three runs, seal the entire primary raw tree, including the preflight report, with:

```text
$PY8 -m pilot_pkg.seal_single_scene_pilot --raw-root $RUN/raw --seal $RUN/raw_seal.json
$PY8 -m pilot_pkg.seal_single_scene_pilot --raw-root $RUN/raw --seal $RUN/raw_seal.json --verify
```

The seal reports `complete` only for 24 paired visual calls, 12 paired decisions, and six result-or-failure rows for each native method. A partial seal is preserved and reported; truth-side analysis requires a complete seal. Transfer `raw/` and `raw_seal.json` back to a new local directory, verify their hashes again, **then** run `analyze_single_scene_pilot.py` locally with `--truth-alias .../truth/server_alias_map.json`. The script writes native raw-scale curve summaries, pairwise orderings, D2/candidate directions and costs, and a fixed semantic evidence audit packet. Human audit of all six clips completes the semantic fields before any architecture claim.

If the primary pattern is unfavorable, the prepared `pilot_pkg.run_semantic_checkpoint_probe` may be run **after** the primary seal using only a locally existing base Qwen3-VL-8B or 4B snapshot. Put those outputs under a separately sealed diagnostic run. Its answer is a separate base-VLM fact probe, never a native TOPReward or Robometer trace and never a primary comparison call. Do not run it automatically just because the primary result is inconvenient; first identify the exact missing evidence checkpoint.

**Next single entry:** local scripts/tests and both ZIPs must pass validation. Then obtain the current existing SSH endpoint, perform the read-only remote preflight, and stop immediately if the instance or any pinned weight is unavailable.

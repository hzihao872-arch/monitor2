# L1/L2 first-batch run card

State on 2026-10-06: local preparation complete; no server connection or new
model output under this design. This is a **seen six-clip development set**.
Use only the user's existing server after they open it. No new rental, download,
installation, model-weight change, or official inference-code change.

## Frozen identity and materials

| Item | SHA-256 |
| --- | --- |
| `design.json` | `0f9ddeb56eb91ef16936114825d4ba28206b8c34451c449f5d87bb970c5f70e7` |
| L1 `first_batch/L1/model_input.zip` | `d19299e3a1a609aaaa42e02474223e748672954b97e575b53d4c09214b0ec1a5` |
| L2 `first_batch/L2/model_input.zip` | `9df5a32ab7f22a13cbda6a536031f8938f0f88d797a274f221eb4d8a7379d3f2` |
| `code_v5.zip` | `800a51e57aa3943626adc1d8f97f1701d004dc877b51b72dafff96e105ac4017` |
| `first_batch_run_remote.sh` | `92fd9aaf84f9f9f0f8c6a422b3c299152fc9c9fdd134f3f36ce6cdb333577bc6` |
| Original R0 input ZIP | `c99543639e2ac7e8ddf270654d1394f42d6f121021463bf3f452648686183cfa` |
| Old v3 code ZIP | `244ef6bdbeb93bc3360149a9801d929dc10c793345e443192bd77141290ea5c5` |
| Old raw result seal | `09edaceac2d967740692e6cfd6e1f10c5aa1da6ae3c225aedf253adbeb176676` |

The v5 ZIP retains the unchanged v3 native runner and adds a batch-specific
preflight, six-clip raw sealer, and official checkpoint shard hashes. The two
input ZIPs each contain exactly nine allowed files. They have one prompt across
all six rows, identical original MP4 bytes, and identical 90 decoded RGB frame
hashes. `truth/`, condition names, continuations, and prior scores are absent.
`first_batch_local_validation.json` records four successful no-model dry runs.

## Existing-server gate before upload

Once the user supplies the live SSH endpoint, check the instance's remaining
rental time in the provider interface. Run only read-only inventory commands
first:

```bash
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader,nounits
df -h /root/autodl-tmp/monitor2
git -C /root/autodl-tmp/monitor2/research/sources/TOPReward rev-parse HEAD
git -C /root/autodl-tmp/monitor2/research/sources/robometer_pr33_compat rev-parse HEAD
test -f /root/autodl-tmp/monitor2/.venv-topreward/bin/python
test -f /root/autodl-tmp/monitor2/.venv-robometer/bin/python
test -f /root/autodl-tmp/hf/hub/models--Qwen--Qwen3-VL-8B-Instruct/snapshots/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b/config.json
test -f /root/autodl-tmp/hf/hub/models--robometer--Robometer-4B/snapshots/beef63bc914c5c189329d49c6d712d96d632aa34/config.json
```

Require approximately 24 GiB available VRAM for the 8B call. Stop if the
instance is absent, its remaining time is too short for the estimated batch,
or weights/cache/source are missing. Record the inventory output locally.

The prior sealed run logged approximately 11.7 seconds of TOPReward per six
clips and 210.6 seconds of Robometer per six clips. Doubling that for L1/L2
gives **about 7.4 minutes of model-call time**, before model startup, six-shard
hashing, transfer and sealing. Reserve at least 20–30 minutes of remaining
instance time; this is an estimate, not a guaranteed completion time. Input
ZIPs total about 3.1 MB; require at least 5 GiB free as the live preflight does.

## Fresh remote run

Use a **new** remote run root, for example:

```bash
RUN=/root/autodl-tmp/monitor2/causal_rescue/20261006_l1_l2_v1
test ! -e "$RUN"
mkdir -p "$RUN/incoming"
```

Upload the three ZIPs and `first_batch_run_remote.sh` into `incoming/` as
`L1.zip`, `L2.zip`, `code_v5.zip`, and `first_batch_run_remote.sh`.
Verify the run-script SHA against the local file before executing it. Do not
upload `design.json`, local package manifests, truth maps, or old results.

```bash
bash "$RUN/incoming/first_batch_run_remote.sh" "$RUN"
```

The script checks all three ZIP hashes, extracts to separate model-input
directories, runs the detailed read-only preflight including GPU/disk,
TOPReward commit, Robometer base commit and exact PR #33 patch, six checkpoint
shard hashes, and `HF_HOME` inheritance into the Robometer subprocess. It then
does four server-side no-model dry runs before four full native cells. Offline
environment variables are fixed. Each cell has a distinct output directory;
failed cells retain their stdout/stderr and exit code. There is no silent retry
under the same run ID.

Seal `raw/` to `raw_seal.json` and verify it before transfer. A `complete`
status means 24 native results. `complete_with_failures` means exactly one
result-or-failure row for each of the 24 calls; failures remain failures.
`incomplete` means missing calls, decoder-pixel mismatch or bad curve shape;
preserve the partial seal and stop analysis. Transfer the raw tree, seal, and
seal summary into a **new** local result directory, then verify all file hashes
again. Keep the remote copy while the rental is live.

## Local analysis after raw seal verification

Only after the raw seal is complete or complete-with-failures, use the local
scorer with the local-only alias file:

```powershell
& 'D:\monitor2\.venv\Scripts\python.exe' -m experiments.prerequisite_probe.score_causal_rescue_batch `
  --raw-root '<new-local-result>\raw' --seal '<new-local-result>\raw_seal.json' `
  --truth-alias 'D:\monitor2\research\prerequisite_monitor\development\scene_video_next\flat_red_only_six_candidate_v1\truth\server_alias_map.json' `
  --output '<new-local-result>\analysis.json'
```

Report all six conditions for L1 and L2, TOPReward raw prefix rewards,
Robometer progress, terminal-control success head, failures, ties, and exact
differences for the five ordered pairs. The prespecified primary value is
`median(t12,t13,t14)-median(t0,t1,t2)`; the prespecified sensitivity is
`t14-median(t0,t1,t2)`. Do not normalize within a video or compare absolute
score scales across models. The four core pairs must all win under both values
for **both methods on the same L arm** to proceed to new-sample replication.
Otherwise prepare and run the conditional V1/C1/Q1 batch under a separately
versioned design and package. A successful old six-clip gate is still only a
development-set finding.

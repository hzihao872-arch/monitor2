# Causal rescue preparation implementation plan

The user supplied and approved the experiment design in
`research/prerequisite_monitor/development/architecture_next/causal_rescue_server_experiment_plan_20261006.md`.
This plan implements the local gates for the first L1/L2 batch. The workspace root
is not a Git repository; identity is recorded with file and source-repository hashes.

1. Freeze R0/L1/L2/C1/Q1 wording, V1 protocol, model revisions, contrasts and stop
   rules in immutable `causal_rescue_20261006/design.json`; write its SHA-256 separately.
2. Test that the input builder preserves all six MP4 bytes and all 90 decoded pixel
   hashes, applies exactly one instruction per arm, and rejects extra files and truth.
   Implement deterministic ZIP creation and per-file manifests; run those tests.
3. Build L1/L2 packages from the sealed R0 model input and verify each with the
   existing native runner's no-model dry run. Record the dry-run logs.
4. Test and implement a batch-specific server preflight and raw sealer. Keep the
   old v3 code package immutable. Bundle the unchanged native runner plus new
   support modules as a new code ZIP, with every member hash recorded.
5. Write exact remote commands and completion/stop checks. Estimate time and disk
   from the prior sealed run; check live resources only after the user opens the
   existing server.
6. Verify all package hashes, tests, dry-run output and no-truth boundary before
   declaring the first batch locally ready.


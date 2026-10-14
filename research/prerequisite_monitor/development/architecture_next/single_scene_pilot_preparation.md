# Single-scene pilot preparation checkpoint, 2026-10-05

## Conclusion

The local model-side, native-baseline, seal, post-seal analyzer and optional fact-probe scripts are ready for an **existing-server preflight**. No SSH connection or model inference for this pilot has been made. The user requested evidence collection to be prepared before server use and a first report after TOPReward, Robometer PR #33 compatibility and relation_endpoint_v1 finish; matched D2 is included as the architecture control.

## Original evidence

- Input-only ZIP SHA-256: `c99543639e2ac7e8ddf270654d1394f42d6f121021463bf3f452648686183cfa`; `FLAT_DEV_READY.json` says six anonymous 15-frame videos, one instruction, nine input files. Independent local decode checks matched 90 frame hashes.
- Model-side code ZIP: `single_scene_pilot_code_v2.zip`, SHA-256 `59d9bb247ffc1b476480ed6e835b952ce79f2d4d2f93dc9716281b3ae9138db1`; nine members under `pilot_pkg/`, no truth, alias mapping, scorer or old results. `single_scene_pilot_code_v1.zip` was an earlier local preparation bundle, superseded before any server transfer.
- Four no-model dry runs passed for paired, TOPReward, Robometer and optional base-VLM fact-probe entrances. The v2 ZIP was imported directly and its native dry run passed. Manifest-to-ZIP file SHA and allowed-member checks passed.
- Targeted unit tests: 27 passed; Python compilation passed. A synthetic full raw tree passed seal/analysis, and post-seal tampering was rejected. This verifies code boundaries, not model behavior.
- `single_scene_pilot_protocol.md` fixes the hoped-for pattern, failure interpretation, scene limitations and semantic evidence checkpoints before inference. `single_scene_pilot_runbook.md` fixes the existing-server-only order. `preflight_single_scene_server.py` checks pinned local resources without model loading or download.

## Strongest counterexample and gate

Native TOPReward and Robometer may succeed on the new flat mechanism; earlier Robometer source-family positives prevent assuming failure. A native score curve exposes no object/relation text. The optional base-VLM fact probe is labeled separate diagnostics, never a native internal trace. G+ full completion and B0 motion asymmetry require explicit audit. One mechanism cannot freeze a method or serve as blind evidence.

**Gate:** local preparation passed. Remote availability and pinned weights are unverified. The user has not yet supplied a confirmed current SSH endpoint; entries in `known_hosts` alone do not identify the still-rented instance. No remote login has been attempted.

**Next single entry:** obtain the current existing SSH endpoint and run read-only preflight. If the instance, source commits, compatibility patch or weights are absent, stop without rental/download. If present, use only the two audited ZIPs, seal three primary outputs before truth-side analysis, and report the initial pattern to the user.

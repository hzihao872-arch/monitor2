# Single-scene development pilot: pre-registered evidence and decision rules

## Scope and input gate

The user authorized using `flat_red_only_six_candidate_v1/FLAT_DEV_READY.json` as **one development mechanism**. This is an explicit pilot exception to the two-mechanism Stage D gate. It cannot establish generalization, trigger `METHOD_FREEZE.json`, or become blind test data. Preserve the first and supplement reader answers separately. Their combined six motion/completion judgments agree with the isolated truth, but the supplement did not spell out G+ tabletop support, release and settling. B0 has more total red-object motion than the one-way clips. The scene report supports necessity of the red object's *state*, not a separately necessary preparatory action.

Before any server connection, verify the input-only ZIP SHA-256 `c99543639e2ac7e8ddf270654d1394f42d6f121021463bf3f452648686183cfa`, six manifest rows, six MP4 hashes, 90 decoded frame hashes, and the absence of truth/condition mapping. Only an existing, still accessible rented instance and local model snapshots may be used. Stop on missing GPU, weights, repository or existing environment; do not rent, purchase, install or download. Keep remote raw files in a new directory. Upload only the input ZIP and model-side code, never `truth/`, continuation or old scores.

## Runs and immutable primary outputs

1. TOPReward official Qwen client at the existing pinned commit/8B weight: all 15 native prefix scores, prefix token counts/timing observed by a non-modifying wrapper, raw and normalized diagnostic curves. The old hardcoded-goal batch script is **not** used; `run_native_single_scene_pilot.py` reads the new instruction from `model_input/manifest.jsonl`.
2. Robometer PR #33 dtype compatibility script at the existing pinned commit/4B weight: 15 native progress values, separate 15 success-head values, stdout/stderr, per-video output hashes, runtime. Keep the strict official original's previous dtype failure distinct; do not rename compatibility output as official original.
3. `relation_endpoint_v1` and D2 on the same 8B snapshot: two calls per arm per clip, inspected seconds 0,2,…,14, 512×384, 512 maximum new tokens per call, same v1 contract and common audit fields. Save every raw response before the next call. Six clips × two arms × two calls = 24 primary visual calls. Alternate arm order across clip aliases. Store actual tokens, latency, peak VRAM, errors, abstentions, prompt hashes and pixel hashes.

Do not calculate condition scores or inspect `truth/server_alias_map.json` until all three raw journals are hashed in a separate seal. A partial run is sealed and reported as partial, not silently retried or scored as zero. `seal_single_scene_pilot.py` hashes the full raw tree. `analyze_single_scene_pilot.py` verifies the seal before reading the truth alias. Native outputs stay on their own scales; compare **pair order**, never absolute native versus Monitor numbers.

## Evidence checkpoints

| Checkpoint | Saved observation | Diagnostic use and limit |
| --- | --- | --- |
| 0. Input | ZIP/MP4/decoded-pixel hashes, instruction, 15 frames, model and source revisions, environment | Catches transport, wrong-goal or decode faults before attributing any failure to a model. |
| 1. Scene construct | Independent first/supplement answers, success predicate, red-state necessity/route evidence, B0 motion audit, G+ support/release/settling audit | If the goal or strict state predicate remains ambiguous, direction scores are protocol diagnostics only. Human agreement does not prove model visibility. |
| 2. Native temporal signal | TOPReward raw 15 prefix scores; Robometer progress **and separate success head**; 0–2 and 12–14 medians, middle peak/trough, step signs, B0 transient versus final | Shows whether the native readout tracks visible completion or preparation. Neither native API exposes object identity or endpoint relation, so curves alone cannot show that it "read" the red/green relation. |
| 3. Explicit model evidence | D2/candidate raw first and final records: object, region, relation, 0/14 states and cited seconds, goal completion, alternative route | Human audit marks first supported failure at visibility, binding, endpoint, relevance, direction or parsing; valid JSON is not valid semantics. |
| 4. Coverage and cost | Per-call tokens, time, failures, invalid JSON, `unknown`; paired directional order at similar coverage | A gain caused only by more actual tokens or abstention is not counted as structural gain. |
| 5. Optional fact probe | `run_semantic_checkpoint_probe.py` on already present 8B/4B **base** checkpoints, only after primary seal if needed | A separately prompted base VLM may show whether a related backbone can describe the relation. This is **not** a TOPReward or Robometer intermediate output and does not prove either native scorer used that fact. Its calls are excluded from primary budgets. |

The post-seal evidence packet has fixed manual fields: object binding, region binding, goal relevance, endpoint 0 and 14, completion, alternative route, cited-frame support, and first supported error. Record `correct`, `wrong`, `unknown` with a short frame-backed reason; leave unobservable internals unassigned.

## Result interpretation, fixed before inference

Report each native method's B+>B0, B+>U0, H−<N0 and G+>N0 on raw post-minus-pre medians, plus post-level ordering. Report D2 and candidate on the same four pairings and all six per-clip directions, evidence validity, coverage, abstention, structural invalidity and actual cost. The hoped-for **strong single-scene pattern** is: each native baseline detects G+>N0 but misses at least two of three implicit prerequisite pairings; the candidate gets all four with valid object/relation/endpoint evidence, similar coverage, and at least one implicit pairing beyond matched D2. This is a descriptive pattern, not a statistical proof from one mechanism. Preserve all ties and opposite outcomes.

If the pattern fails, distinguish:

- **Scene problem:** independent review or frame audit cannot establish a complete G+ or unique red-state necessity; plausible alternate placements remain; B0's extra motion dominates the comparison. Repair the scene before changing the model.
- **Native baselines already work:** one or both native methods win all implicit pairings with a valid G+ anchor. Narrow the claimed gap; do not relabel them failures because our candidate was expected to win.
- **Visual/binding problem:** explicit D2/candidate records misidentify the changed object or 0/14 occupancy on clearly visible frames. Inspect the same-video optional fact probe and frame support; a correct base probe is only suggestive about readout, never proof of native internal semantics.
- **Architecture problem:** D2 sees the correct relation or outperforms the candidate at similar coverage and budget; candidate's locked first nomination causes avoidable `unknown`, or its correct endpoints map to a wrong direction. Keep D2 or revise the specific failed stage as a new version.
- **Readout/objective problem:** human-audited relation is clear and explicit VLM records are correct, but native curves follow only G+ or transient B0 movement. This supports a mismatch between native progress/completion readout and the prerequisite construct, without asserting an unobserved internal perception state.

After the three primary methods finish, first return the raw numerical pattern and limitations to the user. Complete the fixed evidence audit; if unfavorable, use checkpoints to decide whether scene revision, a stronger native baseline interpretation, or architecture revision is warranted. No prompt edits or selective reruns inside this pilot.

**Next single entry:** finish local runner/seal/analyzer tests and a no-model dry run. Only then check the user's existing SSH endpoint and the instance's read-only preflight. Do not connect before the evidence scripts are ready.

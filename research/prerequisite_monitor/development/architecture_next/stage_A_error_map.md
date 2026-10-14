# Stage A — sealed development evidence, 2026-10-05

## Boundary and reproducibility

`case_attribution.csv` indexes **216 saved outputs**: 72 direct D/P/F/D2 model calls, 18 derived H0 decisions, 18 caption-slot decisions, and 108 native TOPReward/Robometer curves (old six, six families, s01/s02). Its `raw_source`, SHA-256, `raw_text` or native `native_delta`, evidence seconds, token counts where exposed, and reason are row-level audit handles. `stage_A_manifest.json` records source and index hashes; `stage_A_counts.json` groups the case-level annotations by condition, mechanism and method. The five previously recorded JSONL replays and the newly indexed old-six caption replay have zero parser/direction/progress differences. This run did not call a model. Build with `python research/prerequisite_monitor/development/architecture_next/build_case_attribution.py`.

The direction labels from old experiments refer to one fixed continuation controller. No existing full configuration has passed semantic, alternative-route, and strict-state-necessity admission. In particular s01 has a no-bar-move off-center final placement candidate; s02 has not excluded a side grasp. Thus a score conflicting with an old label is a **protocol diagnostic**, not automatically a model error about a necessary prerequisite. The 0/14-second statements are single-reviewer, post-score visual audits; contact sheets and old truth are audit-side evidence only, never Monitor input.

## First observable link

The review order is visibility → entity/source/destination binding → 0/14 relation → goal relevance/alternative route → direction → curve mapping. `first_supported_issue` in the CSV marks the earliest link contradicted by the saved text and audited frames; it does **not** identify a hidden causal step inside a VLM. A correct direction with an unsound relation remains a semantic evidence error. `later_issue` records inherited direction risk.

Across 72 D/P/F/D2 outputs: 26 have a supported wrong or irrelevant relation choice and 8 have a supported incorrect endpoint relation. The remaining 38 do not have an annotated first error; this includes correct or insufficiently exposed cases. All 72 are structurally valid. Across 18 H0 results, 9 abstentions arise at its P/F consistency gate, 3 decisions inherit a wrong endpoint relation, and 3 inherit a wrong relevance relation; the other 3 have no annotated first issue. H0 is a deterministic combination, not an independent observer. Among 18 caption decisions: 1 self-contradictory action description, 4 endpoint/entity binding errors, 2 source-spatial omissions, 3 goal-object-as-non-goal bindings, 3 fact-extraction gaps, and 1 wrong endpoint occupancy are directly supported; 4 have no supported first issue. All 108 native curves lack entity/relation traces, so their **internal** first error is not localizable from saved scores. Counts are output-level diagnostics, not independent scene sample counts or prevalence estimates.

### Decisive cases and counterexamples

| Mechanism / condition | Saved observation versus 0/14 frames | Earliest supported problem |
| --- | --- | --- |
| old B+ | D/F/D2 retain only “blue cube not in tray” although red cube leaves the tray. P gives a positive `grasp access` story with wrong spatial basis. | Goal-relevant relation selection before direction. Positive P is not evidence of correct prerequisite reasoning. |
| old B0 | P/F call improved access although red cube returns to the tray. H0 agrees and is positive; D2 stays zero. | Endpoint relation before aggregation. |
| old H− | D/F/D2 overlook newly occupied tray; P describes arm approach as an improvement. | Relation selection, then wrong endpoint direction. |
| s01 B+ / H− | Four v12 methods focus on blue cube not yet placed or grasp access rather than bar across tray opening. Caption makes up a source-slot change or self-contradicts. | Target-end relation or source/target binding. |
| s02 B+ | P and F name the grasp-region improvement and give positive; D/D2 give zero because blue cube remains outside tray. | **Counterexample** to universal visual inability: P/F can identify source-side relevance. |
| s02 B0 / H− | P/F say access improves despite return of the bar or newly placed bridge; caption loses/reverses source slots. | 0/14 endpoint relation, not a demonstrated mapper defect. |
| G+ / N0 | Direct methods generally detect visible completion/static state, but H0 can abstain on P/F field disagreement; caption G+ misbinds the goal object in non-goal slots while completion priority masks it. | Separate a correct direction from evidence quality and coverage. |

The six-family native curves supply an essential opposing pattern: Robometer PR #33 compatibility results give B+>B0 and B+>U0 in both source-grasp families, while four tray-occupancy families fail B+>B0. TOPReward reverses both B+ pairings in all six families, yet both native methods give G+>N0 in all six. These scores are observable failures/successes under the old protocol; no first visual or logical link can be assigned without intermediate outputs. The exact family scores and native source hashes are in the CSV and `reports/prerequisite_unseen_six_families_20261005.md`.

## Two falsifiable fault hypotheses

1. **Endpoint relation selection/binding is a bottleneck.** Prediction: on admitted target and source mechanisms, a relation chosen from the goal and full video, then verified at both endpoints, should reduce wrong B0/H− positives and B+ zeros while improving evidence validity at similar coverage. Falsifier: D2 already names the right entity/region/0/14 relation yet still misses direction, or the candidate gains only through extra pixels, calls, or abstentions. Needed fields: candidate object, source/destination region, relation at 0/14, evidence frame/region, actual budget, direction.
2. **Goal semantics/alternate routes are a separate bottleneck.** Prediction: a visibly clear endpoint can coexist with a valid path that never required moving the object; correct relation extraction will then fail to establish strict necessity. Falsifier: newly admitted mechanisms have route exclusion and predicate agreement, yet relation-correct outputs still misrank B+/B0/U0/H− for a different reason. Needed fields: independent semantics review, predicate version, static endpoint search, multiple route challenges, and model's explicit alternative-route reason. These fields belong to evaluation, never to Monitor input.

## Decision and next single entry

Stage A passes as **diagnostic localization**, with scene validity still failed for architectural claims. Prioritize relation choice/binding and endpoint checking; there is no reproduced old parser reversal. Continue at `literature_update.md` with these two hypotheses, before editing a method prompt. Preserve the native two-family positive counterexample and all `unknown` decisions.

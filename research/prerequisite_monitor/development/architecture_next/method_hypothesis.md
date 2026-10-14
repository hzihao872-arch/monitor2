# Stage C pre-registration — relation endpoint v1

## Candidate choice after A+B

Three candidates: (1) **one relation proposal and endpoint verification in two full-frame visual calls**; (2) add relation-driven crop; (3) add counterfactual F challenger. Choose (1). A has 26 wrong/irrelevant relation choices and 8 endpoint errors among 72 direct outputs; B shows ARS already owns adaptive inspection, CoINS owns explicit removal counterfactuals, and neither supports assuming more calls/crops fix our 15-frame cases. The s01 fixed crop harm and s02 crop help conflict, so (2) is separate future diagnostic. F in old outputs often repeats the final-goal relation and does not name an independent visible alternative; H0 adds abstentions. This is an experiment in the effect of an endpoint-focused second question, **not a claimed new architecture**.

## Falsifiable prediction and failure modes

Both passes see the same full 0,2,…,14 s frames at 512×384, with the same backbone and 512 generated-token limit per pass as D2. Pass 1 must nominate the most goal-relevant visible non-goal object and source or destination relation (or `unknown`), using only goal/video. Pass 2 must verify **that same relation** at first and last frame, challenge a remaining blocker or visible alternative, and output a common v1 event record plus intermediate object/region fields. D2 receives the same intermediate fields and two full-frame calls (direct record, then review), so schema and visual opportunity are shared. No hardcoded color, tray coordinates, condition number, scenario ID, geometry label, crop, third call or evaluator truth appears in the prompts.

Expected correction: B0 return and H− newly placed object should stop looking positive; B+ should no longer be reduced to “goal object not yet placed” when a real source/destination relation visibly changes. It may still fail if perspective hides the relation, object identity is confused, the relation is correct but a side route exists, or the goal allows alternative final states. Explicit goal completion may override preparatory relation only when independently seen. `unknown` is warranted for occlusion, unresolved relation or a specific plausible route; generic uncertainty on clearly visible 0/14 evidence is counted as avoidance, never removed from coverage denominator.

Structured intermediate fields for both methods: `candidate_object`, `region_kind` (`source|destination|transfer|unknown`), `region`, `relation`, `before_satisfied`, `after_satisfied`, goal completion at both endpoints, cited second/region/support, `alternative_route`, `uncertainty_reason`, comparison and direction through the unchanged deterministic mapper. The object/region fields are audited, not fed into the mapper as truth.

## Gate and strongest anticipated disproof

Only admitted, complete, qualitatively different development mechanisms can judge value. If D2 has comparable valid object/relation evidence, equal or better B+/B0/U0/H− orderings at similar coverage and actual cost, choose D2. If relation checking improves direction solely through extra tokens or abstention, reject advantage. If a verified no-move route exists, suspend strict necessity scoring for that mechanism even if the model's relation is correct. The 18 old cases are smoke/interface material only; do not rerun their completed v12 experiment. Native methods retain their own scores.

**Next single entry:** implement `monitor_relation_endpoint_v1.py` with test-first common prompt/parse interface and `budget_protocol.md`; wait for qualified `SCENE_READY.json` before any model comparison.

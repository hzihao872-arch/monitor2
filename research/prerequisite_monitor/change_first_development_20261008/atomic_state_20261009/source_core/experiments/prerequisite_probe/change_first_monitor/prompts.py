"""Versioned, role-separated prompts. Payload examples are intentionally absent."""
CAPABILITIES = ('One tabletop arm can approach, grasp, carry, release and interact with visible movable structures. '
                'It cannot pass through rigid solids, teleport or resize objects. Hidden locks, load capacity and exact reach remain unknown.')
V1 = ('Describe actual visible changes in chronological RGB frames. Bind entities across time. '
      'Record at most three persistent changes or reversals, and a neutral initial scene context. '
      'Robot-only motion, camera movement and occlusion are not automatically environment changes. '
      'Do not infer purpose, utility, completion or a task plan. Return only V1 JSON.')
L2_C = ('For each supplied observed change, propose at most one local, falsifiable relation to the final goal. '
        'Bind the changed entity to the intended target. Include irrelevant or insufficient possibilities. '
        'Give neutral visual questions and explicit falsifiers. No unobserved changes or full task tree. Return L2 JSON.')
L2_D = ('Using the supplied scene and observed changes, directly propose provisional goal state and event effects, '
        'and neutral visual checks that could refute them. Keep completion separate from readiness. Return L2 JSON.')
L2_K = ('From only the initial scene, list at most three local visible conditions relevant to the final goal '
        'from the supplied initial scene. Give neutral visual tests. Avoid a full task tree. Return L2 JSON.')
L2_KPLUS = ('Organize up to three local visible conditions around the final goal, now using the full common scene observations. '
            'Keep target-first condition organization and give neutral tests. Return L2 JSON.')
V3 = ('New visual check. Provisional entity bindings may be wrong. Answer neutral questions using newly supplied RGB pixels. '
      'Check before/after identity, current target placement, visible obstruction and persistence. '
      'A missing observation is not proof of absence. Do not assign task value. Return V3 JSON.')
L4 = ('Use only the verification table and cited facts to assess claims, events, completion, direct readiness, '
      'partial preparation and reversal. Unknown is allowed. Claims are not evidence. '
      'Do not introduce new visual facts, a numeric progress score or a task tree. Return L4 JSON.')
FORMAT = {
 'V1': ('Exact top keys: initial_context, changes, coverage, uncertainty. '
        'initial_context item keys: entity_id, description, region_id, visible_relation (max 6). '
        'changes item keys: change_id, entity_ids, before_refs, after_refs, before, after, observation, status (max 3). '
        'Use only supplied evidence IDs. The observation field is a fixed certainty label: write exactly "observed" or "uncertain", never descriptive prose; put the visual description in before and after. '
        'status=closed_event|open_event. '
        'coverage=complete|overflow|occluded|no_observable_change. uncertainty items have code, detail.'),
 'L2': ('Exact top keys: claims, tests. Use at most 3 short claims and 3 short tests TOTAL, one test per claim; keep each string concise so the complete JSON fits. '
        'Claim item keys: claim_id, change_ids, goal_binding, relation_hypothesis, possible_effect, test_ids, falsifier. '
        'Effect=beneficial|harmful|irrelevant|unknown. falsifier must be a short string. '
        'Test item keys: test_id, neutral_question, entity_ids, requested_refs. '
        'requested_refs contains only supplied image evidence IDs such as f0000 or c0a; if no image evidence IDs were supplied, use []. Never put entity IDs in requested_refs. '
        'For target-first conditions at this stage, change_ids is empty. Cite supplied IDs only.'),
 'V3': ('Exact top keys: facts, change_checks, goal_facts, new_unverified_changes, missing. '
        'facts item keys: test_id, at, value, evidence_refs, visible_statement; at=before|after|current. '
        'change_checks item keys: change_id, exists, evidence_refs. '
        'goal_facts item keys: criterion_id, value, evidence_refs. '
        'new_unverified_changes item keys: description, evidence_refs. '
        'missing item keys: test_id, reason. value/exists=true|false|unknown as JSON strings. '
        'reason=occlusion|identity|geometry|stability|budget|out_of_prefix|not_observable.'),
 'L4': ('Exact top keys: claim_results, events, state, state_fact_ids, net_effect, reversal, unresolved. '
        'claim_results item keys: claim_id, status, used_test_ids, short_reason; status=supported|refuted|unknown. '
        'events item keys: change_ids, impact, basis, fact_ids, reversed_event_ids; '
        'impact=beneficial|harmful|irrelevant|mixed|unknown, basis=observed|inference. '
        'state keys: goal_done, direct_ready, partial_preparation. state_fact_ids has the same three keys, each a fact ID list. '
        'Cite exact IDs from VERIFIED_TABLE.fact_catalog: a visual test fact is test_id@at (for example goal_current@current), not bare test_id; a goal fact uses criterion_id. '
        'State values=true|false|unknown|not_applicable as JSON strings; goal_done cannot be not_applicable. '
        'If goal_done=true, other states must be not_applicable. net_effect=beneficial|harmful|unchanged|mixed|unknown. '
        'reversal=true|false|unknown as JSON string. reversed_event_ids must cite a prior beneficial change ID in this output.'),
}


def stage_prompt(stage, arm, goal, context, payload):
    import json
    j = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True)
    if stage == 'V1':
        if arm=='D4DIRECT':
            return ('Direct goal-conditioned visual review. Describe the visible scene and changes in the required V1 structure; '
                    'do not wait for a goal-blind proposal. GOAL: '+goal+'\nOUTPUT CONTRACT: '+FORMAT['V1'])
        return V1 + '\nOUTPUT CONTRACT: ' + FORMAT['V1']
    if stage == 'L2':
        if arm == 'K4':
            return L2_K + '\nGOAL: ' + goal + '\nCAPABILITIES: ' + CAPABILITIES + '\nINITIAL_CONTEXT: ' + j(context) + '\nOUTPUT CONTRACT: ' + FORMAT['L2']
        if arm == 'KPLUS4':
            return L2_KPLUS + '\nGOAL: ' + goal + '\nCAPABILITIES: ' + CAPABILITIES + '\nOBSERVATIONS: ' + j(payload) + '\nOUTPUT CONTRACT: ' + FORMAT['L2']
        core = L2_C if arm == 'C4' else L2_D
        return core + '\nGOAL: ' + goal + '\nCAPABILITIES: ' + CAPABILITIES + '\nOBSERVATIONS: ' + j(payload) + '\nOUTPUT CONTRACT: ' + FORMAT['L2']
    if stage == 'V3':
        # The L2 relation label, confidence and explanation are not passed.
        return V3 + '\nGOAL: ' + goal + '\nNEUTRAL_QUESTIONS: ' + j(payload) + '\nOUTPUT CONTRACT: ' + FORMAT['V3']
    if stage == 'L4':
        return L4 + '\nGOAL: ' + goal + '\nCAPABILITIES: ' + CAPABILITIES + '\nVERIFIED_TABLE: ' + j(payload) + '\nOUTPUT CONTRACT: ' + FORMAT['L4']
    raise ValueError(stage)

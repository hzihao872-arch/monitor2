"""Two V1 variants and matched compact D/C diagnostic chains."""
CAPABILITIES=('One tabletop arm can approach, grasp, carry, release, and interact with visible movable structures. '
              'It cannot pass through rigid solids, teleport or resize objects. Hidden locks, load capacity and exact reach remain unknown.')
SEMANTICS=('Use only supplied evidence at its exact time. Goal completion, direct readiness, partial preparation, event impact and reversal are separate. '
           'Direct readiness means the object can be placed under the common capabilities without further changing other environment structures. '
           'A useful change may be insufficient preparation. Lack of proof of benefit is not evidence of harm. '
           'Reversal needs an earlier observed gain then loss of the same relation; net_effect compares current with initial state. '
           'When completed, readiness and partial preparation are not_applicable. Completion and mixed are allowed together if a separate harmful change has evidence. '
           'Unknown is allowed; do not invent hidden physics, unobserved changes, or a task tree. Return one complete JSON, no prose or markdown.')
FINAL_SCHEMA=('Exact keys: state, impacts, net_effect, reversal, reason. '
              'state exact keys goal_done, direct_ready, partial_preparation; values "true"|"false"|"unknown" (last two also "not_applicable"). '
              'impacts at most 3 items with exact keys change (integer index in CHANGES), effect (beneficial|harmful|irrelevant|mixed|unknown). '
              'net_effect=beneficial|harmful|unchanged|mixed|unknown; reversal="true"|"false"|"unknown". '
              'reason one sentence max 240 characters. Cite no invented changes.')
V1_SCHEMA=('Exact keys context, changes, coverage. context is one neutral first-scene sentence max 240 characters. '
           'changes at most 3 items; exact keys b, a, object, before, after. b and a are supplied evidence IDs, time(b)<time(a). '
           'object/before/after each max 160 characters; brief visible descriptions. '
           'coverage=complete|overflow|occluded|no_observable_change. Host assigns change numbers and looks up timestamps; do not generate entity IDs or timestamps.')
V1_BASE=('Describe actual visible changes in chronological RGB frames. Bind entities across time. '
         'Record at most three persistent changes or reversals and a neutral initial scene context. '
         'Robot-only motion, camera movement and occlusion are not automatically environment changes. '
         'Do not infer purpose, utility, completion or a task plan. Return only JSON. ')
V1_SECOND=('Compare non-robot scene objects before and after the interaction, including stationary-looking structures. '
           'Distinguish their persistent position/shape changes from arm pose and temporary occlusion. '
           'Keep object control changes too. A return needs a later frame, never an earlier similar image. ')
DRAFT_SCHEMA=('Exact top keys judgment, tests. judgment follows FINAL_CONTRACT. '
              'tests at most 4 items; exact keys change (integer CHANGES index, or -1 for current goal), ref (one evidence ID), '
              'predicate (a single positive yes/no visible assertion max 160 characters at that exact ref). '
              'The host numbers tests. No usefulness words, no hypothetical story in predicate. Avoid negated predicates.')
VERIFY_SCHEMA=('Exact top key facts; at most 5 items with exact keys test (host integer test index), value ("true"|"false"|"unknown"), '
               'ref (the exact requested evidence ref), statement (visible evidence max 240 characters). '
               'Value answers the exact predicate at that ref, not whether some other condition is missing. '
               'If evidence cannot decide use unknown, never invert a question. No usefulness labels, no final judgment.')

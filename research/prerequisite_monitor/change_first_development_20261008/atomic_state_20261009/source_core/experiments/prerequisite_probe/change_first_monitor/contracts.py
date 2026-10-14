"""Strict stage payload validation; audit metadata is host-owned."""
import json

STATES = {'true', 'false', 'unknown', 'not_applicable'}
EFFECTS = {'beneficial', 'harmful', 'irrelevant', 'mixed', 'unknown'}
SPEC = {
 'V1': {'initial_context': (list, 6), 'changes': (list, 3), 'coverage': str, 'uncertainty': (list, 8)},
 'L2': {'claims': (list, 6), 'tests': (list, 6)},
 'V3': {'facts': (list, 24), 'change_checks': (list, 3), 'goal_facts': (list, 8), 'new_unverified_changes': (list, 3), 'missing': (list, 12)},
 'L4': {'claim_results': (list, 6), 'events': (list, 3), 'state': dict, 'state_fact_ids': dict, 'net_effect': str, 'reversal': str, 'unresolved': (list, 12)},
}
ITEM_KEYS = {
 'initial_context': {'entity_id','description','region_id','visible_relation'},
 'changes': {'change_id','entity_ids','before_refs','after_refs','before','after','observation','status'},
 'uncertainty': {'code','detail'},
 'claims': {'claim_id','change_ids','goal_binding','relation_hypothesis','possible_effect','test_ids','falsifier'},
 'tests': {'test_id','neutral_question','entity_ids','requested_refs'},
 'facts': {'test_id','at','value','evidence_refs','visible_statement'},
 'change_checks': {'change_id','exists','evidence_refs'},
 'goal_facts': {'criterion_id','value','evidence_refs'},
 'new_unverified_changes': {'description','evidence_refs'},
 'missing': {'test_id','reason'},
 'claim_results': {'claim_id','status','used_test_ids','short_reason'},
 'events': {'change_ids','impact','basis','fact_ids','reversed_event_ids'},
}


def _refs(values, allowed, errors, label):
    if not isinstance(values, list) or any(not isinstance(x, str) or x not in allowed for x in values):
        errors.append(f'invalid_reference:{label}')


def validate_payload(stage, payload, context):
    errors = []
    spec = SPEC[stage]
    if not isinstance(payload, dict) or set(payload) != set(spec):
        return {'valid': False, 'errors': ['field_set']}
    for key, typ in spec.items():
        val = payload[key]
        if isinstance(typ, tuple):
            if not isinstance(val, typ[0]) or len(val) > typ[1]:
                errors.append(f'shape:{key}')
                continue
            if key=='unresolved':
                if any(not isinstance(item,str) or len(item)>80 for item in val):
                    errors.append('unresolved_item')
                continue
            for item in val:
                if not isinstance(item, dict) or set(item) != ITEM_KEYS[key]:
                    errors.append(f'item_fields:{key}')
                    continue
                if any(isinstance(x, str) and len(x) > 320 for x in item.values()):
                    errors.append(f'text_length:{key}')
        elif not isinstance(val, typ):
            errors.append(f'type:{key}')
    if errors:
        return {'valid': False, 'errors': errors}
    evid = set(context.get('evidence_ids', ()))
    changes = set(context.get('change_ids', ()))
    tests = set(context.get('test_ids', ()))
    claims = set(context.get('claim_ids', ()))
    facts = set(context.get('fact_ids', ()))
    if stage == 'V1':
        if payload['coverage'] not in {'complete','overflow','occluded','no_observable_change'}:
            errors.append('coverage_enum')
        if context.get('proposal_overflow') and payload['coverage']!='overflow':
            errors.append('cpu_candidate_overflow')
        ids = []
        for ch in payload['changes']:
            ids.append(ch['change_id'])
            _refs(ch['before_refs'] + ch['after_refs'], evid, errors, 'V1')
            if ch['observation']=='observed' and (not ch['before_refs'] or not ch['after_refs']):
                errors.append('observed_without_endpoints')
            times=context.get('evidence_times',{})
            if ch['before_refs'] and ch['after_refs'] and all(x in times for x in ch['before_refs']+ch['after_refs']):
                if max(times[x] for x in ch['before_refs'])>min(times[x] for x in ch['after_refs']):
                    errors.append('reversed_evidence_time')
            if ch['observation'] not in {'observed','uncertain'} or ch['status'] not in {'closed_event','open_event'}:
                errors.append('change_enum')
        if len(ids) != len(set(ids)):
            errors.append('duplicate_change')
    elif stage == 'L2':
        for c in payload['claims']:
            _refs(c['change_ids'], changes, errors, 'claim_change')
            if c['possible_effect'] not in EFFECTS:
                errors.append('effect_enum')
        seen = [x['test_id'] for x in payload['tests']]
        if len(seen) != len(set(seen)):
            errors.append('duplicate_test')
        for c in payload['claims']:
            _refs(c['test_ids'], set(seen), errors, 'claim_test')
        for t in payload['tests']:
            _refs(t['requested_refs'], evid, errors, 'test_evidence')
    elif stage == 'V3':
        for f in payload['facts']:
            if f['test_id'] not in tests or f['at'] not in {'before','after','current'} or f['value'] not in {'true','false','unknown'}:
                errors.append('fact_enum_or_ref')
            _refs(f['evidence_refs'], evid, errors, 'fact_evidence')
            if f['value']!='unknown' and not f['evidence_refs']:
                errors.append('unearned_fact')
        for c in payload['change_checks']:
            if c['change_id'] not in changes or c['exists'] not in {'true','false','unknown'}:
                errors.append('change_check')
            _refs(c['evidence_refs'], evid, errors, 'change_evidence')
            if c['exists']!='unknown' and not c['evidence_refs']:
                errors.append('unearned_change_check')
        for f in payload['goal_facts']:
            if f['value'] not in {'true','false','unknown'}:
                errors.append('goal_fact')
            _refs(f['evidence_refs'], evid, errors, 'goal_evidence')
            if f['value']!='unknown' and not f['evidence_refs']:
                errors.append('unearned_goal_fact')
        for f in payload['new_unverified_changes']:
            _refs(f['evidence_refs'], evid, errors, 'new_change_evidence')
        for m in payload['missing']:
            if m['reason'] not in {'occlusion','identity','geometry','stability','budget','out_of_prefix','not_observable'}:
                errors.append('missing_reason')
    else:
        if set(payload['state']) != {'goal_done','direct_ready','partial_preparation'} or set(payload['state_fact_ids']) != set(payload['state']):
            errors.append('state_fields')
        else:
            for key, state in payload['state'].items():
                if state not in STATES or (key == 'goal_done' and state == 'not_applicable'):
                    errors.append(f'state_enum:{key}')
                _refs(payload['state_fact_ids'][key], facts, errors, f'state_fact:{key}')
                if state in {'true','false'} and not payload['state_fact_ids'][key]:
                    errors.append(f'unearned_state:{key}')
            if payload['state']['goal_done'] == 'true' and any(payload['state'][x] != 'not_applicable' for x in ('direct_ready','partial_preparation')):
                errors.append('completed_state_conflict')
            if payload['state']['direct_ready'] == 'true' and payload['state']['partial_preparation'] == 'true':
                errors.append('ready_partial_conflict')
        if payload['net_effect'] not in EFFECTS | {'unchanged'} or payload['reversal'] not in {'true','false','unknown'}:
            errors.append('output_enum')
        for c in payload['claim_results']:
            if c['claim_id'] not in claims or c['status'] not in {'supported','refuted','unknown'}:
                errors.append('claim_result')
            _refs(c['used_test_ids'], tests, errors, 'used_tests')
        prior_beneficial=set()
        any_reversal=False
        for e in payload['events']:
            _refs(e['change_ids'], changes, errors, 'event_changes')
            _refs(e['fact_ids'], facts, errors, 'event_facts')
            if e['impact'] not in EFFECTS or e['basis'] not in {'observed','inference'}:
                errors.append('event_enum')
            if e['impact'] != 'unknown' and not e['fact_ids']:
                errors.append('unearned_event')
            _refs(e['reversed_event_ids'], prior_beneficial, errors, 'reversed_event')
            any_reversal |= bool(e['reversed_event_ids'])
            if e['impact']=='beneficial':
                prior_beneficial.update(e['change_ids'])
        if payload['reversal']=='true' and not any_reversal:
            errors.append('reversal_without_reference')
    return {'valid': not errors, 'errors': errors}


def parse_and_validate(stage, raw, context):
    try:
        obj = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None, {'valid': False, 'errors': ['invalid_json']}
    return obj, validate_payload(stage, obj, context)

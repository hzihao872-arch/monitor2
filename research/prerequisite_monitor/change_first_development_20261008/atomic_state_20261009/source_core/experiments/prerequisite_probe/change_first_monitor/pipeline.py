"""Common-V1 four-slot D4/K4/C4 mechanism comparison."""
import hashlib
import json

from .contracts import parse_and_validate
from .prompts import stage_prompt

LIMITS = {'V1': (5000, 768), 'L2': (2200, 640), 'V3': (7500, 1024), 'L4': (2800, 512)}


class Pipeline:
    def __init__(self, backend, invoke=None):
        self.backend = backend
        self.invoke = invoke or backend.generate

    def _call(self, package, stage, arm, goal, context, payload, ids):
        image_ids = self.image_ids if stage in ('V1', 'V3') else []
        images = [package.read(x, stage) for x in image_ids]
        prompt = stage_prompt(stage, arm, goal, context, payload)
        if stage=='V1':
            prompt += '\nCPU_SEARCH_HINT (may be wrong): camera_uncertain=' + str(self.proposal['camera_uncertain']).lower()
            prompt += '; candidate_count=' + str(len(self.proposal['candidates']))
            prompt += '; candidate_overflow=' + str(self.proposal['overflow']).lower() + '. Inspect all supplied full frames.'
        request = {'stage': stage, 'arm': arm, 'prompt': prompt, 'image_ids': image_ids,
                   'query_id':self.query_id,
                   'image_meta':[{k:package.handles[x].get(k) for k in ('time_ms','parent_id','crop_xyxy')} for x in image_ids],
                   'image_hashes': [hashlib.sha256(x).hexdigest() for x in images], 'images': images,
                   'limits': LIMITS[stage], 'prefix_signature': package.manifest['signature']}
        raw = self.invoke(request)
        if stage=='V1':
            ids=ids|{'evidence_times':{x:package.handles[x]['time_ms'] for x in image_ids},
                     'proposal_overflow':self.proposal['overflow']}
        obj, check = parse_and_validate(stage, raw, ids)
        return {'request': {k:v for k,v in request.items() if k != 'images'}, 'raw': raw, 'payload': obj, 'validation': check}

    def run(self, package, goal, arms=('D4','K4','C4'),query_id='ad_hoc'):
        if any(a not in {'D4','K4','C4','KPLUS4','D4DIRECT'} for a in arms):
            raise ValueError('unsupported arm')
        self.query_id=query_id
        self.image_ids, self.proposal = package.shared_ids()
        evid = set(self.image_ids)
        shared_needed=any(a!='D4DIRECT' for a in arms)
        v1 = self._call(package, 'V1', 'shared', '', None, None, {'evidence_ids': evid}) if shared_needed else None
        outputs = {'shared_v1': v1, 'arms': {}, 'calls': int(shared_needed)}
        for arm in arms:
            records = {}
            arm_v1=v1
            if arm=='D4DIRECT':
                arm_v1=self._call(package,'V1',arm,goal,None,None,{'evidence_ids':evid})
                records['V1']=arm_v1
                outputs['calls']+=1
            observed = arm_v1['payload'] if arm_v1['validation']['valid'] else {'initial_context': [], 'changes': []}
            changes = {c['change_id'] for c in observed['changes']}
            initial = observed['initial_context']
            l2 = self._call(package, 'L2', arm, goal, initial, observed,
                            {'evidence_ids': evid, 'change_ids': changes})
            records['L2'] = l2
            tests = l2['payload']['tests'] if l2['validation']['valid'] else []
            # Global completion check is independent of L2 and still runs after an L2 failure.
            neutral = [{'test_id': t['test_id'], 'neutral_question': t['neutral_question'],
                        'entity_ids': t['entity_ids'], 'requested_refs': t['requested_refs']} for t in tests]
            neutral.append({'test_id': 'goal_current', 'neutral_question': 'What visible end-state evidence supports the final goal now?',
                            'entity_ids': [], 'requested_refs': [x for x in self.image_ids if x.startswith('f')][-2:]})
            visual_context = {'provisional_bindings': [
                {'change_id':c['change_id'],'entity_ids':c['entity_ids'],
                 'before_refs':c['before_refs'],'after_refs':c['after_refs']}
                for c in observed['changes']], 'questions': neutral}
            v3 = self._call(package, 'V3', arm, goal, None, visual_context,
                            {'evidence_ids': evid, 'change_ids': changes, 'test_ids': {t['test_id'] for t in neutral}})
            records['V3'] = v3
            if v3['validation']['valid']:
                vp = v3['payload']
                fact_ids = {f['test_id'] + '@' + f['at'] for f in vp['facts']}
                fact_ids.update(f['criterion_id'] for f in vp['goal_facts'])
                fact_catalog = [{'fact_id':f['test_id']+'@'+f['at'],'value':f['value'],
                                 'evidence_refs':f['evidence_refs']} for f in vp['facts']]
                fact_catalog += [{'fact_id':f['criterion_id'],'value':f['value'],
                                  'evidence_refs':f['evidence_refs']} for f in vp['goal_facts']]
                verified = {'facts': vp, 'fact_catalog':fact_catalog,
                            'claims': l2['payload']['claims'] if l2['validation']['valid'] else [],
                            'change_ids': sorted(changes)}
                l4 = self._call(package, 'L4', arm, goal, None, verified,
                                {'change_ids': changes, 'claim_ids': {c['claim_id'] for c in verified['claims']},
                                 'test_ids': {t['test_id'] for t in neutral}, 'fact_ids': fact_ids})
                records['L4'] = l4
                outputs['calls'] += 3
            else:
                records['L4'] = {'skipped': 'invalid_v3'}
                outputs['calls'] += 2
            records['first_failure']=next((s for s,r in [('V1',arm_v1),('L2',l2),('V3',v3),('L4',records['L4'])]
                                           if not r.get('validation',{}).get('valid',False)),None)
            records['event_snapshot']=[]
            if records['L4'].get('validation',{}).get('valid',False):
                by_change={c['change_id']:c for c in observed['changes']}
                host_ids={}
                for index,event in enumerate(records['L4']['payload']['events']):
                    related=[by_change[x] for x in event['change_ids']]
                    before=[package.handles[x]['time_ms'] for c in related for x in c['before_refs']]
                    after=[package.handles[x]['time_ms'] for c in related for x in c['after_refs']]
                    event_id='ev'+hashlib.sha256(json.dumps([package.manifest['signature'],goal,arm,index,event['change_ids']],
                                                 sort_keys=True).encode()).hexdigest()[:16]
                    records['event_snapshot'].append({'event_id':event_id,'revision':1,
                        'observed_interval_ms':[min(before) if before else None,max(after) if after else None],
                        'proposed_at_ms':package.manifest['as_of_ms'],'confirmed_at_ms':package.manifest['as_of_ms'],
                        'change_ids':event['change_ids'],'fact_ids':event['fact_ids'],'impact':event['impact'],
                        'reversed_event_ids':[host_ids[x] for x in event['reversed_event_ids']]})
                    if event['impact']=='beneficial':
                        for x in event['change_ids']:host_ids[x]=event_id
            outputs['arms'][arm] = records
        outputs['accesses'] = package.accesses
        return outputs

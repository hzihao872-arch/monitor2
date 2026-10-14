import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from experiments.prerequisite_probe.change_first_monitor.contracts import validate_payload
from experiments.prerequisite_probe.change_first_monitor.contracts import SPEC
from experiments.prerequisite_probe.change_first_monitor.prefix import materialize_frames, PrefixPackage
from experiments.prerequisite_probe.change_first_monitor.sampling import sample
from experiments.prerequisite_probe.change_first_monitor.pipeline import Pipeline
from experiments.prerequisite_probe.change_first_monitor.backends import ScriptedBackend
from experiments.prerequisite_probe.change_first_monitor.runner import unknown_answers
from experiments.prerequisite_probe.change_first_monitor.prompts import stage_prompt


class CoreTests(unittest.TestCase):
    def test_prefix_ignores_future_and_rejects_bad_paths(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            base = [np.zeros((32, 32, 3), np.uint8) for _ in range(3)]
            a = materialize_frames(base + [np.full((32, 32, 3), 20, np.uint8)], 2000, root / 'a')
            b = materialize_frames(base + [np.full((32, 32, 3), 90, np.uint8)], 2000, root / 'b')
            self.assertEqual(a['signature'], b['signature'])
            self.assertEqual(len(a['frames']), 3)
            pkg = PrefixPackage(root / 'a')
            self.assertRaises(ValueError, pkg.read, '../x', 'V1')
            self.assertRaises(ValueError, pkg.read, 'not-listed', 'V1')
            self.assertLessEqual(max(x['time_ms'] for x in a['frames']), 2000)

    def test_materialized_model_image_is_bounded(self):
        with tempfile.TemporaryDirectory() as td:
            m=materialize_frames([np.zeros((480,640,3),np.uint8)],0,Path(td))
            self.assertLessEqual(m['frames'][0]['width'],512)
            self.assertLessEqual(m['frames'][0]['height'],384)

    def test_noninteger_cutoff_does_not_interpolate_or_include_future(self):
        with tempfile.TemporaryDirectory() as td:
            frames=[np.zeros((8,8,3),np.uint8) for _ in range(4)]
            m=materialize_frames(frames,1250,Path(td),times_ms=[0,500,1000,1500])
            self.assertEqual([r['time_ms'] for r in m['frames']],[0,500,1000])

    def test_contract_rejects_unearned_facts_and_extra_fields(self):
        good = {'initial_context': [], 'changes': [], 'coverage': 'no_observable_change', 'uncertainty': []}
        self.assertTrue(validate_payload('V1', good, {'evidence_ids': set(), 'change_ids': set()})['valid'])
        bad = dict(good, invented=True)
        self.assertFalse(validate_payload('V1', bad, {'evidence_ids': set(), 'change_ids': set()})['valid'])
        bad = dict(good, changes=[{'change_id': 'e1', 'entity_ids': ['o1'], 'before_refs': ['fake'], 'after_refs': [], 'before': 'x', 'after': 'y', 'observation': 'observed', 'status': 'closed_event'}])
        self.assertFalse(validate_payload('V1', bad, {'evidence_ids': set(), 'change_ids': set()})['valid'])

    def test_valid_unknown_readout_is_not_schema_failure(self):
        self.assertTrue(validate_payload('L4',unknown_answers()['L4'],
                         {'change_ids':set(),'fact_ids':set(),'claim_ids':set(),'test_ids':set()})['valid'])

    def test_v3_determinate_fact_requires_pixel_reference(self):
        v3={'facts':[{'test_id':'q1','at':'current','value':'true','evidence_refs':[],
                      'visible_statement':'visible'}], 'change_checks':[], 'goal_facts':[],
            'new_unverified_changes':[], 'missing':[]}
        check=validate_payload('V3',v3,{'evidence_ids':{'f0000'},'test_ids':{'q1'},'change_ids':set()})
        self.assertFalse(check['valid'])

    def test_v1_rejects_reversed_before_after_evidence(self):
        v1={'initial_context':[], 'changes':[{'change_id':'e1','entity_ids':['o1'],
            'before_refs':['f0002'],'after_refs':['f0000'],'before':'closed','after':'open',
            'observation':'observed','status':'closed_event'}], 'coverage':'complete','uncertainty':[]}
        check=validate_payload('V1',v1,{'evidence_ids':{'f0000','f0002'},
              'evidence_times':{'f0000':0,'f0002':2000}})
        self.assertFalse(check['valid'])

    def test_v1_cannot_claim_complete_when_cpu_candidate_overflows(self):
        v1={'initial_context':[],'changes':[],'coverage':'complete','uncertainty':[]}
        self.assertFalse(validate_payload('V1',v1,{'evidence_ids':set(),'proposal_overflow':True})['valid'])

    def test_sampler_keeps_reversal_and_is_goal_blind(self):
        frames = [np.zeros((48, 48, 3), np.uint8) for _ in range(5)]
        frames[1][10:22, 10:22] = 255
        frames[2][10:22, 10:22] = 255
        out = sample(frames, [i * 1000 for i in range(5)])
        self.assertIn(1, out['selected_indices'])
        self.assertIn(4, out['selected_indices'])
        self.assertGreaterEqual(len(out['candidates']), 1)

    def test_persistent_small_change_gets_priority_crop_over_robot_motion(self):
        with tempfile.TemporaryDirectory() as td:
            frames = [np.zeros((96, 128, 3), np.uint8) for _ in range(15)]
            for i in range(1, 11):
                frames[i][8:48, 5 + 3*i:45 + 3*i] = 255
            for i in range(11, 15):
                frames[i][64:80, 90:106] = 255
            manifest = materialize_frames(frames, 14000, Path(td))
            endpoint = manifest['proposal']['candidates'][0]
            self.assertEqual((endpoint['before_index'], endpoint['after_index']), (0, 14))
            self.assertGreaterEqual(endpoint['bbox_xyxy'][0], 85)
            self.assertEqual([c['parent_id'] for c in manifest['crops'][:2]], ['f0000', 'f0014'])

    def test_reversal_has_no_persistent_endpoint_proposal(self):
        frames = [np.zeros((96, 128, 3), np.uint8) for _ in range(5)]
        frames[1][60:80, 90:110] = 255
        frames[2][60:80, 90:110] = 255
        result = sample(frames, [i * 1000 for i in range(5)])
        self.assertTrue(result['candidates'])
        self.assertFalse(any(c['before_index'] == 0 and c['after_index'] == 4 for c in result['candidates']))

    def test_sampler_preserves_middle_coverage_under_many_changes(self):
        frames=[]
        for i in range(15):
            f=np.zeros((48,48,3),np.uint8)
            if 5<=i<=8:f[10:25,10:25]=255
            if i in (2,3,10,11):f[30:45,30:45]=255
            frames.append(f)
        out=sample(frames,[i*1000 for i in range(15)])
        self.assertTrue(any(i in out['selected_indices'] for i in (6,7,8)))
        self.assertIn(14,out['selected_indices'])

    def test_sampler_marks_global_camera_shift_and_stable_intervals(self):
        rng=np.random.default_rng(7)
        base=rng.integers(0,256,(48,48,3),dtype=np.uint8)
        shifted=np.roll(base,3,axis=1)
        out=sample([base,base.copy(),shifted,shifted.copy()],[0,1000,2000,3000])
        self.assertTrue(out['camera_uncertain'])
        self.assertTrue(out['stable_indices'])

    def test_v1_receives_camera_risk_hint_without_goal(self):
        with tempfile.TemporaryDirectory() as td:
            rng=np.random.default_rng(9)
            base=rng.integers(0,256,(48,48,3),dtype=np.uint8)
            materialize_frames([base,base.copy(),np.roll(base,3,axis=1)],2000,Path(td))
            backend=ScriptedBackend(unknown_answers())
            Pipeline(backend).run(PrefixPackage(td),'secret task',arms=['C4'])
            prompt=next(r for r in backend.requests if r['stage']=='V1')['prompt']
            self.assertIn('camera_uncertain',prompt)
            self.assertNotIn('secret task',prompt)

    def test_v1_prompt_orders_shown_evidence_and_allows_complete_answer(self):
        with tempfile.TemporaryDirectory() as td:
            frames = [np.zeros((32, 32, 3), np.uint8) for _ in range(15)]
            frames[-1][16:26, 16:26] = 255
            materialize_frames(frames, 14000, Path(td))
            backend = ScriptedBackend(unknown_answers())
            Pipeline(backend).run(PrefixPackage(td), 'secret task', arms=['C4'])
            request = next(r for r in backend.requests if r['stage'] == 'V1')
            prompt = request['prompt']
            self.assertIn('f0000@0', prompt)
            self.assertIn('f0014@14000', prompt)
            self.assertIn('before_refs earlier than after_refs', prompt)
            self.assertEqual(request['limits'][1], 1536)
            self.assertNotIn('secret task', prompt)

    def test_shared_observation_keeps_initial_and_current(self):
        with tempfile.TemporaryDirectory() as td:
            frames = [np.full((24,24,3), i, np.uint8) for i in range(15)]
            materialize_frames(frames, 14000, Path(td))
            ids, _ = PrefixPackage(td).shared_ids()
            self.assertEqual(ids[0], 'f0000')
            self.assertIn('f0014', ids)

    def test_change_candidate_materializes_goal_blind_crop_refs(self):
        with tempfile.TemporaryDirectory() as td:
            frames=[np.zeros((64,64,3),np.uint8) for _ in range(4)]
            frames[2][10:28,10:28]=255
            frames[3][10:28,10:28]=255
            m=materialize_frames(frames,3000,Path(td))
            self.assertGreaterEqual(len(m['crops']),2)
            p=PrefixPackage(td)
            ids,_=p.shared_ids()
            self.assertTrue(any(x.startswith('c') for x in ids))
            for x in m['crops']:
                self.assertIn(x['parent_id'],p.all_ids())
                self.assertLessEqual(x['time_ms'],3000)

    def test_reversal_cannot_point_to_nonexistent_achievement(self):
        payload={'claim_results':[],'events':[{'change_ids':['e2'],'impact':'harmful','basis':'inference',
                 'fact_ids':['q@after'],'reversed_event_ids':['invented']}],
                 'state':{'goal_done':'false','direct_ready':'false','partial_preparation':'false'},
                 'state_fact_ids':{'goal_done':['q@after'],'direct_ready':['q@after'],'partial_preparation':['q@after']},
                 'net_effect':'harmful','reversal':'true','unresolved':[]}
        check=validate_payload('L4',payload,{'change_ids':{'e1','e2'},'fact_ids':{'q@after'},'claim_ids':set(),'test_ids':set()})
        self.assertFalse(check['valid'])

    def test_prompts_supply_exact_output_fields_without_cross_stage_goal_leak(self):
        self.assertIn('before_refs', stage_prompt('V1','shared','SECRET GOAL',[],{}))
        self.assertIn('never descriptive prose', stage_prompt('V1','shared','SECRET GOAL',[],{}))
        self.assertNotIn('SECRET GOAL',stage_prompt('V1','shared','SECRET GOAL',[],{}))
        self.assertIn('neutral_question',stage_prompt('L2','C4','g',[],{}))
        self.assertIn('at most 3 short claims and 3 short tests TOTAL',stage_prompt('L2','C4','g',[],{}))
        self.assertIn('Never put entity IDs in requested_refs',stage_prompt('L2','K4','g',[],{}))
        self.assertIn('goal_facts',stage_prompt('V3','C4','g',[],{}))
        self.assertIn('state_fact_ids',stage_prompt('L4','C4','g',[],{}))

    def test_exported_schema_has_exact_stage_fields(self):
        path=Path('experiments/prerequisite_probe/change_first_monitor/protocol/stage_schemas.json')
        schemas=json.loads(path.read_text(encoding='utf-8'))['schemas']
        for stage,spec in SPEC.items():
            self.assertEqual(set(schemas[stage]['properties']),set(spec))
            self.assertFalse(schemas[stage]['additionalProperties'])

    def test_three_arms_share_pixels_and_v1_has_no_goal(self):
        with tempfile.TemporaryDirectory() as td:
            frames = [np.zeros((32, 32, 3), np.uint8) for _ in range(3)]
            manifest = materialize_frames(frames, 2000, Path(td))
            answers = {'V1': {'initial_context': [], 'changes': [], 'coverage': 'no_observable_change', 'uncertainty': []},
                       'L2': {'claims': [], 'tests': []},
                       'V3': {'facts': [], 'change_checks': [], 'goal_facts': [], 'new_unverified_changes': [], 'missing': []},
                       'L4': {'claim_results': [], 'events': [], 'state': {'goal_done': 'unknown', 'direct_ready': 'unknown', 'partial_preparation': 'unknown'}, 'state_fact_ids': {'goal_done': [], 'direct_ready': [], 'partial_preparation': []}, 'net_effect': 'unknown', 'reversal': 'unknown', 'unresolved': ['insufficient_visual_evidence']}}
            backend = ScriptedBackend(answers)
            result = Pipeline(backend).run(PrefixPackage(td), 'Put cube in box', arms=['D4', 'K4', 'C4'])
            self.assertEqual(result['calls'], 10)
            reqs = backend.requests
            self.assertEqual([r['stage'] for r in reqs].count('V1'), 1)
            self.assertNotIn('Put cube', next(r for r in reqs if r['stage'] == 'V1')['prompt'])
            v3 = [r for r in reqs if r['stage'] == 'V3']
            self.assertTrue(all(r['image_hashes'] == v3[0]['image_hashes'] for r in v3))
            self.assertTrue(all(r['images'] for r in v3))
            self.assertFalse(any('beneficial' in r['prompt'] for r in v3))
            self.assertNotIn('changes', next(r for r in reqs if r['arm'] == 'K4' and r['stage'] == 'L2')['prompt'])

    def test_invalid_relation_does_not_erase_independent_completion_fact(self):
        with tempfile.TemporaryDirectory() as td:
            frames=[np.zeros((32,32,3),np.uint8) for _ in range(2)]
            materialize_frames(frames,1000,Path(td))
            answers={'V1':{'initial_context':[],'changes':[],'coverage':'no_observable_change','uncertainty':[]},
                     'L2':'{bad json',
                     'V3':{'facts':[],'change_checks':[],
                           'goal_facts':[{'criterion_id':'g1','value':'false','evidence_refs':['f0001']}],
                           'new_unverified_changes':[],'missing':[]},
                     'L4':{'claim_results':[],'events':[],
                           'state':{'goal_done':'false','direct_ready':'unknown','partial_preparation':'unknown'},
                           'state_fact_ids':{'goal_done':['g1'],'direct_ready':[],'partial_preparation':[]},
                           'net_effect':'unknown','reversal':'unknown','unresolved':['relation_invalid']}}
            out=Pipeline(ScriptedBackend(answers)).run(PrefixPackage(td),'goal',arms=['C4'])
            self.assertFalse(out['arms']['C4']['L2']['validation']['valid'])
            self.assertTrue(out['arms']['C4']['L4']['validation']['valid'])
            self.assertEqual(out['arms']['C4']['L4']['payload']['state']['goal_done'],'false')
            self.assertEqual(out['arms']['C4']['first_failure'],'L2')

    def test_verified_event_gets_host_owned_snapshot(self):
        with tempfile.TemporaryDirectory() as td:
            materialize_frames([np.zeros((32,32,3),np.uint8) for _ in range(2)],1000,Path(td))
            answers={'V1':{'initial_context':[],'changes':[{'change_id':'e1','entity_ids':['o1'],
                'before_refs':['f0000'],'after_refs':['f0001'],'before':'left','after':'right',
                'observation':'observed','status':'closed_event'}],'coverage':'complete','uncertainty':[]},
                'L2':{'claims':[{'claim_id':'h1','change_ids':['e1'],'goal_binding':'target',
                    'relation_hypothesis':'may help','possible_effect':'beneficial','test_ids':['q1'],'falsifier':'not at target'}],
                    'tests':[{'test_id':'q1','neutral_question':'where is object?','entity_ids':['o1'],
                              'requested_refs':['f0001']}]},
                'V3':{'facts':[{'test_id':'q1','at':'after','value':'true','evidence_refs':['f0001'],
                       'visible_statement':'at target'}],'change_checks':[{'change_id':'e1','exists':'true',
                       'evidence_refs':['f0000','f0001']}],'goal_facts':[],
                       'new_unverified_changes':[],'missing':[]},
                'L4':{'claim_results':[{'claim_id':'h1','status':'supported','used_test_ids':['q1'],
                       'short_reason':'verified'}],'events':[{'change_ids':['e1'],'impact':'beneficial',
                       'basis':'inference','fact_ids':['q1@after'],'reversed_event_ids':[]}],
                       'state':{'goal_done':'unknown','direct_ready':'unknown','partial_preparation':'unknown'},
                       'state_fact_ids':{'goal_done':[],'direct_ready':[],'partial_preparation':[]},
                       'net_effect':'beneficial','reversal':'false','unresolved':[]}}
            out=Pipeline(ScriptedBackend(answers)).run(PrefixPackage(td),'goal',arms=['C4'])
            snap=out['arms']['C4']['event_snapshot'][0]
            self.assertEqual(snap['observed_interval_ms'],[0,1000])
            self.assertEqual(snap['confirmed_at_ms'],1000)
            self.assertEqual(snap['fact_ids'],['q1@after'])
            self.assertIn('"fact_id": "q1@after"',out['arms']['C4']['L4']['request']['prompt'])

    def test_strong_control_entries_are_runnable_and_keep_their_information_rights(self):
        with tempfile.TemporaryDirectory() as td:
            materialize_frames([np.zeros((32,32,3),np.uint8)],0,Path(td))
            backend=ScriptedBackend(unknown_answers())
            out=Pipeline(backend).run(PrefixPackage(td),'specific goal',arms=['KPLUS4','D4DIRECT'])
            self.assertEqual(out['calls'],8)
            direct_v1=next(r for r in backend.requests if r['arm']=='D4DIRECT' and r['stage']=='V1')
            self.assertIn('specific goal',direct_v1['prompt'])
            kplus=next(r for r in backend.requests if r['arm']=='KPLUS4' and r['stage']=='L2')
            self.assertIn('OBSERVATIONS',kplus['prompt'])

    def test_v3_discards_v1_interpretive_text(self):
        with tempfile.TemporaryDirectory() as td:
            materialize_frames([np.zeros((32,32,3),np.uint8) for _ in range(2)],1000,Path(td))
            answers=unknown_answers()
            answers['V1']={'initial_context':[], 'changes':[{'change_id':'e1','entity_ids':['o1'],
                'before_refs':['f0000'],'after_refs':['f0001'],'before':'at left','after':'beneficial support established',
                'observation':'uncertain','status':'closed_event'}], 'coverage':'complete','uncertainty':[]}
            backend=ScriptedBackend(answers)
            Pipeline(backend).run(PrefixPackage(td),'goal',arms=['C4'])
            v3=next(r for r in backend.requests if r['stage']=='V3')
            self.assertNotIn('beneficial support established',v3['prompt'])

    def test_model_cannot_cite_an_unshown_legal_prefix_frame(self):
        with tempfile.TemporaryDirectory() as td:
            materialize_frames([np.zeros((32,32,3),np.uint8) for _ in range(15)],14000,Path(td))
            answers=unknown_answers()
            answers['V1']={'initial_context':[], 'changes':[{'change_id':'e1','entity_ids':['o1'],
                'before_refs':['f0001'],'after_refs':['f0014'],'before':'x','after':'y',
                'observation':'observed','status':'closed_event'}], 'coverage':'complete','uncertainty':[]}
            out=Pipeline(ScriptedBackend(answers)).run(PrefixPackage(td),'goal',arms=['C4'])
            self.assertFalse(out['shared_v1']['validation']['valid'])


if __name__ == '__main__':
    unittest.main()

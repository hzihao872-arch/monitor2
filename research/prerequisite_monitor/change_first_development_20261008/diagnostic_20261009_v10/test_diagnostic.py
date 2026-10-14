import json,unittest,tempfile,pathlib
from contracts import validate

class ContractsTest(unittest.TestCase):
    handles={'f0':{'time_ms':0},'f1':{'time_ms':1000},'f2':{'time_ms':2000}}
    def v1(self,b='f0',a='f2'):
        return {'context':'block beside rectangle','changes':[{'b':b,'a':a,'object':'rectangle','before':'left','after':'right'}],'coverage':'complete'}
    def test_accept_valid_short_v1(self):
        self.assertTrue(validate('V1',json.dumps(self.v1()),self.handles)['valid'])
    def test_reject_truncation_and_fake_or_reverse_time(self):
        for s in ['{"changes":',json.dumps(self.v1('f2','f0')),json.dumps(self.v1('fake','f2'))]:
            self.assertFalse(validate('V1',s,self.handles)['valid'])
    def test_goal_done_and_mixed_can_coexist(self):
        obj={'state':{'goal_done':'true','direct_ready':'not_applicable','partial_preparation':'not_applicable'},'impacts':[{'change':0,'effect':'harmful'}],'net_effect':'mixed','reversal':'false','reason':'another change damages a separate relation'}
        self.assertTrue(validate('FINAL',json.dumps(obj),self.handles,1)['valid'])
    def test_negation_is_a_semantic_audit_not_silently_flipped(self):
        obj={'facts':[{'test':0,'value':'false','ref':'f2','statement':'exact predicate is unsupported'}]}
        self.assertTrue(validate('VERIFY',json.dumps(obj),self.handles,1,1)['valid'])
    def test_resume_cannot_reset_budget_or_deadline(self):
        from diagnostic_runner import freeze_window
        with tempfile.TemporaryDirectory() as d:
            freeze_window(d,{'max_requests':80,'deadline_epoch':123})
            for w in ({'max_requests':81,'deadline_epoch':123},{'max_requests':80,'deadline_epoch':124}):
                with self.assertRaisesRegex(ValueError,'window/budget'):freeze_window(d,w)

if __name__=='__main__':unittest.main()

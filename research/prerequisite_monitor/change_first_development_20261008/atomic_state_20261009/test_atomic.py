import unittest
import atomic_runner as A

class AtomicTests(unittest.TestCase):
    def test_future_is_rejected(self):
        with self.assertRaises(ValueError):
            A.check_times([{'time_ms':8000}],7000)
    def test_exact_output_contract(self):
        self.assertTrue(A.validate_answer('Unknown')['valid'])
        self.assertFalse(A.validate_answer('True because open')['valid'])
        self.assertFalse(A.validate_answer('{"value":true}')['valid'])
    def test_budget_keeps_parent_and_failed_issued(self):
        with self.assertRaises(RuntimeError): A.check_budget(50,30,1,100,200)
        with self.assertRaises(RuntimeError): A.check_budget(51,0,1,100,200)
        with self.assertRaises(RuntimeError): A.check_budget(50,0,2,199,200)
        A.check_budget(50,24,6,100,400)
    def test_logits_unknown_and_numerics(self):
        x=A.read_logits({'True':-8.,'False':-9.,'Unknown':-1.})
        self.assertEqual(x['value'],'Unknown')
        self.assertAlmostEqual(sum(x['conditional_three_way'].values()),1.)
    def test_causal_sampling(self):
        rows=[{'evidence_id':f'f{i:04d}','time_ms':i*1000} for i in range(15)]
        self.assertEqual(A.causal_ids(rows,7000)[-1],'f0007')
        self.assertEqual(A.causal_ids(rows,0),['f0000'])
        self.assertNotIn('f0014',A.causal_ids(rows,7000))

if __name__=='__main__': unittest.main()

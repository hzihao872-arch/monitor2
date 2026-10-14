import unittest
from sampling_runner import subset,causal_ids
class Test(unittest.TestCase):
 def test_legal_endpoint(self):
  ids=[f'f{i:04d}' for i in range(15)];self.assertEqual(subset(ids,2),[ids[0],ids[-1]]);self.assertEqual(subset(ids,8),ids[::2]);self.assertEqual(len(set(subset(ids,8))),8)
 def test_future(self):self.assertEqual(causal_ids([{'evidence_id':'a','time_ms':0},{'evidence_id':'b','time_ms':15000}],14000),['a'])
if __name__=='__main__':unittest.main()

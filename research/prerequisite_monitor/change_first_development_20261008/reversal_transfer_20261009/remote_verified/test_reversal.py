import unittest
from reversal_runner import select,causal_ids
class Test(unittest.TestCase):
 def test_past_only(self):
  frames=[{'time_ms':i*1000,'evidence_id':str(i)} for i in range(15)];ids=causal_ids(frames,7000);self.assertEqual(select(ids,'prefix8'),[str(i) for i in range(8)]);self.assertEqual(select(ids,'current'),['7'])
 def test_retain_endpoint(self):self.assertEqual(select([str(i) for i in range(15)],'prefix8')[-1],'14')
if __name__=='__main__':unittest.main()

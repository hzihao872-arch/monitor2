import unittest
from fact_runner import derive,subset
class Test(unittest.TestCase):
 def test_verbatim_automatic(self):
  c={'b':'f0','a':'f2','object':'box','before':'covered','after':'open'};r=derive('q',{'changes':[c]});self.assertEqual(len(r),2);self.assertEqual([x['condition'] for x in r],['covered','open']);self.assertEqual([x['ref'] for x in r],['f0','f2'])
 def test_past_endpoint(self):
  ids=[str(i) for i in range(15)];r=subset(ids);self.assertEqual(len(r),8);self.assertEqual(r[-1],'14');self.assertEqual(subset(ids[:2]),ids[:2])
if __name__=='__main__':unittest.main()

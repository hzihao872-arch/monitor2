import unittest
from experiments.local_stronger_20261003 import accept_response
GOOD='{"memory":"Green and blue are separate.","judgments":[{"object_id":"green_on_blue","H":"-","C":"-","P":"?","G":"-","evidence_time":0}]}'
class LocalStrongerTest(unittest.TestCase):
 def test_invalid_raw_keeps_previous_summary(self):
  r=accept_response(GOOD+'}',1,'previous',400,90)
  self.assertEqual(r['memory'],'previous');self.assertEqual(r['parse_status'],'invalid_json')
 def test_over_budget_response_cannot_advance_memory(self):
  r=accept_response(GOOD,1,'previous',4097,90)
  self.assertEqual(r['memory'],'previous');self.assertEqual(r['budget_reason'],'input_tokens')
 def test_valid_summary_advances_without_rewriting(self):
  self.assertEqual(accept_response(GOOD,1,'previous',400,90)['memory'],'Green and blue are separate.')
 def test_future_evidence_cannot_advance_memory(self):
  r=accept_response(GOOD.replace('"evidence_time":0','"evidence_time":3'),1,'previous',400,90)
  self.assertEqual(r['memory'],'previous');self.assertNotEqual(r['parse_status'],'valid')
if __name__=='__main__':unittest.main()

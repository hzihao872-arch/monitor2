import unittest
from experiments.summary_isolation_20261003 import inspect_output
class IsolationTest(unittest.TestCase):
 def test_summary_only_rejects_other_fields(self):
  self.assertFalse(inspect_output('{"memory":"Cubes are separated.","judgments":[]}', 'json',0,15)['format_valid'])
 def test_truncated_and_extra_brace_are_not_salvaged(self):
  for raw in ['{"memory":"cube','{"memory":"Cubes separated."}}']:
   self.assertFalse(inspect_output(raw,'json',0,20)['format_valid'])
 def test_cap_or_repeated_summary_is_not_usable(self):
  self.assertFalse(inspect_output('Cubes are separated.','text',0,256)['summary_usable_syntax'])
  self.assertFalse(inspect_output('The green cube is on blue. '*4,'text',0,40)['summary_usable_syntax'])
 def test_joint_rejects_future_evidence(self):
  raw='{"memory":"Cubes are separated.","judgments":[{"object_id":"green_on_blue","H":"-","C":"-","P":"?","G":"-","evidence_time":3}]}'
  self.assertFalse(inspect_output(raw,'joint',2,80)['format_valid'])
 def test_short_plain_and_json_summary_are_usable(self):
  for mode,raw in [('text','Cubes are separated.'),('json','{"memory":"Cubes are separated."}')]:
   self.assertTrue(inspect_output(raw,mode,0,12)['summary_usable_syntax'])
if __name__=='__main__':unittest.main()

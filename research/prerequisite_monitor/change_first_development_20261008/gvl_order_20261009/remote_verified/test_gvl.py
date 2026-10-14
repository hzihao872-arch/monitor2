import json,unittest
from gvl_runner import validate
class Test(unittest.TestCase):
 def test_unrepaired_values(self):
  r=[{'frame_number':i,'frame_description':'x','task_completion_percentage':0} for i in range(1,6)];self.assertTrue(validate(json.dumps(r))['valid']);r[0]['task_completion_percentage']=True;self.assertFalse(validate(json.dumps(r))['valid'])
 def test_duplicates(self):
  r=[{'frame_number':1,'frame_description':'x','task_completion_percentage':0} for _ in range(5)];self.assertFalse(validate(json.dumps(r))['valid'])
if __name__=='__main__':unittest.main()

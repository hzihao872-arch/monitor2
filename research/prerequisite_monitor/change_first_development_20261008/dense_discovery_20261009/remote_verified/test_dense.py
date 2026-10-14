import unittest,json
from contracts import validate
class Test(unittest.TestCase):
 def test_future_reference_rejected(self):
  obj={'context':'x','changes':[{'b':'f0','a':'future','object':'x','before':'x','after':'y'}],'coverage':'complete'};self.assertFalse(validate('V1',json.dumps(obj),{'f0':{'time_ms':0}})['valid'])
 def test_unrepaired_contract(self):self.assertFalse(validate('V1','{"context":"x","changes":[],"coverage":"complete","extra":1}',{})['valid'])
if __name__=='__main__':unittest.main()

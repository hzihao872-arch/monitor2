import unittest
from prefix_runner import last_forms
class Fake:
 def encode(self,text,add_special_tokens=False):return [1,{'True':2,'False':3,'Unknown':4}[text.split()[-1]]]
class Test(unittest.TestCase):
 def test_shared_prefix_last_label(self):self.assertEqual(last_forms(Fake(),'The answer is: '),{'True':2,'False':3,'Unknown':4})
if __name__=='__main__':unittest.main()

import unittest
import choice_runner as C
class Tests(unittest.TestCase):
 def test_swapped_answer_is_same_state(self):
  self.assertEqual(C.state_from_choice('A','positive_first'),'True')
  self.assertEqual(C.state_from_choice('B','opposed_first'),'True')
  self.assertEqual(C.state_from_choice('Unknown','positive_first'),'Unknown')
 def test_order_only_changes_statement_order(self):
  a=C.options('p','q','positive_first');b=C.options('p','q','opposed_first')
  self.assertEqual(a,{'A':'p','B':'q'});self.assertEqual(b,{'A':'q','B':'p'})
if __name__=='__main__':unittest.main()

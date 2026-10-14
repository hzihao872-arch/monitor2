import unittest
from inventory_runner import validate_inventory,check_object_ids
class Test(unittest.TestCase):
 def test_cycle_and_unknown(self):
  import json
  x={'objects':[{'id':'o0','description':'part','part_of':'unknown','visible_state':'touching orange surface'}],'coverage':'unknown'};self.assertTrue(validate_inventory(json.dumps(x))['valid']);x['objects'][0]['part_of']='o0';self.assertFalse(validate_inventory(json.dumps(x))['valid'])
 def test_unregistered_change(self):
  self.assertEqual(check_object_ids({'changes':[{'object':'ghost'}]},{'o0'}),['unknown_object_id'])
if __name__=='__main__':unittest.main()

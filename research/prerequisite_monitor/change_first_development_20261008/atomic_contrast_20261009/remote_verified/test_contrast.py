import unittest
import contrast_runner as C
class Tests(unittest.TestCase):
    def test_raw_truncates_only_known_eos(self):
        self.assertEqual(C.raw_text('user body<END>assistant','<END>'),'user body')
        self.assertEqual(C.raw_text('user body',None),'user body')
    def test_complement_never_changes_pixels(self):
        self.assertEqual(C.opposition('opening'),'The orange panel covers the rectangular top opening of the box.')
    def test_all_alias_mass_is_kept(self):
        p=C.alias_readout({'True':[-10.,-1.],'False':[-2.,-3.],'Unknown':[-8.,-9.]})
        self.assertEqual(p['alias_argmax'],'True')
        self.assertEqual(p['bare_argmax'],'False')
if __name__=='__main__':unittest.main()

"""Registration must carry hand preservation and exact-reference contracts."""
import unittest
from library_exercises import LIBRARY_EXERCISES,LIBRARY_MUSCLES
from motion_reference_gate import load_reference
from library_gate import validator_hashes

class Batch008Tests(unittest.TestCase):
    def test_variant_contracts(self):
        for n,ident,grip in [('standing_supinated_curl','0416','supinated'),('bilateral_reverse_curl','0382','pronated')]:
            with self.subTest(n=n):
                c=LIBRARY_EXERCISES[n]
                self.assertEqual((c['id'],c['grip'],c['batch'],c['audit_version']),(ident,grip,'008',8))
                self.assertEqual(c['contact_recipe'],'preserve_thickness')
                self.assertFalse(c.get('alternating') or c.get('unilateral') or c.get('seated'))
                self.assertIn('biceps_brachii',LIBRARY_MUSCLES[n])
    def test_exact_references_and_checkers(self):
        for n in ['standing_supinated_curl','bilateral_reverse_curl']:
            ref,_=load_reference(n)
            self.assertEqual(ref['variant']['loadedSides'],['Left','Right'])
            self.assertIn('library_audit_v8.py',validator_hashes(n))

if __name__=='__main__':unittest.main()

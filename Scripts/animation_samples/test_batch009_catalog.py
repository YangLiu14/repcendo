"""Exact seated variants must retain the shared contact and reference contract."""
import unittest
from library_exercises import LIBRARY_EXERCISES,LIBRARY_MUSCLES
from motion_reference_gate import load_reference
from library_gate import validator_hashes

class Batch009Tests(unittest.TestCase):
    def test_variant_contracts(self):
        for n,ident in [('seated_supinated_curl','0391'),('concentration_curl','0297')]:
            with self.subTest(n=n):
                c=LIBRARY_EXERCISES[n]
                self.assertEqual((c['id'],c['grip'],c['batch'],c['audit_version']),(ident,'supinated','009',9))
                self.assertEqual(c['contact_recipe'],'preserve_thickness')
                self.assertTrue(c['seated']);self.assertFalse(c.get('alternating'))
                self.assertIn('biceps_brachii',LIBRARY_MUSCLES[n])
        self.assertEqual(LIBRARY_EXERCISES['concentration_curl']['unilateral'],'Left')
        self.assertTrue(LIBRARY_EXERCISES['concentration_curl']['thigh_support'])
    def test_exact_references_and_checkers(self):
        for n,sides in [('seated_supinated_curl',['Left','Right']),('concentration_curl',['Left'])]:
            ref,_=load_reference(n)
            self.assertEqual(ref['variant']['loadedSides'],sides)
            self.assertEqual(ref['variant']['posture'],'seated')
            self.assertIn('library_audit_v9.py',validator_hashes(n))
if __name__=='__main__':unittest.main()

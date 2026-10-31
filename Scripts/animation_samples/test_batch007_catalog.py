"""New registered motions must inherit the production grip recipe and overlay."""
import unittest
from library_exercises import LIBRARY_EXERCISES,LIBRARY_MUSCLES
class Batch007CatalogTests(unittest.TestCase):
 def test_new_motions_inherit_contact_recipe(self):
  for n,c in LIBRARY_EXERCISES.items():
   if c['batch']=='007':
    with self.subTest(n=n):self.assertEqual(c.get('contact_recipe'),'preserve_thickness')
 def test_new_motions_have_correct_overlay(self):
  self.assertEqual(LIBRARY_MUSCLES['standing_alternate_kickback'],['triceps_brachii'])
  self.assertIn('biceps_brachii',LIBRARY_MUSCLES['seated_single_hammer_curl'])

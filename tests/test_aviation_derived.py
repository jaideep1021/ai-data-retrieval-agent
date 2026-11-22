import unittest
from derive_aviation_candidates import other_seats,distance_candidates
class DerivedTests(unittest.TestCase):
 def test_missing_other_is_not_zero(self):self.assertEqual(other_seats({'a':1,'b':None,'c':2},'a'),(None,1))
 def test_missing_own_does_not_block_others(self):self.assertEqual(other_seats({'a':None,'b':0,'c':2},'a'),(2,0))
 def test_unknown_country(self):
  with self.assertRaises(ValueError):other_seats({'a':1},'b')
 def test_empty_distance(self):self.assertEqual(distance_candidates([]),{})
 def test_weighting_and_zero_weights(self):
  rows=[{'DISTANCE':d,'ORIGIN_AIRPORT_ID':1,'DEST_AIRPORT_ID':2,'SEATS':s,'PASSENGERS':0,'DEPARTURES_PERFORMED':1} for d,s in [(100,1),(200,3)]]
  v=distance_candidates(rows);self.assertEqual(v['row_mean'],150);self.assertEqual(v['seats_weighted'],175);self.assertIsNone(v['passengers_weighted'])

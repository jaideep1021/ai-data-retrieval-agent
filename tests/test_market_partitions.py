import unittest
from market_partitions import matching_partitions
class PartitionTests(unittest.TestCase):
 def test_unique_requires_both_counts_and_seats(self):
  self.assertEqual(matching_partitions({'a':[2,100],'b':[2,200]},2,100),[{'a':1,'b':0}])
 def test_ambiguity_retained(self):
  self.assertEqual(len(matching_partitions({'a':[1,0],'b':[1,0]},1,0)),2)
 def test_no_solution_not_guessed(self):
  self.assertEqual(matching_partitions({'a':[1,20]},1,30),[])
 def test_bound(self):
  with self.assertRaises(ValueError):matching_partitions({str(i):[1,0] for i in range(19)},1,0)

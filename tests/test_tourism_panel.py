import unittest
from review_tourism_panel import quarterly
class TourismTests(unittest.TestCase):
    def test_missing_no_carry(self):
        rows=quarterly({('Kenya',2020,'ST.INT.ARVL'):0},['Kenya'])
        self.assertEqual(len(rows),26)
        self.assertEqual([r['Tourism_T'] for r in rows[:4]],[0]*4)
        self.assertIsNone(rows[4]['Tourism_T'])
        self.assertEqual((rows[-1]['year'],rows[-1]['quarter']),(2026,2))
    def test_percent_not_divided(self):
        rows=quarterly({('Kenya',2020,'ST.INT.RCPT.XP.ZS'):15.5},['Kenya'])
        self.assertEqual([r['Tourism_P'] for r in rows[:4]],[15.5]*4)

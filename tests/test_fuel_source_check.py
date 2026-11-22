import unittest
from decimal import Decimal
from fuel_source_check import parse,mean_complete
class FuelTests(unittest.TestCase):
    def test_missing_month_not_averaged(self):
        self.assertIsNone(mean_complete([Decimal(1),None,Decimal(3)]))
    def test_price_mean_not_sum(self):
        self.assertEqual(mean_complete([Decimal(1),Decimal(2),Decimal(3)]),Decimal(2))
    def test_empty_page(self):
        with self.assertRaises(ValueError):parse('<html>Error</html>','eia')
    def test_eia_cutoff(self):
        text='<tr><td>2026</td>'+''.join('<td>1.5</td>' for _ in range(12))+'</tr>'
        self.assertEqual(len(parse(text,'eia')),6)
    def test_duplicate_rejected(self):
        text='<tr><td>2015</td>'+''.join('<td>1.5</td>' for _ in range(12))+'</tr>'
        with self.assertRaises(ValueError):parse(text+text,'eia')
    def test_schema_change(self):
        with self.assertRaises(ValueError):parse('<tr><td>2015</td><td>1</td></tr>','eia')

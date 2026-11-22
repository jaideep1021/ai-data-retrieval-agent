import unittest
from compare_bts_reference import compare

class ReferenceComparisonTests(unittest.TestCase):
    def reference(self, seats=10, passengers=8):
        return [dict(country='Kenya',code='KE',year=2015,quarter=1,excel_row=2,
                     seats=seats,passengers=passengers,CountAirline=2,distance=100)]
    def row(self, service='F', airline='1'):
        return dict(CLASS=service,SEATS='10',PASSENGERS='8',AIRLINE_ID=airline,
                    DEPARTURES_PERFORMED='1',MONTH='1',DISTANCE='100')
    def test_exact_and_unresolved_count(self):
        r=compare(self.reference(),{('KE',2015,1):[self.row()]})[0]
        self.assertEqual(r['status_seats'],'EXACT_MATCH')
        self.assertEqual(r['F_distinct_operating_airlines'],1)
        self.assertEqual(r['reference_CountAirline'],2)
    def test_non_scheduled_diagnostic_does_not_replace_primary(self):
        r=compare(self.reference(),{('KE',2015,1):[self.row('L')]})[0]
        self.assertEqual(r['status_seats'],'NO_F_ROWS_REFERENCE_NONZERO')
        self.assertEqual(r['all_classes_seats'],'10')
        self.assertIsNone(r['F_seats'])
    def test_absence_not_imputed_zero(self):
        r=compare(self.reference(0,0),{})[0]
        self.assertEqual(r['status_seats'],'NO_F_ROWS_REFERENCE_ZERO')
        self.assertIsNone(r['F_seats'])
    def test_diagnostic_product_separate_from_unique_count(self):
        r=compare(self.reference(20,16),{('KE',2015,1):[self.row(airline='1'),self.row(airline='2')]})[0]
        self.assertEqual(r['all_classes_distinct_airlines'],2)
        self.assertEqual(r['diagnostic_rows_times_distinct'],4)

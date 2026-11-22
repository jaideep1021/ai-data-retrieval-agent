import unittest
from bts_quarterly_preview import preview, numeric

def record(month, origin='US', dest='KE', **changes):
    row=dict(YEAR='2020',MONTH=str(month),CLASS='F',ORIGIN_COUNTRY=origin,DEST_COUNTRY=dest,
             UNIQUE_CARRIER_ENTITY='1',AIRLINE_ID='1',ORIGIN_AIRPORT_ID=origin,
             DEST_AIRPORT_ID=dest,AIRCRAFT_TYPE='1',AIRCRAFT_CONFIG='1',ORIGIN=origin,DEST=dest,
             SEATS='10',PASSENGERS='8',DEPARTURES_SCHEDULED='1',DEPARTURES_PERFORMED='1',
             FREIGHT='0',MAIL='0',DISTANCE='100')
    row.update(changes)
    return 2020,month,row

class PreviewTests(unittest.TestCase):
    def test_directions_and_carrier_union(self):
        data=[record(m,o,d) for m in (1,2,3) for o,d in [('US','KE'),('KE','US')]]
        rows,lineage,audit=preview(data,['KE'],2020,2020,3)
        self.assertEqual(rows[0]['provisional_SEATS'],'60')
        self.assertEqual(rows[0]['provisional_CountAirline'],1)
        self.assertEqual(len(lineage),6)
        self.assertFalse(rows[0]['reference_validated'])

    def test_missing_months_absent_country_and_observed_zero(self):
        rows,_,_=preview([record(1,SEATS='0')],['KE','NG'],2020,2020,3)
        self.assertEqual(rows[0]['observed_SEATS'],'0')
        self.assertIsNone(rows[0]['provisional_SEATS'])
        self.assertIsNone(rows[1]['observed_SEATS'])
        self.assertEqual(rows[1]['status'],'NO_SELECTED_RECORDS')

    def test_cutoff_and_class(self):
        rows,_,audit=preview([record(4),record(1,CLASS='G')],['KE'],2020,2020,3)
        self.assertEqual(audit['after_cutoff_rows'],1)
        self.assertEqual(audit['selected_rows'],0)

    def test_duplicate_and_invalid_values(self):
        with self.assertRaises(ValueError): preview([record(1),record(1)],['KE'],2020,2020,3)
        for value in ('','NaN','-1','Infinity'):
            with self.assertRaises(ValueError): numeric(value)

    def test_invalid_config_and_snapshot(self):
        with self.assertRaises(ValueError): preview([],['US'])
        with self.assertRaises(ValueError): preview([],['KE','KE'])
        with self.assertRaises(ValueError): preview([record(1,YEAR='2019')],['KE'])

    def test_suspicious_values_flagged_not_silently_corrected(self):
        _,_,audit=preview([record(1,PASSENGERS='11.5')],['KE'],2020,2020,3)
        self.assertEqual(audit['passengers_above_seats_rows'],1)
        self.assertEqual(audit['noninteger_count_rows'],1)

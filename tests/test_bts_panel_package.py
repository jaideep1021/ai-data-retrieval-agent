import unittest
from build_bts_panel_package import split_periods, compare_view, retain_counts
from bts_quarterly_preview import preview
from test_bts_quarterly_preview import record

class PackageTests(unittest.TestCase):
    def test_full_grid_split(self):
        codes=['AO','CV','CI','EG','ET','GH','KE','MA','NG','RW','SN','ZA','TG','ZW']
        rows,_,_=preview([],codes)
        a,b=split_periods(rows)
        self.assertEqual((len(rows),len(a),len(b)),(644,280,364))
        self.assertTrue(all(r['observed_SEATS'] is None for r in rows))
    def test_variants_are_separate(self):
        records=[record(1),record(2,CLASS='L'),record(3,CLASS='G')]
        f,_,_=preview(records,['KE'],2020,2020,3)
        allrows,lineage,_=preview(records,['KE'],2020,2020,3,service_classes=('F','G','L','P'))
        self.assertEqual(f[0]['observed_SEATS'],'10')
        self.assertIsNone(f[0]['provisional_SEATS'])
        self.assertEqual(allrows[0]['provisional_SEATS'],'30')
        self.assertEqual({r['service_class'] for r in lineage},{'F','G','L'})
    def test_unknown_class_selection_and_cutoff(self):
        with self.assertRaises(ValueError):preview([],['KE'],service_classes=('Z',))
        with self.assertRaises(ValueError):split_periods([{'year':2026,'quarter':3}])
    def test_reference_absence_and_count_remain_unresolved(self):
        rows,_,_=preview([],['KE'],2015,2015,3)
        refs=[{'country':'Kenya','code':'KE','year':'2015','quarter':'1','reference_seats':'0','reference_passengers':'0','reference_CountAirline':'0'}]
        result=compare_view(rows,refs)[0]
        self.assertEqual(result['status_seats'],'NO_ROWS_REFERENCE_ZERO')
        self.assertIsNone(result['observed_seats'])
        self.assertIsNone(result['approved_CountAirline'])

    def test_count_units_are_not_conflated(self):
        row={'observed_distinct_reported_airlines':7,
             'observed_distinct_operating_airlines':6,
             'source_rows':28,'diagnostic_rows_times_reported_airlines':196}
        result=retain_counts(row)
        self.assertEqual(result['DistinctAirlineCount'],7)
        self.assertEqual(result['OperatingAirlineCount'],6)
        self.assertEqual(result['SourceRecordCount'],28)
        self.assertEqual(result['HistoricalCountProductDiagnostic'],196)

    def test_no_records_is_not_claimed_zero_airlines(self):
        rows,_,_=preview([],['KE'],2015,2015,3)
        row=retain_counts(rows[0])
        self.assertEqual(row['SourceRecordCount'],0)
        self.assertIsNone(row['DistinctAirlineCount'])
        self.assertIsNone(row['OperatingAirlineCount'])

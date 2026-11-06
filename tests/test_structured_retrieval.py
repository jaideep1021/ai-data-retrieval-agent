"""Structured retrieval and authority checks never consume reference values."""
import copy
import unittest
from structured_retrieval import authority, context_valid, dataset_location, row_query, valid_schema, verify
from tests.test_business_agent import TASK


class StructuredTests(unittest.TestCase):
    def setUp(self):
        self.meta={'name':'City-pair market records','provenance':'official',
                   'attribution':'Department of Transportation example office',
                   'attributionLink':'https://www.transportation.gov/example',
                   'columns':[{'fieldName':k,'description':v} for k,v in {
                       'year':'Year','quarter':'Quarter','citymarketid_1':'City market ID',
                       'citymarketid_2':'City market ID','city1':'City','city2':'City',
                       'fare':'Overall average fare','passengers':'Passenger per day','nsmiles':'Nonstop miles'}.items()]}
        self.row={'year':'2024','quarter':'4','citymarketid_1':'30001','citymarketid_2':'30002','fare':'123.45'}

    def test_discovery_does_not_require_specific_identifier(self):
        self.assertEqual(dataset_location('https://example.org/Aviation/name/abcd-1234/about_data'),('example.org','abcd-1234'))
        self.assertIsNone(dataset_location('https://example.org/not-a-dataset'))
        self.assertIsNone(dataset_location('https://user:pass@example.org/abcd-1234'))

    def test_query_uses_only_identifiers_not_questionable_value(self):
        a=row_query(TASK);b=row_query({**TASK,'current_value':'secret-oracle-value'})
        self.assertEqual(a,b)
        self.assertNotIn('secret',str(b));self.assertEqual(a['$limit'],2)
        with self.assertRaises(ValueError):row_query({**TASK,'citymarketid_1':'1 OR 1=1'})

    def test_period_market_and_decimal_failures(self):
        self.assertTrue(context_valid(self.row,TASK))
        for update in [{'quarter':'3'},{'citymarketid_2':'99999'},{'fare':'NaN'}]:
            self.assertFalse(context_valid({**self.row,**update},TASK))

    def test_publisher_claim_or_gov_suffix_alone_insufficient(self):
        self.assertEqual(authority(self.meta,'datahub.transportation.gov')['classification'],'ORIGINAL_PUBLISHER')
        self.assertNotEqual(authority(self.meta,'unrelated.gov')['classification'],'ORIGINAL_PUBLISHER')
        for update in [{'provenance':'community'},{'attribution':''},{'attributionLink':'https://evil.example'}]:
            self.assertNotEqual(authority({**self.meta,**update},'datahub.transportation.gov')['classification'],'ORIGINAL_PUBLISHER')

    def test_airport_and_incomplete_schema_rejected(self):
        self.assertTrue(valid_schema(self.meta))
        self.assertFalse(valid_schema({**self.meta,'name':'All Airport Pair Markets'}))
        self.assertFalse(valid_schema({**self.meta,'columns':[]}))

    def test_authority_policy_compared_on_same_duplicate_evidence(self):
        s={'context_match':True,'value':'123.45','row_sha256':'same',
           'authority':{'classification':'ORIGINAL_PUBLISHER'}}
        result=verify([s,copy.deepcopy(s)])
        self.assertEqual(result['agreement_policy'],'DUPLICATE_EVIDENCE')
        self.assertEqual(result['authority_policy'],'ACCEPT_AUTHORITATIVE_RECORD')
        self.assertEqual(result['independence'],'NOT_ESTABLISHED')
        self.assertEqual(verify([s,{**s,'value':'124'}])['authority_policy'],'CONFLICT')
        self.assertEqual(verify([{**s,'authority':{'classification':'UNCONFIRMED_OR_SECONDARY'}}])['authority_policy'],'UNRESOLVED')

class StructuredIntegrationTests(unittest.TestCase):
    def test_discovery_schema_query_and_authority_end_to_end(self):
        import json
        from pathlib import Path
        import tempfile
        from unittest.mock import Mock,patch
        from structured_retrieval import run
        fixture=StructuredTests();fixture.setUp()
        metadata=fixture.meta
        row={**fixture.row,'city1':TASK['city1'],'city2':TASK['city2'],'passengers':'10.25','nsmiles':'500'}
        fetcher=Mock(policy_events=[])
        calls=[]
        def read(url,check_robots=True):
            calls.append(url)
            self.assertFalse(check_robots) # documented API client, not webpage crawler
            if '/catalog/' in url:
                payload={'results':[{'link':'https://datahub.transportation.gov/Aviation/example/abcd-1234','resource':{'name':'City-pair markets'}}]}
            elif '/api/views/' in url:payload=metadata
            elif '/resource/' in url:payload=[row]
            else:raise AssertionError('Unexpected endpoint')
            return 200,'application/json',json.dumps(payload),url
        fetcher.read.side_effect=read
        with tempfile.TemporaryDirectory() as folder,patch('structured_retrieval.time.sleep'):
            result=run(TASK,'socrata',Path(folder)/'trial',fetcher)
            self.assertEqual(result['decision'],'ACCEPT_AUTHORITATIVE_RECORD')
            self.assertEqual(result['accepted_value'],'123.45')
            self.assertEqual(result['agreement_policy'],'INSUFFICIENT_EVIDENCE')
            self.assertFalse(result['reference_used'])
            self.assertEqual(len(result['requests']),3)
            self.assertTrue(all((Path(folder)/'trial'/r['evidence_file']).exists() for r in result['requests']))
        self.assertNotIn('123.45',' '.join(calls))
        self.assertIn('abcd-1234',calls[1])

    def test_api_quota_stops_batch(self):
        from pathlib import Path
        import tempfile
        from unittest.mock import Mock,patch
        from structured_retrieval import run
        fetcher=Mock(policy_events=[])
        fetcher.read.return_value=(429,'application/json','{}','https://api.us.socrata.com/api/catalog/v1')
        with tempfile.TemporaryDirectory() as folder,patch('structured_retrieval.time.sleep'):
            result=run(TASK,'socrata',Path(folder)/'trial',fetcher)
        self.assertTrue(result['stop_batch']);self.assertEqual(result['decision'],'ERROR')
        self.assertEqual(fetcher.read.call_count,1)


if __name__=='__main__':unittest.main()

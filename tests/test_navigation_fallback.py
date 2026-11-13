import unittest
from aviation_selection import navigation_fallback

class NavigationFallbackTests(unittest.TestCase):
    def test_queue_navigation_and_deprioritize_service_failure(self):
        c=[{'url':'https://a.example/new'},{'url':'https://b.example/nav'}]
        a=[{'index':1,'role':'official_navigation'}]
        r=navigation_fallback(c,[0],a,[{'url':'https://a.example/old','reason':'SERVICE_ERROR_PAGE'}])
        self.assertEqual(r['indices'],[1,0])
    def test_robots_origin_deferred_not_entire_domain(self):
        c=[{'url':'https://a.example/new'},{'url':'https://sub.a.example/nav'}]
        r=navigation_fallback(c,[0,1],[],[{'url':'https://a.example/old','reason':'ROBOTS_UNAVAILABLE_OR_DENIED'}])
        self.assertEqual(r['indices'],[1]);self.assertEqual(r['deferred_access_indices'],[0])
    def test_parser_failure_does_not_downrank_host_and_no_retries(self):
        c=[{'url':'https://a.example/new'},{'url':'https://a.example/old'}]
        r=navigation_fallback(c,[0,1],[],[{'url':'https://a.example/old','reason':'PDF_HAS_NO_EXTRACTABLE_TEXT'}])
        self.assertEqual(r['indices'],[0])
    def test_unrelated_not_added(self):
        self.assertEqual(navigation_fallback([{'url':'https://a.example'}],[],[{'index':0,'role':'unrelated'}],[])['indices'],[])

    def test_bilateral_scope_cues_exclude_generic_and_domestic_navigation(self):
        c=[{'url':'https://example.org/notices','title':'Notices','snippet':'Domestic air service licence'},
           {'url':'https://example.org/agreements','title':'Air Service Agreements'},
           {'url':'https://example.org/database','title':"Database of World’s Air Services Agreements"}]
        a=[{'index':i,'role':'official_navigation'} for i in range(3)]
        r=navigation_fallback(c,[0],a,[],task={'topic':'us_bilateral_air_services'})
        self.assertEqual(r['indices'],[1,2])
        self.assertEqual(r['navigation_without_scope_cue'],[0])

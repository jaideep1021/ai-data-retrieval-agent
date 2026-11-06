"""Search adapters: discovery only; snippets are never verification evidence."""
import requests


class SearchServiceError(ValueError):
    """Safe status metadata lets batch runners stop on auth/quota failures."""
    def __init__(self, status=None):
        super().__init__('Search provider reported an error')
        self.status = status


# EXPLAIN: Define the structured fields accepted from the model; unexpected fields are rejected.
class SearchProvider:
    # EXPLAIN: Initialize this helper and store the dependencies supplied by its caller; this makes offline testing possible.
    def __init__(self, name, client=None, key=None):
        if name not in ('serpapi', 'brave'):
            raise ValueError('Unknown provider')
        if name == 'serpapi' and client is None:
            raise ValueError('SerpApi client required')
        if name == 'brave' and not key:
            raise ValueError('Brave key required')
        self.name, self.client, self.key = name, client, key

    # EXPLAIN: Call the configured search service and return discovery results. Search snippets are not verification evidence.
    def search(self, query):
        if self.name == 'serpapi':
            payload = self.client.search(engine='google', q=query, num=10)
            if 'error' in payload:
                # The SDK may return errors without an HTTP status. Fail closed:
                # the Week 3 runner stops instead of repeatedly spending quota.
                raise SearchServiceError()
            rows = payload.get('organic_results', [])
            url_field, snippet_field = 'link', 'snippet'
        else:
            # Fixed API endpoint; never forward credentials to discovered pages or redirects.
            with requests.get('https://api.search.brave.com/res/v1/web/search',
                              headers={'X-Subscription-Token': self.key, 'Accept': 'application/json'},
                              params={'q': query, 'count': 10}, timeout=(10, 25),
                              allow_redirects=False) as response:
                if response.status_code != 200:
                    raise SearchServiceError(response.status_code)
                payload = response.json()
            rows = payload.get('web', {}).get('results', [])
            url_field, snippet_field = 'url', 'description'
        if not isinstance(rows, list):
            raise ValueError('Invalid search result format')
        results = []
        for row in rows[:10]:
            if isinstance(row, dict) and isinstance(row.get(url_field), str):
                results.append({'url': row[url_field], 'title': str(row.get('title', ''))[:500],
                                'snippet': str(row.get(snippet_field, ''))[:1500]})
        return results

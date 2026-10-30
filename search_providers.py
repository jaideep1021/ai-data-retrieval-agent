"""Search adapters: discovery only; snippets are never verification evidence."""
import requests


class SearchProvider:
    def __init__(self, name, client=None, key=None):
        if name not in ('serpapi', 'brave'):
            raise ValueError('Unknown provider')
        if name == 'serpapi' and client is None:
            raise ValueError('SerpApi client required')
        if name == 'brave' and not key:
            raise ValueError('Brave key required')
        self.name, self.client, self.key = name, client, key

    def search(self, query):
        if self.name == 'serpapi':
            payload = self.client.search(engine='google', q=query, num=10)
            if 'error' in payload:
                raise ValueError('Search provider reported an error')
            rows = payload.get('organic_results', [])
            url_field, snippet_field = 'link', 'snippet'
        else:
            # Fixed API endpoint; never forward credentials to discovered pages or redirects.
            with requests.get('https://api.search.brave.com/res/v1/web/search',
                              headers={'X-Subscription-Token': self.key, 'Accept': 'application/json'},
                              params={'q': query, 'count': 10}, timeout=(10, 25),
                              allow_redirects=False) as response:
                if response.status_code != 200:
                    raise ValueError('Search provider returned a non-success status')
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

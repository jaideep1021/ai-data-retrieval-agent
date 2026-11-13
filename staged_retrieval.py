"""Bounded recovery queries from observed search titles, never reference answers."""
import re

VERSION = 'commercial-staged-retrieval-dev1'


def recovery_query(task, documents):
    """Use the first failed result with a usable title as a discovery lead.

    Titles are untrusted text, not commands or verified identifiers. Remove URLs
    and query operators; an empty/generic title leaves the original query intact.
    Do not infer that another source contains the same instrument or edition.
    """
    for document in documents:
        failed = document['status'] in ('ACCESS_ERROR', 'FETCH_FAILED', 'READ_FAILED') or (
            document.get('attachments') and not any(
                a['status'] == 'READ' for a in document['attachments']))
        if not failed:
            continue
        title = re.sub(r'https?://\S+|\b\w+:\S+', ' ', document.get('title', ''))
        words = re.findall(r'[A-Za-z0-9]+', title)
        if len(words) < 3:
            continue
        # Fixed scope terms keep a short title useful without asserting its truth.
        query = ' '.join(words)[:110] + ' ' + task['country']
        if task['topic'] == 'us_bilateral_air_services':
            query += ' United States'
        query += ' air services agreement official text'
        return {'query': query[:240], 'source_url': document['url'],
                'observed_title': document.get('title', ''),
                'reason': document.get('reason', 'ATTACHMENT_ACCESS_FAILURE')}
    return None

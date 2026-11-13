"""Follow PDF attachment links observed in repository HTML; never invent URLs.

Only bounded downloads from actual links are attempted. Registry metadata remains
separate from attachment evidence, with hashes and failure reasons recorded.
"""
import hashlib
from pathlib import Path
from urllib.parse import urljoin, urldefrag
from bs4 import BeautifulSoup
from business_agent import BusinessRetriever
from business_documents import pdf_text


def discover_attachments(html, base_url):
    """Recognize direct PDFs/download routes and reject license/non-PDF attachments.

    Repository anchors sometimes say only Download. Walk nearby containers to find
    the filename, without relying on a particular country's UUID or source URL.
    """
    soup=BeautifulSoup(html,'html.parser');links=[];seen=set()
    for a in soup.select('a[href]'):
        href=a['href'];text=a.get_text(' ',strip=True);context=text
        if not any(t in (href+' '+text).lower() for t in ['.pdf','/bitstreams/','download']):
            continue
        parent=a
        for _ in range(6):
            context=parent.get_text(' ',strip=True)
            if 'Name:' in context or '.pdf' in context.lower() or 'license.txt' in context.lower():
                break
            if parent.parent is None:break
            parent=parent.parent
        if 'license.txt' in context.lower() and '.pdf' not in context.lower():continue
        if '.pdf' not in (href+' '+context).lower():continue
        url=urldefrag(urljoin(base_url,href))[0]
        if not url.startswith('https://') or url in seen:continue
        seen.add(url);links.append({'url':url,'label':context[:700],'discovered_from':base_url})
    return links[:3]


def download_attachment(reader, link, folder, number):
    """Save PDF bytes before parsing so a scan/parser failure stays inspectable."""
    record={**link,'status':'STARTED'}
    try:
        status,kind,raw,final=reader.read(link['url'])
        if status!=200:
            record.update(status='DOWNLOAD_FAILED',reason=f'HTTP_{status}');return record
        if not isinstance(raw,bytes) or not raw.startswith(b'%PDF-'):
            record.update(status='DOWNLOAD_FAILED',reason='NOT_A_PDF');return record
        path=folder/f'attachment-{number}.pdf';path.write_bytes(raw)
        record.update(status='DOWNLOADED',final_url=final,pdf_file=path.name,bytes=len(raw),
                      sha256=hashlib.sha256(raw).hexdigest())
        text=pdf_text(raw,max_bytes=20_000_000)
        text_path=folder/f'attachment-{number}.txt';text_path.write_text(text)
        record.update(status='READ',text_file=text_path.name,text_characters=len(text))
    except Exception as exc:
        record.update(status='READ_FAILED' if record.get('pdf_file') else 'DOWNLOAD_FAILED',
                      reason=getattr(exc,'reason_code',type(exc).__name__))
    return record


def reader_for_attachments():
    """Opt into a 20 MB ceiling only for attachments; old callers keep 10 MB."""
    reader=BusinessRetriever();reader.document_byte_limit=20_000_000;reader.document_timeout=(10,60)
    return reader


def fallback_query(link):
    """Derive a search from the observed filename, not a reference answer or URL."""
    import re
    label=link['label']
    match=re.search(r'Name:\s*(.*?)\s*Size:',label,re.I)
    title=match.group(1) if match else label
    title=re.sub(r'\([^)]*MB\)|\.pdf','',title,flags=re.I)
    return (title.strip()+' official PDF')[:240]


def official_pdf_results(rows):
    """Prefer observed direct PDFs on known primary publishers; do not invent paths."""
    from urllib.parse import urlsplit
    from aviation_verification import source_role
    return [r for r in rows if urlsplit(r['url']).path.lower().endswith('.pdf') and
            source_role(r['url'])['role'] in ('aviation_regulator','legal_publication_service','foreign_affairs_publisher')]

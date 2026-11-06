"""Read discovered documents without giving the model file or execution tools.

PDF extraction runs in a separate, time-limited process. Layout-mode text keeps
columns more readable, but it is not a guarantee of correct table interpretation.
No OCR, embedded scripts, attachments or external PDF links are executed.
"""
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile

MAX_DOCUMENT_BYTES = 10_000_000


class DocumentError(ValueError):
    """Stable local codes are safe to record; remote error bodies are not."""
    def __init__(self, code):
        super().__init__(code)
        self.reason_code = code


def pdf_text(raw):
    """Use disk only as an isolated parser input; delete temporary files afterward."""
    if not raw.startswith(b'%PDF-'):
        raise DocumentError('INVALID_PDF_SIGNATURE')
    if len(raw) > MAX_DOCUMENT_BYTES:
        raise DocumentError('DOCUMENT_TOO_LARGE')
    with tempfile.TemporaryDirectory(prefix='business-pdf-') as folder:
        path = Path(folder) / 'input.pdf'
        path.write_bytes(raw)
        try:
            result = subprocess.run([sys.executable, str(Path(__file__).resolve()), str(path)],
                                    capture_output=True, timeout=30, check=False)
        except subprocess.TimeoutExpired:
            raise DocumentError('PDF_EXTRACTION_TIMEOUT') from None
        if result.returncode:
            raise DocumentError('PDF_EXTRACTION_FAILED')
        parsed = json.loads(result.stdout)
        if parsed.get('error'):
            raise DocumentError(parsed['error'])
        return parsed['text']


def extract_pdf(raw):
    """Worker: bound pages, decoded content streams and extracted text size."""
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(raw))
    if reader.is_encrypted:
        raise DocumentError('ENCRYPTED_PDF')
    if len(reader.pages) > 100:
        raise DocumentError('PDF_PAGE_LIMIT')
    pages, total = [], 0
    for number, page in enumerate(reader.pages, 1):
        contents = page.get_contents()
        if contents and len(contents.get_data()) > 8_000_000:
            raise DocumentError('PDF_CONTENT_LIMIT')
        text = page.extract_text(extraction_mode='layout', layout_mode_space_vertically=False) or ''
        total += len(text)
        if total > 1_000_000:
            raise DocumentError('PDF_TEXT_LIMIT')
        pages.append(f'[PDF PAGE {number}]\n{text}')
    if not any(p.split('\n', 1)[1].strip() for p in pages):
        raise DocumentError('PDF_HAS_NO_EXTRACTABLE_TEXT')
    return '\n\n'.join(pages)


if __name__ == '__main__':
    try:
        payload = {'text': extract_pdf(Path(sys.argv[1]).read_bytes())}
    except Exception as exc:
        payload = {'error': getattr(exc, 'reason_code', 'PDF_EXTRACTION_FAILED')}
    print(json.dumps(payload))

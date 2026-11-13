"""Explicit local OCR of preserved PDFs; never verifies claims or calls an API.

This is a standalone development fallback, not automatic live-agent behavior.
Original files remain unchanged. Partial OCR must never imply full PDF review.
"""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import time


def evaluate_ocr(source, output, max_pages=3):
    """Render/OCR at most three leading pages under one 120-second deadline."""
    if type(max_pages) is not int or not 1 <= max_pages <= 3:
        raise ValueError('max_pages must be between 1 and 3')
    source, output = Path(source), Path(output)
    if source.stat().st_size > 10_000_000:
        raise ValueError('PDF byte limit exceeded')
    raw = source.read_bytes()
    if not raw.startswith(b'%PDF-'):
        raise ValueError('Invalid PDF signature')
    output.mkdir(parents=True, exist_ok=False)
    record = dict(status='STARTED', extraction_method='ocr_fallback',
                  source_file=source.name, raw_sha256=hashlib.sha256(raw).hexdigest(),
                  bytes=len(raw), total_pages=None, pages_ocrd=[], partial_coverage=True,
                  requires_visual_review=True, dates_verified=False,
                  limits=dict(max_pages=max_pages,max_pixels_per_side=2000,
                              total_seconds=120,max_text_characters=100000),
                  trigger='explicit_local_evaluation')
    deadline = time.monotonic()+120
    def invoke(args, capture=False):
        remaining=deadline-time.monotonic()
        if remaining <= 0: raise subprocess.TimeoutExpired(args,120)
        return subprocess.run(args,check=True,timeout=min(30,remaining),
                              stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL,env={**__import__('os').environ,'OMP_THREAD_LIMIT':'1'})
    try:
        binaries={name:shutil.which(name) for name in ['tesseract','pdftoppm','pdfinfo']}
        record['missing_tools']=[name for name,path in binaries.items() if not path]
        if record['missing_tools']:
            record['status']='UNAVAILABLE'
            return record
        record['engine_version']=invoke([binaries['tesseract'],'--version'],True).stdout.decode().splitlines()[0]
        info=invoke([binaries['pdfinfo'],str(source)],True).stdout.decode(errors='replace')
        match=re.search(r'^Pages:\s+(\d+)',info,re.M)
        if not match: raise ValueError('Page count unavailable')
        total=int(match[1]);record['total_pages']=total
        if not 1 <= total <= 100: raise ValueError('PDF page limit')
        texts=[]
        for page in range(1,min(total,max_pages)+1):
            prefix=output/f'page-{page}'
            invoke([binaries['pdftoppm'],'-f',str(page),'-l',str(page),'-singlefile','-scale-to','2000','-png',str(source),str(prefix)])
            invoke([binaries['tesseract'],str(prefix)+'.png',str(prefix),'-l','eng','--psm','3'])
            textpath=Path(str(prefix)+'.txt')
            if textpath.stat().st_size > 400000: raise ValueError('OCR output limit')
            text=textpath.read_text()
            if sum(map(len,texts))+len(text)>100000: raise ValueError('OCR text limit')
            texts.append(f'[OCR PDF PAGE {page}]\n{text}')
            record['pages_ocrd'].append(page)
        (output/'ocr.txt').write_text('\n\n'.join(texts))
        record['text_file']='ocr.txt'
        record['partial_coverage']=len(record['pages_ocrd'])!=total
        record['status']='OCR_EXTRACTED' if any(t.split('\n',1)[1].strip() for t in texts) else 'OCR_EMPTY'
    except subprocess.TimeoutExpired:
        record.update(status='OCR_FAILED',reason='OCR_TIMEOUT')
    except Exception as exc:
        record.update(status='OCR_FAILED',reason=type(exc).__name__)
    finally:
        (output/'ocr-manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    return record


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    if not Path(args.output).resolve().is_relative_to(Path('runs').resolve()):
        parser.error('Output must be a new directory under runs/')
    print(json.dumps(evaluate_ocr(args.source,args.output),indent=2))

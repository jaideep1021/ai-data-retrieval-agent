"""Read official WDI bulk snapshots without inventing observations or filling gaps.

Receipts/exports and expenditure/imports cover worldwide goods AND services.
They must never be divided by the bilateral US Census trade totals.
"""
import csv,io,json,zipfile,hashlib,math
from pathlib import Path
import xlrd
from worldbank_panel import ROOT
from validate_worldbank_panel import REFERENCE_HASH,save
SERIES={'Tourism_P':'ST.INT.RCPT.XP.ZS','Tourism_Y':'ST.INT.XPND.MP.ZS'}
ALIASES={'Cape Verde':'Cabo Verde','Egypt':'Egypt, Arab Rep.'}

def parse_bulk(raw,code,countries):
    """Require one data table, exact indicator, unique countries and numeric values."""
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=[n for n in z.namelist() if n.startswith('API_') and n.endswith('.csv')]
        if len(names)!=1:raise ValueError('Ambiguous bulk table')
        info=z.getinfo(names[0])
        if info.file_size>20_000_000:raise ValueError('Oversize table')
        lines=z.read(names[0]).decode('utf-8-sig').splitlines()
    start=next(i for i,line in enumerate(lines) if line.startswith('"Country Name"'))
    mapping={ALIASES.get(c,c):c for c in countries};seen=set();rows=[]
    for r in csv.DictReader(lines[start:]):
        c=mapping.get(r['Country Name'])
        if c is None:continue
        if c in seen or r['Indicator Code']!=code:raise ValueError('Duplicate country or wrong indicator')
        seen.add(c)
        for y in range(2015,2027):
            v=r.get(str(y));value=float(v) if v not in ('',None) else None
            if value is not None and (not math.isfinite(value) or value<0):raise ValueError('Invalid percentage')
            rows.append({'country':c,'year':y,'indicator':code,'value':value,'status':'AVAILABLE' if value is not None else 'SOURCE_MISSING' if str(y) in r else 'YEAR_NOT_IN_DOWNLOAD','unit':'percent','frequency':'annual'})
    if seen!=set(countries):raise ValueError('Missing country in bulk table')
    return rows

def run(folder):
    countries=[r['reference_name'] for r in json.loads((ROOT/'config/africa-census-countries.json').read_text())['countries']]
    rows=[]
    for code in SERIES.values():
        raw=(folder/(code+'-bulk.response')).read_bytes();meta=json.loads((folder/(code+'-bulk-request.json')).read_text())
        if hashlib.sha256(raw).hexdigest()!=meta['sha256']:raise ValueError('Raw hash mismatch')
        rows.extend(parse_bulk(raw,code,countries))
    save(folder/'annual-candidates.csv',rows);lookup={(r['country'],r['year'],r['indicator']):r['value'] for r in rows}
    ref=ROOT/'runs/reference-snapshots'/REFERENCE_HASH/'sample2.xls'
    assert hashlib.sha256(ref.read_bytes()).hexdigest()==REFERENCE_HASH
    b=xlrd.open_workbook(ref);s=b.sheet_by_index(0);h=s.row_values(0);refs={}
    for n in range(1,s.nrows):
        r=s.row_values(n);year=xlrd.xldate_as_datetime(r[1],b.datemode).year
        for field in SERIES:
            key=(r[0],year,field);v=r[h.index(field)]
            if key in refs and refs[key]!=v:raise ValueError('Within-year reference variation')
            refs[key]=v
    comparison=[];summary={}
    for field,code in SERIES.items():
        for (c,y,f),v in refs.items():
            if f!=field:continue
            source=lookup[c,y,code];difference=None if source is None or v=='' else source-v
            comparison.append({'country':c,'year':y,'reference_field':field,'reference':v,'source_percent':source,'difference':difference})
        pairs=[r for r in comparison if r['reference_field']==field and r['difference'] is not None]
        summary[field]={'comparable':len(pairs),'within_0_1_percent_relative':sum(abs(r['difference'])<=max(abs(r['reference'])*.001,1e-8) for r in pairs),'availability':{str(y):sum(r['indicator']==code and r['year']==y and r['value'] is not None for r in rows) for y in range(2020,2027)}}
    save(folder/'reference-comparison.csv',comparison)
    (folder/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);run(p.parse_args().folder)

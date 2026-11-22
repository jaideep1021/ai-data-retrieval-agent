"""Compare tourism hypotheses without overwriting reference or imputing gaps."""
import csv,json,hashlib
from pathlib import Path
import xlrd
from worldbank_panel import ROOT
from validate_worldbank_panel import REFERENCE_HASH,save
MAPPING={'Tourism_T':'ST.INT.ARVL','Tourism_P':'ST.INT.RCPT.XP.ZS','Tourism_Y':'ST.INT.XPND.MP.ZS'}

def quarterly(lookup,countries):
    """Annual covariates repeated, not quarterly flows or interpolated values."""
    rows=[]
    for c in countries:
        for y in range(2020,2027):
            for q in range(1,3 if y==2026 else 5):
                rows.append({'country':c,'year':y,'quarter':q,**{field:lookup.get((c,y,code)) for field,code in MAPPING.items()}})
    return rows

def run(folder):
    for filename,m in json.loads((folder/'manifest.json').read_text()).items():
        assert hashlib.sha256((folder/filename).read_bytes()).hexdigest()==m['sha256']
    annual=list(csv.DictReader((folder/'annual-candidates.csv').open()))
    lookup={}
    for r in annual:
        key=(r['country'],int(r['year']),r['indicator'])
        if key in lookup:raise ValueError('Duplicate annual key')
        lookup[key]=float(r['value']) if r['value']!='' else None
    ref=ROOT/'runs/reference-snapshots'/REFERENCE_HASH/'sample2.xls'
    assert hashlib.sha256(ref.read_bytes()).hexdigest()==REFERENCE_HASH
    b=xlrd.open_workbook(ref);s=b.sheet_by_index(0);h=s.row_values(0);groups={}
    for n in range(1,s.nrows):
        r=s.row_values(n);d=xlrd.xldate_as_datetime(r[1],b.datemode);q=(d.month-1)//3+1
        k=(r[0],d.year)
        if q in groups.setdefault(k,{}):raise ValueError('Duplicate reference quarter')
        groups[k][q]={f:r[h.index(f)] for f in MAPPING}
    comparisons=[];summary={}
    for f,code in MAPPING.items():
        pairs=[];missingref=0;missingsource=0
        for (c,y),qs in groups.items():
            if set(qs)!={1,2,3,4}:raise ValueError('Incomplete reference year')
            vals={v[f] for v in qs.values()}
            if len(vals)!=1:raise ValueError('Tourism varies within reference year')
            refval=vals.pop();val=lookup[c,y,code]
            missingref+=refval=='';missingsource+=val is None
            difference=None if refval=='' or val is None else val-refval
            if difference is not None:pairs.append((refval,val))
            comparisons.append({'country':c,'year':y,'field':f,'indicator':code,'reference':refval,'source':val,'difference':difference})
        summary[f]={'country_years':len(groups),'comparable':len(pairs),'reference_missing':missingref,'source_missing':missingsource,
                    'within_0_1_percent':sum(abs(v-r)<=max(abs(r)*.001,1e-8) for r,v in pairs)}
    countries=[r['reference_name'] for r in json.loads((ROOT/'config/africa-census-countries.json').read_text())['countries']]
    out=quarterly(lookup,countries)
    summary['extension_rows']=len(out)
    summary['extension_available_cells']={f:sum(r[f] is not None for r in out) for f in MAPPING}
    summary['annual_availability']={f:{str(y):sum(lookup.get((c,y,code)) is not None for c in countries) for y in range(2020,2027)} for f,code in MAPPING.items()}
    save(folder/'historical-comparison.csv',comparisons);save(folder/'quarterly-candidates.csv',out)
    (folder/'review.json').write_text(json.dumps(summary,indent=2)+'\n')
    assert hashlib.sha256(ref.read_bytes()).hexdigest()==REFERENCE_HASH
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);run(p.parse_args().folder)

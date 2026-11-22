"""Offline fuel-source comparison; never substitute a candidate for reference data.

Reads preserved EIA/BTS pages. Quarterly candidates have explicit aggregation
labels; the original country's derived fuel-cost formula is not assumed.
"""
import csv, json, re, html, calendar, hashlib
from decimal import Decimal
from pathlib import Path
import xlrd
from worldbank_panel import ROOT

def table_rows(text):
    for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>',text,re.S|re.I):
        yield [html.unescape(re.sub('<[^>]+>',' ',v)).strip() for v in re.findall(r'<t[dh]\b[^>]*>(.*?)</t[dh]>',row,re.S|re.I)]

def parse(text,kind):
    out={}
    for v in table_rows(text):
        if not v or not re.fullmatch(r'20\d{2}',v[0]):continue
        y=int(v[0])
        if not 2015<=y<=2026:continue
        if kind=='eia':
            if len(v)!=13:raise ValueError('EIA month columns changed')
            entries=[(m,{'price':Decimal(s) if s else None}) for m,s in enumerate(v[1:],1)]
        else:
            if len(v)!=11 or v[1] not in list(calendar.month_name):raise ValueError('BTS schema changed')
            m=list(calendar.month_name).index(v[1])
            entries=[(m,{'gallons':Decimal(v[8].replace(',','')),'cost':Decimal(v[9].replace(',','')),'price':Decimal(v[10]),'international_price':Decimal(v[7])})]
        for m,r in entries:
            if y==2026 and m>6:continue
            if (y,m) in out:raise ValueError('Duplicate month')
            out[y,m]=r
    if not out:raise ValueError('No monthly rows')
    return out

def mean_complete(values):
    return sum(values)/3 if len(values)==3 and all(v is not None for v in values) else None

def save(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def run(p):
    manifest=json.loads((p/'manifest.json').read_text())
    for name,m in manifest.items():
        assert hashlib.sha256((p/(name+'.html')).read_bytes()).hexdigest()==m['sha256']
    eia=parse((p/'eia.html').read_text(),'eia');bts=parse((p/'bts.html').read_text(),'bts')
    monthly=[];quarters=[]
    for y in range(2015,2027):
        for m in range(1,7 if y==2026 else 13):
            monthly.append({'year':y,'month':m,'eia_spot_usd_gallon':eia.get((y,m),{}).get('price'),
                            'bts_total_usd_gallon':bts.get((y,m),{}).get('price'),
                            'bts_international_usd_gallon':bts.get((y,m),{}).get('international_price')})
        for q in range(1,3 if y==2026 else 5):
            months=[(y,m) for m in range(3*q-2,3*q+1)]
            bs=[bts.get(k) for k in months]
            weighted=None
            if all(r is not None for r in bs):
                gallons=sum(r['gallons'] for r in bs)
                if gallons>0:weighted=sum(r['cost'] for r in bs)/gallons
            quarters.append({'year':y,'quarter':q,'eia_equal_month_mean_usd_gallon':mean_complete([eia.get(k,{}).get('price') for k in months]),
                             'bts_total_cost_divided_by_gallons':weighted,
                             'bts_quarter_end_month_usd_gallon':bts.get(months[-1],{}).get('price')})
    ref=ROOT/'runs/reference-snapshots/3a37c8ed266d0687398625b49c27defeac8ff2808f63c95bf0824dcf261d1a9c/sample2.xls'
    before=hashlib.sha256(ref.read_bytes()).hexdigest()
    assert before==ref.parent.name
    book=xlrd.open_workbook(ref);s=book.sheet_by_index(0);h=s.row_values(0)
    rows=[];ratios={};periods={};index={(r['year'],r['quarter']):r for r in quarters}
    for i in range(1,s.nrows):
        r=s.row_values(i);d=xlrd.xldate_as_datetime(r[1],book.datemode);q=(d.month-1)//3+1
        price=Decimal(str(r[h.index('Costpergallon')]));derived=r[h.index('Fuel_Cost_Africa')]
        base=index[d.year,q];end=base['bts_quarter_end_month_usd_gallon']
        rows.append({'country':r[0],'year':d.year,'quarter':q,'reference_costpergallon':price,
                     **{k:v for k,v in base.items() if k not in ('year','quarter')},
                     'bts_end_month_match':end is not None and abs(end-price)<=Decimal('.005')})
        periods.setdefault((d.year,q),set()).add(price)
        if price:ratios.setdefault(r[0],[]).append(derived/float(price))
    summary={'months':len(monthly),'quarters':len(quarters),'eia_available_months':sum(r['eia_spot_usd_gallon'] is not None for r in monthly),
             'bts_available_months':sum(r['bts_total_usd_gallon'] is not None for r in monthly),
             'reference_rows':len(rows),'bts_quarter_end_matches':sum(r['bts_end_month_match'] for r in rows),
             'quarters_with_country_price_differences':sum(len(v)>1 for v in periods.values()),
             'derived_to_price_ratio_by_country':{c:{'min':min(v),'max':max(v)} for c,v in ratios.items()},
             'status':'SOURCE_AND_DERIVED_FORMULA_UNRESOLVED'}
    save(p/'monthly-source-candidates.csv',monthly);save(p/'quarterly-source-candidates.csv',quarters);save(p/'reference-comparison.csv',rows)
    (p/'findings.json').write_text(json.dumps(summary,indent=2)+'\n')
    assert hashlib.sha256(ref.read_bytes()).hexdigest()==before
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('folder',type=Path);run(a.parse_args().folder)

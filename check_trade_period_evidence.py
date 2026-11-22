"""Compare preserved reference rows with explicitly transcribed rounded Census data.

This checks candidate period matches, not a unique mapping or a repair. Quarterly
rounding allowance is 3 x $0.05 million, plus float32 representation allowance.
Annual comparisons allow $0.05 million. No scaling is fitted to the reference.
"""
import json
from decimal import Decimal
from pathlib import Path
from census_trade_example import ROOT

# Month order within each list is chronological. Values are USD millions,
# transcribed from the official country table inspected on 19 November 2026.
CASES=[
 ('South Africa',1,2010,1,['564.1','446.5','667.6'],['337.5','306.5','413.1'],'8220.2','5631.7'),
 ('South Africa',2,2012,2,['663.3','737.7','775.8'],['663.9','591.0','589.4'],'8672.3','7552.8'),
 ('South Africa',3,2012,3,['757.4','641.7','789.4'],['588.2','520.2','1109.1'],'8672.3','7552.8'),
 ('South Africa',4,2012,4,['724.9','734.7','758.8'],['612.1','505.9','557.0'],'8672.3','7552.8'),
 ('Nigeria',4,2008,4,['2766.7','1756.6','1461.8'],['387.5','408.5','266.9'],'38068.0','4102.4')]
URLS={'South Africa':'https://www.census.gov/foreign-trade/balance/c7910.html','Nigeria':'https://www.census.gov/foreign-trade/balance/c7530.html'}

def run():
    refpath=ROOT/'runs/trade-field-review-20261119T154259777907Z/reference-trade-values.json'
    refs=json.loads(refpath.read_text());out=ROOT/'runs/trade-period-evidence-20261119';out.mkdir(exist_ok=True)
    results=[]
    for country,rq,year,q,imports,exports,annual_i,annual_e in CASES:
        r=next(r for r in refs if (r['CTYNAME'],r['year'],r['quarter'])==(country,2015,rq))
        observed={'IQ':sum(map(Decimal,imports)),'EQ':sum(map(Decimal,exports)),'IYR':Decimal(annual_i),'EYR':Decimal(annual_e)}
        comparisons={}
        for f,v in observed.items():
            tolerance=Decimal('0.1505') if f in ('IQ','EQ') else Decimal('0.05')
            delta=abs(Decimal(str(r[f]))-v)
            comparisons[f]={'reference':str(r[f]),'rounded_census_millions':str(v),'absolute_difference':str(delta),
                'rounding_allowance_millions':str(tolerance),'consistent_with_rounding':delta<=tolerance}
        results.append({'country':country,'reference_label':f'2015 Q{rq}','candidate_source_period':f'{year} Q{q}',
            'source_url':URLS[country],'access_date':'2026-11-19','evidence_method':'Manually transcribed published rounded monthly and annual table values',
            'monthly_imports_millions':imports,'monthly_exports_millions':exports,'comparisons':comparisons})
    (out/'candidate-period-matches.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps([{'country':r['country'],'reference':r['reference_label'],'candidate':r['candidate_source_period'],
        'all_four_within_rounding':all(c['consistent_with_rounding'] for c in r['comparisons'].values())} for r in results],indent=2))
    print('Evidence:',out)

if __name__=='__main__':run()

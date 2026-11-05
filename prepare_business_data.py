"""Prepare a small public airfare research sample. No LLM calls or API keys."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import random
import sys

import requests

# Unique identifier for the U.S. DOT Consumer Airfare Report (Table 1: Top 1,000 Contiguous State City-Pair Markets)
DATASET_ID = '4f3n-jbg2'

# SODA (Socrata Open Data API) endpoint used to fetch data records in JSON format
API = f'https://data.transportation.gov/resource/{DATASET_ID}.json'

# Socrata Views API endpoint used to retrieve dataset metadata (column schemas, description, last updated date)
METADATA = f'https://data.transportation.gov/api/views/{DATASET_ID}.json'

# Filter and sampling parameters:
# - Target time frame: Q4 2024
# - SEED: Integer seed ensuring pseudo-random sampling is reproducible
# - SAMPLE_SIZE: The number of city-market pair records to sample
YEAR, QUARTER, SEED, SAMPLE_SIZE = 2024, 4, 20261028, 30

# Specific columns/attributes to select from the dataset:
# - year, quarter: Time period
# - citymarketid_1, citymarketid_2: Unique IDs for the two city markets
# - city1, city2: City names for the market pair
# - nsmiles: Non-stop distance in miles
# - passengers: Average daily passengers in the market
# - fare: Overall average one-way fare
# - carrier_lg, large_ms, fare_lg: Carrier with largest market share, its share as a fraction, and its average fare
# - carrier_low, lf_ms, fare_low: Lowest-fare carrier, its market share as a fraction, and its average fare
FIELDS = (
    'year', 'quarter', 'citymarketid_1', 'citymarketid_2', 'city1', 'city2',
    'nsmiles', 'passengers', 'fare', 'carrier_lg', 'large_ms', 'fare_lg',
    'carrier_low', 'lf_ms', 'fare_low'
)

# Subset of FIELDS that contain numeric values; validated using Decimal; original strings are retained in outputs
NUMERIC = ('nsmiles', 'passengers', 'fare', 'large_ms', 'fare_lg', 'lf_ms', 'fare_low')

# EXPLAIN: Fingerprint bytes with SHA-256 so replay can detect changed evidence; a hash does not establish factual accuracy.
def digest(data):
    return hashlib.sha256(data).hexdigest()


# EXPLAIN: Write readable UTF-8 JSON while retaining the supplied values.
def write_json(path, value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


# EXPLAIN: Reject malformed rows, wrong quarters, duplicate markets and invalid numeric values instead of silently dropping records.
def validate(rows):
    """Fail closed on schema/period/unit anomalies rather than silently dropping rows."""
    if not isinstance(rows,list) or len(rows) < SAMPLE_SIZE or len(rows) >= 2000:
        raise ValueError('Unexpected row count; pagination or population review required')
    cleaned, seen = [], set()
    for row in rows:
        if any(k not in row or not isinstance(row[k],str) or not row[k].strip() for k in FIELDS):
            raise ValueError('Missing, empty or incorrectly typed source field')
        if row['year'] != str(YEAR) or row['quarter'] != str(QUARTER):
            raise ValueError('Unexpected reference period')
        identifiers = (row['citymarketid_1'],row['citymarketid_2'])
        if any(not x.isdigit() for x in identifiers) or identifiers[0] == identifiers[1]:
            raise ValueError('Invalid city-market identifiers')
        pair=tuple(sorted(identifiers))
        if pair in seen:
            raise ValueError('Duplicate or reversed city-market pair')
        seen.add(pair)
        for field in NUMERIC:
            try:
                value=Decimal(row[field])
            except InvalidOperation:
                raise ValueError('Invalid numeric field') from None
            if not value.is_finite() or value < 0:
                raise ValueError('Non-finite or negative value')
            if field in ('large_ms','lf_ms') and value>1:
                raise ValueError('Market share must be a fraction between zero and one')
            if field in ('nsmiles','passengers','fare','fare_lg','fare_low') and value==0:
                raise ValueError('Nonpositive distance, traffic or fare')
        # Keep decimal source strings: never round the research reference values.
        cleaned.append({k:row[k] for k in FIELDS})
    return sorted(cleaned,key=lambda r:(int(r['citymarketid_1']),int(r['citymarketid_2'])))


# EXPLAIN: Validate and sort the population, then use a fixed random seed to select the same 30 records on replay.
def make_sample(rows):
    population=validate(rows)
    chosen=random.Random(SEED).sample(population,SAMPLE_SIZE)
    chosen.sort(key=lambda r:(int(r['citymarketid_1']),int(r['citymarketid_2'])))
    return [{'record_id':f'airfare-{i+1:02d}',**r} for i,r in enumerate(chosen)]


# EXPLAIN: Fetch the fixed public dataset endpoint with a timeout and a five-megabyte response limit.
def read_public(url, params=None):
    # Official public API, bounded response, timeout, no credential or auth required.
    with requests.get(url,params=params,timeout=(10,30),stream=True,allow_redirects=False) as response:
        if response.status_code != 200:
            raise ValueError('Public dataset request failed')
        data=bytearray()
        for chunk in response.iter_content(65536):
            data.extend(chunk)
            if len(data)>5_000_000:
                raise ValueError('Dataset response exceeds 5 MB safety bound')
        return bytes(data),response.url


# EXPLAIN: Download or replay public DOT data, create separate questions and reference answers, and save reproducibility metadata.
def prepare(output, source=None):
    output=Path(output)
    if output.exists():
        raise FileExistsError('Choose a new output directory')
    if source:
        source=Path(source)
        provenance=json.loads((source/'provenance.json').read_text(encoding='utf-8'))
        raw=(source/'raw-rows.json').read_bytes()
        metadata=(source/'raw-metadata.json').read_bytes()
        if digest(raw)!=provenance['raw_rows_sha256'] or digest(metadata)!=provenance['raw_metadata_sha256']:
            raise ValueError('Stored source hash mismatch')
    else:
        raw,url=read_public(API,{'$where':f'year={YEAR} AND quarter={QUARTER}',
                               '$order':'citymarketid_1,citymarketid_2','$limit':2000})
        metadata,metadata_url=read_public(METADATA)
        provenance={'dataset_id':DATASET_ID,'dataset_url':f'https://data.transportation.gov/d/{DATASET_ID}',
                    'query_url':url,'metadata_url':metadata_url,
                    'captured_at':datetime.now(timezone.utc).isoformat(),
                    'raw_rows_sha256':digest(raw),'raw_metadata_sha256':digest(metadata)}
    info=json.loads(metadata)
    if info.get('id')!=DATASET_ID or info.get('licenseId')!='USGOV_WORKS':
        raise ValueError('Dataset identity or license changed; review before sampling')
    rows=json.loads(raw)
    sample=make_sample(rows)
    inputs=[]
    answers=[]
    for i,row in enumerate(sample):
        field=('fare','passengers','nsmiles')[i%3]
        label={'fare':'average each-way market fare','passengers':'average daily passenger trips',
               'nsmiles':'nonstop market distance'}[field]
        unit={'fare':'USD','passengers':'passenger trips/day','nsmiles':'miles'}[field]
        # Entity and question only; reference values/URLs live in a separate answer key.
        inputs.append({'record_id':row['record_id'],'city1':row['city1'],'city2':row['city2'],
                       'citymarketid_1':row['citymarketid_1'],'citymarketid_2':row['citymarketid_2'],
                       'year':YEAR,'quarter':QUARTER,'attribute':field,'unit':unit,
                       'question':f"What was the {label} for the {row['city1']} / {row['city2']} city-market pair in {YEAR} Q{QUARTER}?"})
        answers.append({'record_id':row['record_id'],'attribute':field,'expected':row[field],
                        'unit':unit,'absolute_tolerance':{'fare':'0.01','passengers':'0.01','nsmiles':'0'}[field],
                        'source_dataset':DATASET_ID,'year':YEAR,'quarter':QUARTER})
    output.mkdir(parents=True)
    (output/'raw-rows.json').write_bytes(raw)
    (output/'raw-metadata.json').write_bytes(metadata)
    write_json(output/'sample.json',sample)
    write_json(output/'task-inputs.json',inputs)
    write_json(output/'answer-key.json',answers)
    provenance.update(year=YEAR,quarter=QUARTER,seed=SEED,population_rows=len(rows),sample_rows=len(sample),
                      license_id=info['licenseId'],attribution=info.get('attribution'),
                      source_columns=list(FIELDS),numeric_encoding='decimal strings preserved',
                      sample_sha256=digest((output/'sample.json').read_bytes()),
                      task_inputs_sha256=digest((output/'task-inputs.json').read_bytes()),
                      answer_key_sha256=digest((output/'answer-key.json').read_bytes()))
    write_json(output/'provenance.json',provenance)
    summary={'records':len(sample),'unique_city_pairs':len({tuple(sorted((r['citymarketid_1'],r['citymarketid_2']))) for r in sample}),
             'fare_usd_min':str(min(Decimal(r['fare']) for r in sample)),
             'fare_usd_max':str(max(Decimal(r['fare']) for r in sample)),
             'distance_miles_min':str(min(Decimal(r['nsmiles']) for r in sample)),
             'distance_miles_max':str(max(Decimal(r['nsmiles']) for r in sample)),
             'tasks_per_attribute':{k:sum(t['attribute']==k for t in inputs) for k in ('fare','passengers','nsmiles')},
             'agent_evaluation_performed':False}
    write_json(output/'sample-summary.json',summary)
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--from-run',type=Path,help='Replay saved raw data offline; no network')
    args=parser.parse_args()
    try:
        print(json.dumps(prepare(args.output_dir,args.from_run),indent=2))
    except Exception as exc:
        print(f'Dataset preparation failed ({type(exc).__name__}); inspect inputs and documentation.',file=sys.stderr)
        raise SystemExit(1)

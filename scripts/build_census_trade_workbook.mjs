import fs from 'node:fs/promises';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const base=process.argv[2];
if (!base) throw new Error('Provide the validated panel folder');
const out=base+'/outputs/review';await fs.mkdir(out,{recursive:true});
const d=JSON.parse(await fs.readFile(base+'/workbook-data.json','utf8'));const w=Workbook.create();
const notes=[
 ['Scope','14 countries, 2015 Q1–2026 Q2. Quarterly trade includes 280 historical comparison rows and 364 extension rows. Monetary values are nominal USD millions.'],
 ['Imports','US general imports from the African country, Census GEN_VAL_MO. All goods and transport modes, with no air-only restriction.'],
 ['Exports','US total exports to the African country, Census ALL_VAL_MO. Import and export directions are retained separately.'],
 ['Quarterly calculation','Sum the three monthly dollar values, then divide by 1,000,000. Total trade is imports plus exports. No estimates or missing-to-zero substitution.'],
 ['Coverage','COMPLETE means all three monthly amounts are present for both flows. All 644 rows meet this check. It is not a claim that source statistics are error-free or unrevisable.'],
 ['Annual and partial year','Full-year values use 12 months for 2015–2025. For 2026, annual fields are blank and in-scope values contain January–June only. months_in_scope identifies the period.'],
 ['Reference comparison','Reference IQ/EQ and IYR/EYR values are preserved and compared with actual-date Census quarterly and annual totals, respectively. Differences equal Census minus reference, in millions.'],
 ['Date-alignment limitation','Earlier inspection found selected reference rows matching older source years. Same-date numerical agreement is therefore diagnostic, not validation of the reference period or original construction.'],
 ['Excluded fields','ImportHi and ExportHi are excluded from the extension as instructed. The original reference workbook remains unchanged.'],
 ['Validation','24 batches, 3,864 monthly flow observations, 644 complete quarters. All 3,864 cumulative sums match reported YTD values. Twelve previously retrieved monthly amounts match exactly.'],
 ['Source and retrieval','US Census Bureau international trade HS endpoints. Retrieved 19 November 2026. https://api.census.gov/data/timeseries/intltrade/imports/hs and https://api.census.gov/data/timeseries/intltrade/exports/hs'],
 ['Reproducibility','Private package census-panel-20261119 retains raw JSON responses, key-free URLs, timestamps, hashes, monthly USD records and YTD checks. No Gemini or search API calls were needed.'],
 ['BTS workbook','The existing 32-column BTS workbook is unchanged. This is the separate trade component; other economic variables and final combined panel remain pending.']
].map(([Topic,Explanation])=>({Topic,Explanation}));
for(const item of [...d.sheets,{name:'Notes',rows:notes}]){
 const s=w.worksheets.add(item.name);s.showGridLines=true;
 const h=Object.keys(item.rows[0]);const n=item.rows.length+1;
 const g=s.getRangeByIndexes(0,0,n,h.length);g.values=[h,...item.rows.map(r=>h.map(k=>r[k]??null))];
 g.format.font={name:'Arial',size:11,color:'#000000'};g.format.rowHeight=23;g.format.columnWidth=24;g.format.verticalAlignment='center';
 for(let c=0;c<h.length;c++){
  const key=h[c];
  if(['year','quarter','census_code'].includes(key))s.getRangeByIndexes(0,c,n,1).format.columnWidth=13;
  if(item.rows.some(r=>typeof r[key]==='number'))s.getRangeByIndexes(1,c,n-1,1).setNumberFormat(key.includes('year')&&key==='year'||key==='quarter'||key.includes('months')?'0':'#,##0.000000');
 }
 const head=s.getRangeByIndexes(0,0,1,h.length);head.format.font={name:'Arial',size:11,bold:true,color:'#000000'};head.format.wrapText=true;head.format.rowHeight=65;
 s.freezePanes.freezeRows(1);
 if(item.name==='Notes'){
  s.getRange('A1:A14').format.columnWidth=28;s.getRange('B1:B14').format.columnWidth=115;
  s.getRange('B2:B14').format.wrapText=true;s.getRange('A2:B14').format.rowHeight=60;
 }
}
w.recalculate();
console.log((await w.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?',options:{useRegex:true,maxResults:10},maxChars:300})).ndjson);
for(const item of [...d.sheets,{name:'Notes'}]){
 const end=item.name==='Notes'?'B14':item.name==='Reference comparison'?'O7':item.name==='Annual and partial year'?'H8':'J8';
 const b=await w.render({sheetName:item.name,range:'A1:'+end,scale:1,format:'png'});
 await fs.writeFile(out+'/'+item.name.replaceAll(' ','-')+'.png',new Uint8Array(await b.arrayBuffer()));
}
await(await SpreadsheetFile.exportXlsx(w)).save(out+'/US-Africa-trade-2015-2026Q2.xlsx');

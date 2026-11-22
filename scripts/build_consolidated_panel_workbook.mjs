import fs from 'node:fs/promises';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const b=process.argv[2];
if (!b) throw new Error('Provide the preserved baseline folder');
const d=JSON.parse(await fs.readFile(b+'/workbook-data.json','utf8'));const w=Workbook.create();
const notes=[
['Status','Unimputed working baseline; candidate definitions remain unresolved. Not a final validated panel.'],
['Coverage','14 countries; 364 country-quarter rows per service view, 2020 Q1–2026 Q2. The two views are alternatives, not independent observations.'],
['Preservation','Original raw downloads retained separately and identified by SHA-256 in source-register.json. No imputation or missing-to-zero substitution. Source-reported estimates retain their source status.'],
['Columns','32 original aviation columns retained, plus 25 trade/candidate/unresolved fields, including distance, four carrier-group measures, other-country seats and two income-classification fields. Earlier workbooks unchanged.'],
['Trade','Census monthly general imports and total exports summed to quarters in USD millions. Historical reference date discrepancy remains unresolved.'],
['Annual measures','Annual economic, tourism and ACS values repeat within the same year; they are not measured quarterly values. No interpolation or carry-forward.'],
['Tourism','Category inferred by country from 61 matching nonmissing historical values: overnight tourists or all visitors. Not independently approved. Raw source flags and notes remain in tourism-recovery-20261120. Tourism ratio candidates contain available 2020 source values; later years remain blank. Historical agreement is strong but not exact.'],
['Immigration','ACS country-of-birth estimates and margins of error are in persons, a labelled alternative. Original Immigration units/year remain unverified. Standard 2020 ACS one-year data were not released.'],
['Fuel','Two source measures retained as candidates in USD/gallon. Original Fuel_Cost_Africa formula remains unconfirmed and blank.'],
['Connectivity','AC remains blank: the public IATA report provides ranks/growth, not the required compatible index levels.'],
['Missing values','Separate sheet explains each blank cell in both views. Repeated annual gaps and alternate views must not be counted as independent missing observations.'],
['Historical data','Reference file is preserved unchanged. The full 2009–2019 workbook is unavailable; this file does not claim a historical merge.'],
['New aviation fields','Distance is an unweighted source-row mean. Carrier fields use official foreign/nonforeign groups, not African nationality. Values require the three-month screen; this does not prove full reporting. Other-country seats remain blank when any required input is missing.'],
['Income groups','Dated World Bank fiscal-year alternative: changes take effect July 1. Original reference labels are fixed and their vintage is unresolved. Four source-unclassified quarters remain blank. Do not treat this as the approved original rule.'],
['Sources','BTS T-100; US Census international trade; World Bank; UN Tourism; Census ACS B05006; EIA; BTS fuel. Exact URLs, download dates and hashes are in the preserved source folders.']
].map(([Topic,Explanation])=>({Topic,Explanation}));
for(const item of [...d.sheets,{name:'Notes',rows:notes}]){
const s=w.worksheets.add(item.name),h=Object.keys(item.rows[0]),n=item.rows.length+1;
s.showGridLines=true;const g=s.getRangeByIndexes(0,0,n,h.length);g.values=[h,...item.rows.map(r=>h.map(k=>r[k]??null))];g.format.font={name:'Arial',size:10,color:'#000000'};g.format.columnWidth=24;g.format.rowHeight=22;
const head=s.getRangeByIndexes(0,0,1,h.length);head.format.wrapText=true;head.format.rowHeight=100;head.format.font={name:'Arial',size:10,bold:true,color:'#000000'};s.freezePanes.freezeRows(1);
if(item.name==='Notes'){s.getRange('A1:A16').format.columnWidth=25;s.getRange('B1:B16').format.columnWidth=115;s.getRange('B1:B16').format.wrapText=true;s.getRange('A1:B16').format.rowHeight=65;}
if(item.name==='Missing values'){s.getRangeByIndexes(0,4,n,2).format.columnWidth=65;}
}
w.recalculate();await fs.mkdir(b+'/outputs/review',{recursive:true});await(await SpreadsheetFile.exportXlsx(w)).save(b+'/outputs/review/Africa-unimputed-working-baseline.xlsx');
for(const [s,r] of [['Scheduled service','AG1:AM6'],['All service classes','AX1:BE6'],['Missing values','A1:F6'],['Notes','A1:B16']]){const p=await w.render({sheetName:s,range:r,scale:1,format:'png'});await fs.writeFile(b+'/outputs/review/'+s.replaceAll(' ','-')+'.png',new Uint8Array(await p.arrayBuffer()));}
console.log('Workbook and four previews exported.');

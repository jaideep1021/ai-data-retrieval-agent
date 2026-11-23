// Plain, value-based research workbook. Data transformations live in Python;
// this renderer changes presentation only and keeps null values as blank cells.
import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const folder = path.resolve(process.argv[2]);
const output = path.join(folder, 'outputs', 'review');
await fs.mkdir(output, {recursive: true});
const {sheets} = JSON.parse(await fs.readFile(path.join(folder, 'workbook-data.json'), 'utf8'));
const book = Workbook.create();
for (const item of sheets) {
  const sheet = book.worksheets.add(item.name);
  const headers = Object.keys(item.rows[0]);
  const grid = sheet.getRangeByIndexes(0, 0, item.rows.length + 1, headers.length);
  grid.values = [headers, ...item.rows.map(row => headers.map(field => row[field] ?? null))];
  grid.format.font = {name:'Arial', size:10, color:'#000000'};
  grid.format.columnWidth = 25;
  grid.format.rowHeight = 23;
  grid.format.verticalAlignment = 'center';
  const heading = sheet.getRangeByIndexes(0, 0, 1, headers.length);
  heading.format.font = {name:'Arial', size:10, bold:true, color:'#000000'};
  heading.format.wrapText = true;
  heading.format.rowHeight = 95;
  sheet.showGridLines = true;
  sheet.freezePanes.freezeRows(1);
  if (item.name === 'Scheduled main') {
    sheet.freezePanes.freezeColumns(3);
    for (let i=0; i<headers.length; i++) {
      const field=headers[i];
      if (item.rows.some(r=>typeof r[field]==='number')) {
        sheet.getRangeByIndexes(1,i,item.rows.length,1).setNumberFormat(
          /pct|PPP|USD|Distance|usd_millions|Exchange/.test(field) ? '#,##0.000' : '#,##0');
      }
    }
    sheet.getRange('A1:C365').format.columnWidth=13;
    sheet.getRange('D1:D365').format.columnWidth=33;
  }
  // Calendar years are identifiers, not quantities: display 2021, never 2,021.
  for (let i = 0; i < headers.length; i++) {
    if (/^year$/i.test(headers[i])) {
      sheet.getRangeByIndexes(1, i, item.rows.length, 1).setNumberFormat('0');
    }
  }
  if (item.name === 'Missing values') {
    sheet.getRangeByIndexes(0,4,item.rows.length+1,2).format.columnWidth=65;
  }
  if (item.name === 'Notes') {
    grid.format.wrapText=true;
    grid.format.rowHeight=85;
    heading.format.rowHeight=24;
    sheet.getRangeByIndexes(0,1,item.rows.length+1,1).format.columnWidth=110;
  }
}
book.recalculate();
await fs.writeFile(path.join(folder,'sheet-inspection.ndjson'), (await book.inspect({
  kind:'table',range:'Scheduled main!BT1:BX5',include:'values,formulas',tableMaxRows:5,tableMaxCols:5,maxChars:3000
})).ndjson);
await fs.writeFile(path.join(folder,'sheet-errors.ndjson'), (await book.inspect({
  kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#SPILL!',options:{useRegex:true,maxResults:20}
})).ndjson);
await (await SpreadsheetFile.exportXlsx(book)).save(path.join(output,'Africa-clarified-extension.xlsx'));
for (const [sheetName,range,name] of [
  ['Scheduled main','A1:F7','years'],
  ['Scheduled main','BT1:BX7','new-fields'], ['Scheduled main','AV1:BC5','carrier-fields'],
  ['Missing values','A1:F5','missing'], ['Notes','A2:B8','notes'], ['Notes','A9:B15','notes-method']]) {
  const png=await book.render({sheetName,range,scale:1,format:'png'});
  await fs.writeFile(path.join(folder,name+'.png'),new Uint8Array(await png.arrayBuffer()));
}
console.log(path.join(output,'Africa-clarified-extension.xlsx'));

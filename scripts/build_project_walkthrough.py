import ast,json,hashlib
from pathlib import Path
flows=[
('Week 1 · PEP baseline','Establish a traceable retrieval pipeline with a known reference.','Specialized PEP baseline; canonical fallback and reference data are explicit assistance.','python agent.py --pep 8 --output-dir runs/new-pep-demo',[
('Read task','agent.py','read_records','CSV records and optional PEP filter','Validate the input before any external call.','Selected records','What value are we trying to repair?'),
('Discover source','agent.py','discover_source','PEP identifier','Search for an official source; the baseline can use its canonical URL fallback.','Source URL','This baseline is not URL-blind general discovery.'),
('Read webpage','agent.py','fetch_source','Selected URL','Use browser retrieval and preserve page evidence.','Source text','A search snippet is not the full source.'),
('Extract value','agent.py','extract_attribute','Source text and requested attribute','Ask Gemini for structured fields and supporting evidence.','Candidate extraction','Extraction is a proposal, not verification.'),
('Verify','agent.py','verify_extraction','Candidate, evidence and reference','Check evidence and reference agreement.','Decision and reasons','A plausible answer may still need review.'),
('Save results','agent.py','save_results','Processed records','Write outcomes and provenance.','Saved results','Explain the source behind the answer.')]),
('Week 2 · Autonomous search','Remove supplied URLs and generate discovery queries.','Researcher-defined tasks and limits remain; generated queries can fail.','python autonomous.py --entity "PEP 703" --attribute title',[
('Accept task','autonomous.py','run','Entity and attribute','Coordinate bounded discovery without a supplied answer URL.','Run state','Autonomy has a declared scope.'),
('Validate query','autonomous.py','validate_query','Generated query','Reject unsupported query syntax and unsafe assumptions.','Validated query','Gemini plans; the code enforces constraints.'),
('Retrieve','autonomous.py','Retriever','Observed source URL','Apply public-address and retrieval safeguards.','Page text or failure','A returned link does not guarantee access.'),
('Ground candidate','autonomous.py','supported_claim','Claim and page text','Check literal support and entity context.','Support assessment','Quoted text can still refer to the wrong fact.')]),
('Week 2 · Multi-source evaluation','Compare evidence and measure failures independently.','Agreement is not independent corroboration when sources duplicate each other.','python multisource.py --entity "PEP 703" --attribute title --provider brave',[
('Collect sources','multisource.py','run','Entity, attribute and providers','Retrieve and extract from multiple sources within limits.','Source claims','Separate search failures from extraction failures.'),
('Compare claims','multisource.py','compare','Grounded source claims','Identify matching and conflicting candidates.','Comparison decision','Correct candidates can remain unaccepted.'),
('Evaluate','evaluate.py',None,'Fixed benchmark and saved outputs','Measure correctness, success, time and usage under declared conditions.','Benchmark report','Evaluation answers must remain separate from agent inputs.')]),
('Week 3 · Structured DOT','Retrieve exact contextual records from public structured data.','DOT-specific schema knowledge; successful workflow uses no Gemini. Socrata is not a general search engine.','python retrieve_record.py --record-id airfare-01 --provider socrata',[
('Select observation','retrieve_record.py','main','Blinded task record','Select one observation and provider.','Run request','The answer key is not an agent input.'),
('Discover dataset','structured_retrieval.py','run','Task and discovery service','Locate and inspect candidate structured datasets.','Metadata and records','Search providers and a data catalog are different services.'),
('Check schema','structured_retrieval.py','valid_schema','Dataset metadata','Check whether required fields exist.','Schema eligibility','Airport pairs and city markets are not interchangeable.'),
('Query record','structured_retrieval.py','row_query','Market IDs, year and quarter','Construct the contextual record query.','Record selection','Exact reporting period matters.'),
('Check context','structured_retrieval.py','context_valid','Returned row and task','Match market, period and requested field context.','Eligible value','Daily passenger averages can contain decimals.'),
('Verify sources','structured_retrieval.py','verify','Eligible source records','Apply provenance/conflict rules.','Accept or unresolved','24/24 in this benchmark does not mean universal accuracy.')]),
('Current · Commercial aviation','Discover historical commercial policy evidence.','Latest paired US–South Africa trial produced zero verified events. Final CSV and country/topic evaluation remain incomplete.','python aviation_agent.py --tasks examples/aviation-regulations/commercial-tasks.json --task-id ZAF-us_bilateral_air_services --output runs/new-aviation-demo',[
('Define task','aviation_agent.py','Task','Country, topic and historical window','Validate scope without source URLs or reference answers.','Bounded task','Commercial scope differs from general technical regulation.'),
('Generate queries','aviation_agent.py','make_plan','Task only','Generate complementary queries using Gemini.','Search queries','Do not insert known answers into discovery.'),
('Select and navigate','aviation_selection.py','navigation_fallback','Observed candidates, labels and access history','Retain useful navigation leads and downrank failed routes.','Bounded source queue','Official does not automatically mean relevant.'),
('Download and preserve','business_agent.py','BusinessRetriever','Observed URL','Save completed response bytes before parsing through the caller callback.','Evidence, hash and text or failure','READ_FAILED means download succeeded but parsing failed.'),
('Screen counterpart','commercial_aviation.py','explicit_counterpart_mismatch','Document text and task','Check narrow explicit party clauses.','Mismatch or unresolved','South Africa–Namibia cannot answer a US bilateral task.'),
('Assess evidence','commercial_aviation.py','assess_commercial','Proposed event and selected source passages','Check scope, grounded passages and date conditions.','Review flags','Planned signature is not entry into force.'),
('Human review','aviation_review_server.py','save_submission','Explicit reviewer decisions','Save validated labels, backups and UTC audit records.','Human labels','Human corrections are not original machine performance.')]),
('Current · Optional OCR screening','Read a bounded subset of otherwise unreadable PDFs.','Opt-in screening only; not automatic OCR-to-event acceptance. Latest live run did not trigger OCR.','python optional_pdf_ocr.py --source runs/parliament-pdf-diagnosis-20261111/parliament-1.pdf --output runs/new-ocr-demo',[
('Render and OCR','optional_pdf_ocr.py','evaluate_ocr','Preserved PDF','Use local Poppler/Tesseract under page, pixel and time limits.','OCR text and manifest','Missing tools produce UNAVAILABLE, not success.'),
('Record coverage','optional_pdf_ocr.py','evaluate_ocr','Processed pages and source hash','Record pages processed, total pages, engine and review flags.','Partial/full page coverage','Three of 29 pages is not complete document review.'),
('Screen and review','commercial_aviation.py','explicit_counterpart_mismatch','OCR text','Propose scope exclusion or retain review requirements.','Proposed decision','OCR can corrupt country names and dates.')])]
files=['agent.py','autonomous.py','search_providers.py','multisource.py','evaluate.py','evaluation_report.py','prepare_business_data.py','retrieve_record.py','structured_retrieval.py','evaluate_business.py','business_agent.py','business_documents.py','aviation_agent.py','aviation_selection.py','staged_retrieval.py','commercial_aviation.py','aviation_verification.py','aviation_triage.py','aviation_attachments.py','optional_pdf_ocr.py','aviation_review_server.py']
functions=[]
for file in files:
 text=Path(file).read_text();lines=text.splitlines();tree=ast.parse(text)
 for node in tree.body:
  if isinstance(node,(ast.FunctionDef,ast.ClassDef)):
   functions.append(dict(file=file,name=node.name,line=node.lineno,doc=ast.get_docstring(node) or 'Read the code and the stage explanation for this implementation.',code='\n'.join(lines[node.lineno-1:node.end_lineno]),sha256=hashlib.sha256(text.encode()).hexdigest()))
data=[]
for title,goal,limit,command,stages in flows:
 ss=[]
 for label,file,name,inp,action,out,say in stages:
  found=next((i for i,f in enumerate(functions) if f['file']==file and f['name']==name),None)
  if name:assert found is not None,(file,name)
  ss.append(dict(label=label,file=file,function=name,input=inp,action=action,output=out,say=say,code_index=found))
 data.append(dict(title=title,goal=goal,limit=limit,command=command,stages=ss))
template=Path('docs/project-walkthrough/template.html').read_text()
payload=json.dumps({'flows':data,'functions':functions}).replace('</','<\\/')
Path('docs/project-walkthrough/index.html').write_text(template.replace('__DATA__',payload))

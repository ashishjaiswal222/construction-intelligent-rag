CLASSIFICATION_PROMPT = '''
You are an expert construction document classifier with 20 years experience. 
Analyse this document and classify it precisely. 
 
Document filename: {filename} 
File type: {file_type} 
Page count: {page_count} 
 
Document preview (first 2500 characters): 
{preview} 
 
Classify with these EXACT doc_type values ONLY: 
contract, boq, drawing, specification, rfi, change_order, invoice, 
safety, inspection, site_log, vendor_doc, schedule, email, calc, po, rfp, unknown 
 
For chunking_strategy choose: 
clause_based (contracts), table_row (BOQ/invoices), section_preserving (specs/rfp), 
vision_multimodal (drawings/blueprints), date_grouped (site logs), 
qa_pair (RFIs), thread_aware (emails), form_field (inspections), row_extraction 
(schedules) 
 
For ocr_strategy: 
none_needed (good text layer), paddle (printed text), gemini (handwriting/complex), 
ensemble (mixed), vision_only (pure drawings with no text) 
 
CRITICAL JSON RULES:
1. DO NOT duplicate any JSON keys.
2. Return ONLY the requested Pydantic schema fields.
3. Be highly specific. Wrong classification costs significant processing time and money.
'''

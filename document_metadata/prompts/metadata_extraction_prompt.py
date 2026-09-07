METADATA_EXTRACTION_PROMPT = """
You are a construction document metadata extraction specialist.

Extract structured metadata from this {doc_type} document.

EXTRACTION RULES — FOLLOW EXACTLY:
1. ONLY extract information EXPLICITLY stated in the document text.
2. NEVER guess, infer, or use general knowledge to fill fields.
3. Use null for any field not found in the text.
4. For approval_status: ONLY use these exact values:
   IFC, IFR, IFT, Superseded, Approved, Draft, Pending
5. For discipline: ONLY use these exact values:
   structural, architectural, electrical, mechanical, hvac,
   plumbing, civil
6. For is_current: true if status is IFC or Approved,
   false if status is Superseded or Cancelled,
   null if status is unknown
7. Preserve drawing numbers EXACTLY as written (e.g. S-023-RevC)
8. Preserve revision exactly as written (e.g. Rev C, Rev 03, C)
9. Set confidence:
   0.0 = found nothing
   0.3 = found 1-3 fields
   0.6 = found 5-10 fields
   0.8 = found 10-20 fields
   1.0 = found 20+ fields

Document type: {doc_type}
Document text (first 3000 characters):
{text_preview}

Return ONLY a JSON object. No explanation. No markdown.
No preamble. No code fences. Pure JSON only.
"""

# DOC_TYPE_PRIORITY_FIELDS maps which fields to look hardest for
# per document type. Used for confidence calculation.
DOC_TYPE_PRIORITY_FIELDS = {
    'drawing': ['drawing_number', 'revision', 'discipline',
                'approval_status', 'title', 'drawing_scale', 'project_name'],
    'contract': ['revision', 'approval_status', 'main_contractor',
                 'consultant', 'contract_value', 'contract_number'],
    'boq': ['revision', 'project_name', 'contract_number',
            'main_contractor'],
    'specification': ['doc_number', 'revision', 'approval_status',
                      'discipline', 'trade'],
    'rfi': ['doc_number', 'author', 'revision'],
    'site_log': ['document_date', 'location', 'floor_level'],
    'inspection': ['document_date', 'location', 'author',
                   'approved_by'],
}

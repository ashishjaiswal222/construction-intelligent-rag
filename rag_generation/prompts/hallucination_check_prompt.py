HALLUCINATION_CHECK_PROMPT = """
You are a construction document grounding verifier.

USER QUESTION:
{user_query}

GENERATED ANSWER:
{answer}

SOURCE DOCUMENTS USED:
{context}

TASK:
Check whether every factual claim in the GENERATED ANSWER
is directly supported by the SOURCE DOCUMENTS.

A claim is UNGROUNDED if:
- It uses specific numbers, dates, dimensions, or strengths
  not present in the sources.
- It references a document, drawing, or clause not in the sources.
- It draws a conclusion that requires knowledge beyond the sources.

A claim is GROUNDED if:
- It quotes or paraphrases information explicitly in the sources.
- It is a direct logical consequence of what is in the sources.
- It is a statement about absence of information (e.g. "the
  documents do not specify this").

Return JSON only:
{{
  "is_grounded": true,
  "ungrounded_claims": [],
  "warning": null
}}

If ungrounded:
{{
  "is_grounded": false,
  "ungrounded_claims": ["The answer states X but no source mentions X"],
  "warning": "This answer may contain information not found in the provided documents."
}}
"""

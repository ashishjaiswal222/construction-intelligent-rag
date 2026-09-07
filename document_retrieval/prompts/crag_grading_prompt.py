CRAG_GRADING_PROMPT = """
You are a construction document relevance grader.
Does each of the following document extracts directly answer or inform the query?

Query: {query}

Extracts:
{extracts}

Grade strictly. A chunk is relevant ONLY if it contains
information that directly helps answer the query.
Tangentially related content is NOT relevant.

Return JSON only containing a list of grades for each chunk_id. 
No explanation. No markdown.
"""

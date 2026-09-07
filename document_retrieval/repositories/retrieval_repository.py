from document_retrieval.schemas.retrieval_result import RetrievedChunk

class RetrievalRepository:
    def get_parent_chunk(self, chunk_id: str) -> RetrievedChunk | None:
        from django.db import connection
        with connection.cursor() as c:
            c.execute("""
                SELECT dc2.id, dc2.content, dc2.chunk_type,
                       dc2.metadata, dc2.document_id, dc2.is_current,
                       dc2.doc_type, dc2.revision
                FROM document_chunk dc1
                JOIN document_chunk dc2
                  ON dc2.document_id = dc1.document_id
                  AND dc2.chunk_index = dc1.chunk_index - 1
                WHERE dc1.id = %s
                  AND dc2.chunk_type = 'contract_clause'
                LIMIT 1
            """, [chunk_id])
            row = c.fetchone()
        
        if not row:
            return None
            
        meta = row[3] or {}
        return RetrievedChunk(
            chunk_id=str(row[0]),
            content=row[1],
            chunk_type=row[2],
            document_id=str(row[4]),
            is_current=bool(row[5]),
            doc_type=row[6] or '',
            revision=row[7] or '',
            project_id=meta.get('project_id', ''),
            filename=meta.get('filename', ''),
            drawing_number=meta.get('drawing_number'),
            clause_number=meta.get('clause_number'),
            page_number=meta.get('page_number'),
            score=0.0,
        )

    def get_chunks_by_ids(
        self, 
        chunk_ids: list[str], 
        filters: "QueryFilters" = None
    ) -> list[RetrievedChunk]:
        """
        Fetch chunks by their UUIDs. Applies SQL filtering for performance.
        """
        if not chunk_ids:
            return []
            
        from django.db import connection
        
        # Build filter logic
        where_clauses = ["id IN %s"]
        params = [tuple(chunk_ids)]
        
        if filters:
            if filters.project_id:
                # project_id is stored in JSON metadata
                where_clauses.append("metadata->>'project_id' = %s")
                params.append(filters.project_id)
            if filters.doc_type:
                where_clauses.append("doc_type = %s")
                params.append(filters.doc_type)
            
            is_current = filters.is_current if filters.is_current is not None else True
            where_clauses.append("is_current = %s")
            params.append(is_current)
            
        where_sql = " AND ".join(where_clauses)
        
        with connection.cursor() as c:
            c.execute(f"""
                SELECT id, content, chunk_type,
                       metadata, document_id, is_current,
                       doc_type, revision
                FROM document_chunk
                WHERE {where_sql}
            """, params)
            rows = c.fetchall()
            
        chunks = []
        for row in rows:
            meta = row[3] or {}
            chunks.append(RetrievedChunk(
                chunk_id=str(row[0]),
                content=row[1],
                chunk_type=row[2],
                document_id=str(row[4]),
                is_current=bool(row[5]),
                doc_type=row[6] or '',
                revision=row[7] or '',
                project_id=meta.get('project_id', ''),
                filename=meta.get('filename', ''),
                drawing_number=meta.get('drawing_number'),
                clause_number=meta.get('clause_number'),
                page_number=meta.get('page_number'),
                score=0.0,
            ))
        return chunks

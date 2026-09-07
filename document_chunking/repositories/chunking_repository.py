import json
from django.db import connection
from document_chunking.models.chunking_job import ChunkingJob
from document_chunking.models.document_chunk import DocumentChunk
from document_chunking.schemas.chunk_result import ChunkResult
from django.db.models import F

class ChunkingRepository:
    def get_document_context(self, document_id: str) -> dict:
        query = """
            SELECT d.id as document_id, d.doc_type, d.project_id, d.filename,
                   '' as revision, d.language
            FROM document_records d
            LEFT JOIN document_processing_processingjob j ON j.document_id = d.id
            WHERE d.id = %s
        """
        with connection.cursor() as cursor:
            cursor.execute(query, [document_id])
            row = cursor.fetchone()
            if not row:
                return {}
            
            return {
                'document_id': str(row[0]),
                'doc_type': row[1] or '',
                'project_id': str(row[2]) if row[2] else '',
                'filename': row[3] or '',
                'revision': row[4] or '',
                'is_current': True, # Overwritten by strategy logic if needed
                'language': row[5] or 'en'
            }

    def get_refined_pages(self, document_id: str) -> list[dict]:
        query = """
            SELECT DISTINCT ON (p.id) p.id as page_id, p.page_number, r.cleaned_text, d.doc_type,
                   r.passed_quality_gate, r.needs_human_review,
                   r.refinement_level, r.layers_applied
            FROM document_processing_page p
            JOIN document_processing_processingjob j ON p.processing_job_id = j.id
            JOIN document_records d ON j.document_id = d.id
            JOIN refined_content r ON r.page_id = p.id
            WHERE j.document_id = %s
              AND j.id = (
                  SELECT id FROM document_processing_processingjob 
                  WHERE document_id = d.id 
                  ORDER BY started_at DESC LIMIT 1
              )
              AND p.status = 'COMPLETED'
              AND r.passed_quality_gate = true
            ORDER BY p.id, r.created_at DESC
        """
        with connection.cursor() as cursor:
            cursor.execute(query, [document_id])
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Convert UUIDs to strings
        for row in results:
            row['page_id'] = str(row['page_id'])
            
        return results

    def get_extracted_tables(self, page_id: str) -> list[dict]:
        query = """
            SELECT raw_data FROM document_processing_extractedcontent
            WHERE page_id = %s AND content_type = 'TABLE'
        """
        with connection.cursor() as cursor:
            cursor.execute(query, [page_id])
            results = []
            for row in cursor.fetchall():
                if row[0]:
                    try:
                        results.append(json.loads(row[0]) if isinstance(row[0], str) else row[0])
                    except json.JSONDecodeError:
                        pass
            return results

    def get_drawing_data(self, page_id: str) -> dict | None:
        query = """
            SELECT raw_data FROM document_processing_extractedcontent
            WHERE page_id = %s AND content_type = 'DRAWING'
        """
        with connection.cursor() as cursor:
            cursor.execute(query, [page_id])
            row = cursor.fetchone()
            if row and row[0]:
                try:
                    return json.loads(row[0]) if isinstance(row[0], str) else row[0]
                except json.JSONDecodeError:
                    pass
        return None

    def create_chunking_job(self, document_id: str, doc_type: str) -> ChunkingJob:
        from django.utils import timezone
        return ChunkingJob.objects.create(
            document_id=document_id,
            doc_type=doc_type,
            status=ChunkingJob.Status.PROCESSING,
            started_at=timezone.now()
        )

    def save_chunks(self, chunks: list[ChunkResult], job: ChunkingJob, document_id: str, page_id: str) -> int:
        db_chunks = [
            DocumentChunk(
                document_id=document_id,
                chunking_job=job,
                page_id=page_id,
                chunk_index=chunk.chunk_index,
                chunk_type=chunk.chunk_type,
                content=chunk.content,
                metadata=chunk.metadata,
                char_count=chunk.char_count,
                word_count=chunk.word_count,
                strategy_used=chunk.strategy_used,
                is_current=chunk.metadata.get('is_current', True),
                doc_type=chunk.metadata.get('doc_type', ''),
                revision=chunk.metadata.get('revision', '')
            )
            for chunk in chunks
        ]
        DocumentChunk.objects.bulk_create(db_chunks, batch_size=500)
        return len(db_chunks)

    def update_job_progress(self, job_id: str, chunked_pages: int = 0, failed_pages: int = 0,
                            total_chunks: int = 0, strategy_breakdown: dict = None) -> None:
        # Atomic update for counts
        updates = {}
        if chunked_pages > 0:
            updates['chunked_pages'] = F('chunked_pages') + chunked_pages
        if failed_pages > 0:
            updates['failed_pages'] = F('failed_pages') + failed_pages
        if total_chunks > 0:
            updates['total_chunks'] = F('total_chunks') + total_chunks
            
        if updates:
            ChunkingJob.objects.filter(id=job_id).update(**updates)
            
        # For strategy breakdown, we cannot easily do atomic jsonb append without custom SQL
        # So we update it in the aggregate task fully
        pass

    def complete_job(self, job_id: str, status: str, total_chunks: int, strategy_breakdown: dict) -> None:
        from django.utils import timezone
        ChunkingJob.objects.filter(id=job_id).update(
            status=status,
            total_chunks=total_chunks,
            strategy_breakdown=strategy_breakdown,
            completed_at=timezone.now()
        )

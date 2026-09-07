from typing import Optional, List, Dict, Any
from django.db import connection
from document_indexing.models.indexing_record import IndexingRecord

class IndexingRepository:
    def get_chunks_for_document(self, document_id: str) -> List[Dict[str, Any]]:
        query = """
            SELECT dc.id, dc.content as chunk_text, dc.chunk_index as chunk_sequence,
                   dc.chunk_type, COUNT(*) OVER() as total_chunks
            FROM document_chunk dc
            WHERE dc.document_id = %s
              AND dc.is_current = True
            ORDER BY dc.chunk_index ASC
        """
        with connection.cursor() as cursor:
            cursor.execute(query, [document_id])
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_metadata_for_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        query = """
            SELECT dm.title, dm.doc_number, dm.revision,
                   dm.is_current, dm.approval_status,
                   dr.project_id, dm.project_name, dm.project_phase,
                   dm.building, dm.floor_level, dm.zone,
                   dm.discipline, dm.trade, dm.drawing_number,
                   dm.main_contractor, dm.author,
                   dm.metadata_confidence
            FROM document_metadata dm
            JOIN document_records dr ON dr.id = dm.document_id
            WHERE dm.document_id = %s
        """
        with connection.cursor() as cursor:
            cursor.execute(query, [document_id])
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                return dict(zip(columns, row))
            return None

    def get_doc_type(self, document_id: str) -> str:
        query = """
            SELECT doc_type FROM document_records
            WHERE id = %s
        """
        with connection.cursor() as cursor:
            cursor.execute(query, [document_id])
            row = cursor.fetchone()
            return row[0] if row else 'unknown'

    def save_indexing_record(
        self,
        document_id: str,
        status: str,
        chunks_indexed: int,
        chunks_failed: int,
        had_version_update: bool,
        embedding_model: str,
        avg_tokens_per_chunk: float,
        processing_ms: int,
        rate_limit_waits: int,
        error_message: str = '',
    ) -> IndexingRecord:
        record, created = IndexingRecord.objects.update_or_create(
            document_id=document_id,
            defaults={
                'status': status,
                'collection_name': 'construction_docs',
                'chunks_indexed': chunks_indexed,
                'chunks_failed': chunks_failed,
                'had_version_update': had_version_update,
                'embedding_model': embedding_model,
                'avg_tokens_per_chunk': avg_tokens_per_chunk,
                'processing_ms': processing_ms,
                'rate_limit_waits': rate_limit_waits,
                'error_message': error_message,
            }
        )
        return record

    def mark_status(self, document_id: str, status: str) -> None:
        IndexingRecord.objects.filter(document_id=document_id).update(status=status)

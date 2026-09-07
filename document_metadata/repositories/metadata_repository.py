from django.db import connection
from document_metadata.models.document_metadata import DocumentMetadata
from document_metadata.schemas.extracted_metadata import ExtractedMetadata
import json

class MetadataRepository:

    def get_document_context(self, document_id: str) -> dict:
        query = """
            SELECT d.id, d.doc_type, d.project_id, d.filename,
                   d.language, d.has_images, d.has_tables,
                   d.has_drawings, d.has_handwriting
            FROM document_records d
            WHERE d.id = %s
        """
        with connection.cursor() as cursor:
            cursor.execute(query, [document_id])
            row = cursor.fetchone()
            if not row:
                return {}
            
            columns = [col[0] for col in cursor.description]
            return dict(zip(columns, row))

    def get_cleaned_text(self, document_id: str) -> str:
        query = """
            SELECT string_agg(rc.cleaned_text, ' ' ORDER BY p.page_number)
            FROM document_processing_page p
            JOIN document_processing_processingjob j
              ON p.processing_job_id = j.id
            JOIN refined_content rc
              ON rc.page_id = p.id
            WHERE j.document_id = %s
              AND p.status = 'COMPLETED'
              AND rc.passed_quality_gate = true
        """
        with connection.cursor() as cursor:
            cursor.execute(query, [document_id])
            row = cursor.fetchone()
            return row[0] if row and row[0] else ""

    def find_current_revision(self, drawing_number: str, project_id: str, exclude_document_id: str) -> dict | None:
        qs = DocumentMetadata.objects.filter(
            drawing_number=drawing_number,
            project_id=project_id,
            is_current=True
        ).exclude(document_id=exclude_document_id).first()
        
        if qs:
            return {'document_id': str(qs.document_id)}
        return None

    def mark_superseded(self, document_id: str, superseded_by_id: str) -> None:
        DocumentMetadata.objects.filter(document_id=document_id).update(
            is_current=False,
            superseded_by_id=superseded_by_id
        )

    def set_is_current(self, document_id: str, is_current: bool) -> None:
        DocumentMetadata.objects.filter(document_id=document_id).update(is_current=is_current)

    def save_metadata(self, document_id: str, extracted: ExtractedMetadata, language: str) -> DocumentMetadata:
        update_defaults = extracted.model_dump(exclude_unset=True, exclude_none=True)
        # Handle parsed dates separately if needed, for now just use as strings/dates
        
        # Determine is_current (default True)
        if 'is_current' not in update_defaults:
            update_defaults['is_current'] = True
            
        update_defaults.pop('confidence', None)
        update_defaults['metadata_confidence'] = extracted.confidence

        obj, created = DocumentMetadata.objects.update_or_create(
            document_id=document_id,
            defaults=update_defaults
        )
        return obj

    def update_chunk_metadata(self, document_id: str, is_current: bool) -> None:
        query = """
            UPDATE document_chunk
            SET is_current = %s
            WHERE document_id = %s
        """
        with connection.cursor() as cursor:
            cursor.execute(query, [is_current, document_id])

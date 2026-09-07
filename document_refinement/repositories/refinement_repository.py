from uuid import UUID
from typing import List, Dict, Any, Optional
from django.db import connection
from document_refinement.models import RefinedContent
from document_refinement.schemas.refinement_result import RefinementResult

class RefinementRepository:
    def get_pages_for_document(self, document_id: UUID) -> List[Dict[str, Any]]:
        """
        Gets all pages for a document that are COMPLETED and have a refinement_level.
        Since we cannot import from document_processing, we use raw SQL to fetch from its tables.
        """
        query = """
            SELECT p.id, p.page_number, p.refinement_level, p.layers_to_run, o.raw_text, o.strategy_used, d.doc_type
            FROM document_processing_page p
            JOIN document_processing_ocrresult o ON p.id = o.page_id
            JOIN document_processing_processingjob j ON p.processing_job_id = j.id
            JOIN document_records d ON j.document_id = d.id
            WHERE d.id = %s AND p.status = 'COMPLETED'
        """
        with connection.cursor() as cursor:
            cursor.execute(query, [str(document_id)])
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_page_data(self, page_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Gets specific page data by page_id using raw SQL.
        """
        query = """
            SELECT p.id, p.page_number, p.refinement_level, p.layers_to_run, o.raw_text, o.strategy_used, d.doc_type
            FROM document_processing_page p
            JOIN document_processing_ocrresult o ON p.id = o.page_id
            JOIN document_processing_processingjob j ON p.processing_job_id = j.id
            JOIN document_records d ON j.document_id = d.id
            WHERE p.id = %s AND p.status = 'COMPLETED'
        """
        with connection.cursor() as cursor:
            cursor.execute(query, [str(page_id)])
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                return dict(zip(columns, row))
        return None

    def save_refined_content(self, result: RefinementResult) -> RefinedContent:
        obj, created = RefinedContent.objects.update_or_create(
            page_id=result.page_id,
            defaults={
                'raw_text': result.raw_text,
                'cleaned_text': result.cleaned_text,
                'refinement_level': result.refinement_level,
                'layers_applied': result.layers_applied,
                'quality_before': result.quality_before,
                'quality_after': result.quality_after,
                'quality_delta': result.quality_delta,
                'semantic_validation_used': result.semantic_validation_used,
                'passed_quality_gate': result.passed_quality_gate,
                'needs_human_review': result.needs_human_review,
                'refinement_flags': result.refinement_flags,
                'processing_ms': result.processing_ms
            }
        )
        return obj

import time
import os
import logging
from celery import shared_task
from django.db import transaction
from document_metadata.repositories.metadata_repository import MetadataRepository
from document_metadata.services.language_detector import LanguageDetector
from document_metadata.services.metadata_extractor import MetadataExtractor
from document_metadata.services.version_chain_manager import VersionChainManager
from document_metadata.signals import metadata_extracted
from document_metadata.schemas.extracted_metadata import ExtractedMetadata

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60, rate_limit='15/m')
def extract_metadata_task(self, document_id: str):
    """
    Triggered by chunking_completed signal.
    Extracts metadata, updates version chain, fires signal.
    """
    start = time.time()
    repo = MetadataRepository()
    
    try:
        # 1. Load document context
        doc_context = repo.get_document_context(document_id)
        if not doc_context:
            logger.warning(f"No document context found for {document_id}")
            metadata_extracted.send(
                sender=None,
                document_id=document_id,
                metadata_confidence=0.0,
                is_current=True,
                has_version_chain_update=False
            )
            return

        doc_type = doc_context.get('doc_type', 'unknown')
        
        # 2. Load full concatenated cleaned_text
        cleaned_text = repo.get_cleaned_text(document_id)
        if not cleaned_text:
            logger.warning(f"No cleaned text found for {document_id}")
            metadata_extracted.send(
                sender=None,
                document_id=document_id,
                metadata_confidence=0.0,
                is_current=True,
                has_version_chain_update=False
            )
            return

        # 3. Detect language
        lang = LanguageDetector().detect(cleaned_text)

        # 4. Extract metadata
        extractor = MetadataExtractor(os.environ.get('GROQ_API_KEY', ''))
        metadata = extractor.extract(cleaned_text, doc_type, document_id)

        # 5. Version chain update
        version_chain_manager = VersionChainManager(repo)
        
        with transaction.atomic():
            has_update = False
            if metadata.drawing_number and metadata.project_id:
                has_update = version_chain_manager.update_chain(
                    document_id=document_id,
                    drawing_number=metadata.drawing_number,
                    project_id=metadata.project_id or doc_context.get('project_id', ''),
                    new_revision=metadata.revision or '',
                )
            
            # Determine is_current
            is_current = True  # default
            if metadata.approval_status == 'Superseded':
                is_current = False
            elif metadata.is_current is not None:
                is_current = metadata.is_current
            metadata.is_current = is_current

            # Save to DocumentMetadata
            repo.save_metadata(document_id, metadata, lang)

            # Backfill is_current on all chunks
            repo.update_chunk_metadata(document_id, is_current)

        # 6. Fire signal
        metadata_extracted.send(
            sender=None,
            document_id=document_id,
            metadata_confidence=metadata.confidence,
            is_current=is_current,
            has_version_chain_update=has_update,
        )

        # 7. Log structured JSON
        logger.info(
            "metadata_extracted",
            extra={
                'event': 'metadata_extracted',
                'document_id': document_id,
                'doc_type': doc_type,
                'confidence': metadata.confidence,
                'is_current': is_current,
                'has_version_chain_update': has_update,
                'language': lang,
                'drawing_number': metadata.drawing_number,
                'approval_status': metadata.approval_status,
                'processing_ms': int((time.time()-start)*1000),
            }
        )

    except Exception as exc:
        logger.error(f"Metadata extraction failed for {document_id}: {exc}")
        # Only retry on DB or generic exceptions, Groq exception is handled inside extractor
        try:
            jitter = __import__('random').uniform(0, 15)
            self.retry(exc=exc, countdown=60 * (2 ** self.request.retries) + jitter)
        except self.MaxRetriesExceededError:
            metadata_extracted.send(
                sender=None,
                document_id=document_id,
                metadata_confidence=0.0,
                is_current=True,
                has_version_chain_update=False
            )

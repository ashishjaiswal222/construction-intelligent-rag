import logging
import time
from uuid import UUID
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.db import transaction

from document_processing.repositories.processing_repository import ProcessingRepository
from document_processing.repositories.page_repository import PageRepository
from document_processing.repositories.content_repository import ContentRepository

from document_classification.models import Document
from document_processing.models import Page
from document_processing.schemas.page_analysis import PageAnalysisResult
from document_processing.schemas.ocr_result import OCRStrategy, OCRPageResult

from document_processing.services.metadata.page_metadata_extractor import PageMetadataExtractor
from document_processing.services.text_layer.text_layer_extractor import TextLayerExtractor
from document_processing.services.routing.ocr_router import OCRRouter
from document_processing.services.ocr.paddle_service import PaddleService
from document_processing.services.ocr.gemini_vision_service import GeminiVisionService
from document_processing.services.ocr.ensemble_service import EnsembleService
from document_processing.services.ocr.ocr_quality_service import OCRQualityService
from document_processing.services.parsing.content_cleaner import ContentCleaner
from document_processing.services.parsing.engineering_symbol_normalizer import EngineeringSymbolNormalizer
from document_processing.services.table.table_extractor import TableExtractor
from document_processing.services.drawing.drawing_understanding_service import DrawingUnderstandingService
from document_processing.services.routing.refinement_router import route_to_refinement
from document_processing.exceptions import RateLimitException

from document_processing.utils.pdf_utils import extract_page_as_image

class LowQualityException(Exception):
    pass

import random

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=10, default_retry_delay=30, rate_limit='15/m')
def process_page_task(self, job_id: str, page_number: int):
    """
    Handles ONE page independently.
    Steps:
    1. Load ProcessingJob -> get document + doc_type
    2. Create Page record (status=PROCESSING)
    3. Call OCRRouter.route() -> get strategy
    4. Execute appropriate OCR service
    5. Run OCRQualityService.calculate_quality()
    6. If quality < 0.55 -> raise for retry (max 3x)
    7. Run ContentCleaner on raw text
    8. If page has tables -> run TableExtractor
    9. If doc_type == 'drawing' -> run DrawingUnderstandingService
    10. Save OCRResult, ExtractedContent records
    11. Update Page status=COMPLETED
    12. Increment ProcessingJob.processed_pages (atomic F() update)
    """
    proc_repo = ProcessingRepository()
    page_repo = PageRepository()
    content_repo = ContentRepository()
    
    try:
        job = proc_repo.get_job(UUID(job_id))
        if not job:
            logger.info(f"Job {job_id} not found (likely deleted). Aborting task.")
            return f"Job {job_id} not found"
            
        doc = job.document
        doc_type = getattr(doc, 'doc_type', '')
        pdf_path = getattr(doc, 'storage_path', None) or (doc.file.path if hasattr(doc, 'file') and doc.file else getattr(doc, 'file_path', ''))
        
        if not pdf_path:
            logger.info(f"Document for job {job_id} has no valid pdf path (likely deleted). Aborting task.")
            return f"No PDF path for job {job_id}"
        
        # 2. Get or Create Page record
        page = page_repo.get_page_by_number(UUID(job_id), page_number)
        if not page:
            page = page_repo.create_page(UUID(job_id), doc.id, page_number)
        page_repo.update_status(page.id, Page.Status.PROCESSING)
        
        # Extract metadata
        meta_extractor = PageMetadataExtractor()
        page_analysis = meta_extractor.extract(page_number, "", doc_type)
        
        # Check text layer
        text_extractor = TextLayerExtractor()
        text_layer_text, text_layer_quality, text_strategy = text_extractor.extract(pdf_path, page_number)
        
        # 3. Call OCRRouter.route()
        router = OCRRouter()
        strategy = router.route(pdf_path, page_number, doc_type, page_analysis, text_layer_quality)
        
        # Setup image
        image_path = extract_page_as_image(pdf_path, page_number, '/tmp/doc_processing')
        
        # 4. Execute appropriate OCR service
        raw_text = ""
        confidence = 0.0
        processing_time_ms = 0
        
        if strategy == OCRStrategy.TEXT_LAYER:
            raw_text = text_layer_text
            confidence = text_layer_quality
            processing_time_ms = 50 # negligible
        elif strategy == OCRStrategy.GEMINI_VISION:
            gemini_svc = GeminiVisionService()
            raw_text, confidence, processing_time_ms = gemini_svc.extract_text(image_path)
        else: # PADDLE_OCR or ENSEMBLE
            from document_processing.services.parsing.language_detector import LanguageDetector
            lang_det = LanguageDetector()
            detected_lang = lang_det.detect(text_layer_text)
            paddle_lang = 'multilingual' if detected_lang in ['hi', 'mixed'] else 'en'
            
            paddle_svc = PaddleService(lang=paddle_lang)
            gemini_svc = GeminiVisionService()
            ensemble_svc = EnsembleService(paddle_svc, gemini_svc)
            raw_text, confidence, processing_time_ms = ensemble_svc.extract_text(image_path)
            # update strategy if ensemble escalated, but for now just use the routed strategy
            
        # 5. Run OCRQualityService
        quality_svc = OCRQualityService()
        quality_score = quality_svc.calculate_quality(raw_text, confidence)
        
        if quality_score < 0.55:
            # Assume page model has retry_count, or just update via repo if we have it
            # But the user specifically asked for:
            # page.retry_count += 1
            # page_repo.save(page)
            # raise self.retry( ... )
            page.retry_count += 1
            page.save(update_fields=['retry_count'])
            raise self.retry(
                exc=LowQualityException('Quality too low'),
                countdown=30 * (2 ** self.request.retries)
            )
        
        # Structured Logging
        logger.info({
            "event": "ocr_completed",
            "document_id": str(doc.id),
            "page_number": page_number,
            "strategy": strategy,
            "confidence": confidence,
            "latency_ms": processing_time_ms,
            "quality_score": quality_score,
            "char_count": len(raw_text)
        })
        
        print(f"\n" + "="*50)
        print(f"📄 Document ID: {doc.id} | Page: {page_number}")
        print(f"🤖 Strategy Used: {strategy.upper() if isinstance(strategy, str) else strategy}")
        print(f"✅ OCR CONFIDENCE: {confidence * 100:.2f}%")
        print("="*50 + "\n")
        
        # 6. Call refinement router
        route_decision = route_to_refinement(
            raw_text=raw_text,
            strategy=strategy,
            quality_score=quality_score,
            doc_type=doc_type,
        )

        if not route_decision.should_refine:
            # quality too low — flag page, do not proceed
            page_repo.update_status(page.id, Page.Status.NEEDS_REVIEW)
            return f"Page {page_number} flagged for review"

        # Store the route decision on the page record
        Page.objects.filter(id=page.id).update(
            refinement_level=route_decision.refinement_level,
            layers_to_run=route_decision.layers_to_run
        )

        # Initialize defaults
        cleaned_text = raw_text
        hw_segments = []
        stamp_segments = []

        if 'structural_repair' in route_decision.layers_to_run:
            cleaner = ContentCleaner()
            cleaned_text, hw_segments, stamp_segments = cleaner.clean(cleaned_text)
            
        if 'symbol_normalizer' in route_decision.layers_to_run:
            symbol_normalizer = EngineeringSymbolNormalizer()
            cleaned_text = symbol_normalizer.normalize(cleaned_text)
        
        # 8. If page has tables -> run TableExtractor
        seq_idx = 1
        if page_analysis.contains_tables or doc_type == 'boq':
            table_ext = TableExtractor()
            tables = table_ext.extract_tables(image_path, page_number)
            for t in tables:
                content_repo.save_content(
                    page.id, 'TABLE', t.model_dump(), 
                    t.raw_markdown[:500], t.confidence, seq_idx
                )
                seq_idx += 1
                
        # 9. If doc_type == 'drawing' -> run DrawingUnderstandingService
        if doc_type == 'drawing':
            drawing_ext = DrawingUnderstandingService()
            drawing_res = drawing_ext.analyze_drawing(image_path, page_number)
            content_repo.save_content(
                page.id, 'DRAWING', drawing_res.model_dump(),
                drawing_res.description[:500], drawing_res.confidence, seq_idx
            )
            seq_idx += 1
            
        # 10. Save OCRResult
        ocr_res_schema = OCRPageResult(
            page_number=page_number,
            text=raw_text,
            confidence=confidence,
            strategy_used=strategy,
            has_tables=page_analysis.contains_tables,
            has_handwriting=len(hw_segments) > 0,
            handwriting_segments=hw_segments,
            char_count=len(raw_text),
            word_count=len(raw_text.split()),
            processing_ms=processing_time_ms
        )
        page_repo.save_ocr_result(page.id, ocr_res_schema, cleaned_text)
        
        # 11. Update Page status=COMPLETED
        page_repo.update_metrics(page.id, strategy, confidence, processing_time_ms, len(raw_text), quality_score)
        page_repo.update_flags(page.id, {
            'contains_handwriting': len(hw_segments) > 0,
            'contains_stamp': len(stamp_segments) > 0
        })
        page_repo.update_status(page.id, Page.Status.COMPLETED)
        
        # 12. Increment ProcessingJob.processed_pages
        proc_repo.increment_processed_pages(UUID(job_id))
        
        return f"Page {page_number} completed"
        
    except MaxRetriesExceededError:
        try:
            page = page_repo.get_page_by_number(UUID(job_id), page_number)
            if page:
                page.status = Page.Status.FAILED
                page.save(update_fields=['status'])
            proc_repo.increment_failed_pages(UUID(job_id))
        except Exception:
            pass
        return  # do NOT re-raise, let chord continue
    except RateLimitException as exc:
        jitter = random.randint(1, 30)
        logger.warning(f"Rate limit exceeded on page {page_number} for job {job_id}. Pausing {60 + jitter}s.")
        raise self.retry(exc=exc, countdown=60 + jitter)
    except Exception as exc:
        logger.error(f"Error processing page {page_number} for job {job_id}: {str(exc)}")
        retry_delay = self.default_retry_delay * (2 ** self.request.retries) + random.uniform(0, 15)
        raise self.retry(exc=exc, countdown=retry_delay)

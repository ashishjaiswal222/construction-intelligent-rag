import time
import logging
from uuid import UUID
from celery import shared_task

from document_refinement.repositories.refinement_repository import RefinementRepository
from document_refinement.services import (
    Layer1StructuralRepair,
    Layer2OCRCorrection,
    Layer3SymbolNormalizer,
    Layer4AbbreviationExpander,
    Layer5SemanticValidator,
    RefinementOrchestrator
)

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def refine_page_task(self, page_id: str):
    start_time = time.time()
    page_uuid = UUID(page_id)
    
    repo = RefinementRepository()
    
    # 1. Load page data via RefinementRepository
    page_data = repo.get_page_data(page_uuid)
    if not page_data:
        logger.error(f"Page data not found for {page_id}")
        return
        
    raw_text = page_data.get('raw_text', '')
    refinement_level = page_data.get('refinement_level', 'NONE')
    layers_to_run = page_data.get('layers_to_run', [])
    doc_type = page_data.get('doc_type', 'unknown')
    page_number = page_data.get('page_number', 1)
    strategy_used = page_data.get('strategy_used', 'unknown')
    
    # Bypass logic for perfectly extracted text layers
    if strategy_used == 'text_layer':
        logger.info(f"Bypassing Phase 3 refinement for page {page_id} because strategy is 'text_layer'")
        from document_refinement.schemas.refinement_result import RefinementResult
        result = RefinementResult(
            page_id=page_uuid,
            raw_text=raw_text,
            cleaned_text=raw_text, # Exact copy
            refinement_level='NONE',
            layers_applied=[],
            quality_before=1.0,
            quality_after=1.0,
            quality_delta=0.0,
            char_count_before=len(raw_text),
            char_count_after=len(raw_text),
            processing_ms=10,
            semantic_validation_used=False,
            passed_quality_gate=True,
            needs_human_review=False,
            refinement_flags=['bypassed_text_layer']
        )
        refined_content = repo.save_refined_content(result)
        return {
            "page_id": page_id,
            "status": "completed (bypassed)",
            "quality_after": 1.0,
            "needs_review": False
        }
    
    # 2. Setup Providers and Orchestrator
    import os
    from document_refinement.services.providers.groq_provider import GroqRepairProvider
    from document_refinement.services.providers.ollama_provider import OllamaRepairProvider
    
    groq_provider = GroqRepairProvider(api_key=os.environ.get('GROQ_API_KEY', ''))
    ollama_provider = OllamaRepairProvider(
        base_url=os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    )
    
    layer5 = Layer5SemanticValidator(groq_provider, ollama_provider)
    
    orchestrator = RefinementOrchestrator(
        layer1=Layer1StructuralRepair(),
        layer2=Layer2OCRCorrection(),
        layer3=Layer3SymbolNormalizer(),
        layer4=Layer4AbbreviationExpander(),
        layer5=layer5,
        quality_calculator=None # The orchestrator has internal quality calc
    )
    
    # 3. Call refine
    try:
        result = orchestrator.refine(
            page_id=page_uuid,
            raw_text=raw_text,
            refinement_level=refinement_level,
            layers_to_run=layers_to_run,
            doc_type=doc_type,
            page_number=page_number,
            retry_count=self.request.retries
        )
        
        # Update processing time
        result.processing_ms = int((time.time() - start_time) * 1000)
        
        # 4. Save RefinedContent via RefinementRepository
        refined_content = repo.save_refined_content(result)
        
        return {
            "page_id": page_id,
            "status": "completed",
            "quality_after": result.quality_after,
            "needs_review": result.needs_human_review
        }
    except Exception as exc:
        logger.error(f"Refinement failed for page {page_id}: {exc}")
        import random
        jitter = random.uniform(0, 15)
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries) + jitter)

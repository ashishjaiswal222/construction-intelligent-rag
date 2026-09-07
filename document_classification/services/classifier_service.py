import os
from .file_analyzer import FileAnalyzerService
from .heuristic_classifier import HeuristicClassifierService
from shared.llms.factory import LLMFactory
from ..schemas.classification import DocumentClassification
from ..models.audit import LLMUsageLog
from ..models.document import Document

class ClassifierService:
    def __init__(self):
        self.file_analyzer = FileAnalyzerService()
        self.heuristic_classifier = HeuristicClassifierService()
        
        # We can dynamically decide this, but hardcode for Phase 1 or use feature flags
        self.primary_provider = 'groq'
        self.fallback_provider = 'gemini'
        
        self.primary_llm = LLMFactory.get_provider(self.primary_provider)
        self.fallback_llm = LLMFactory.get_provider(self.fallback_provider)

    def process_document(self, document: Document) -> DocumentClassification:
        filename = os.path.basename(document.filename)
        file_ext = os.path.splitext(filename)[1].lower()

        # Step 1: Analyze file
        analysis_result = self.file_analyzer.analyze(document.storage_path)

        # Step 2: Layer 1 - Heuristics
        heuristic_type = self.heuristic_classifier.classify(filename, file_ext, analysis_result.preview_text)

        # Step 3: Layer 2 - Fast LLM
        prompt = self._build_prompt(filename, file_ext, analysis_result.page_count, analysis_result.preview_text)
        
        try:
            try:
                result, usage = self.primary_llm.analyze_structured(prompt, DocumentClassification)
                self._log_usage(document, usage, self.primary_provider)
                
                # Layer 3 - Fallback if uncertain
                if result.confidence < 0.75:
                    try:
                        fallback_result, fallback_usage = self.fallback_llm.analyze_structured(prompt, DocumentClassification)
                        self._log_usage(document, fallback_usage, self.fallback_provider)
                        result = fallback_result
                    except Exception as fallback_e:
                        print(f"Fallback LLM failed (Rate limit/Error: {fallback_e}), continuing with primary result.")
            except Exception as primary_e:
                # Groq/Langchain parsing hallucinated or failed completely (e.g. duplicate JSON keys)
                print(f"Primary LLM failed ({primary_e}), falling back to {self.fallback_provider}...")
                result, usage = self.fallback_llm.analyze_structured(prompt, DocumentClassification)
                self._log_usage(document, usage, self.fallback_provider)
                
            # Override with heuristic if LLM extremely uncertain and heuristic confident
            if result.confidence < 0.70 and heuristic_type:
                result.doc_type = heuristic_type
                result.confidence = 0.65
                
            if analysis_result.has_images and not result.has_images:
                result.has_images = True
                
            return result
            
        except Exception as e:
            raise RuntimeError(f"Classification pipeline failed: {e}")
            
    def _build_prompt(self, filename, file_ext, page_count, preview):
        from ..prompts.classification_prompt import CLASSIFICATION_PROMPT
        return CLASSIFICATION_PROMPT.format(
            filename=filename, 
            file_type=file_ext, 
            page_count=page_count or 0, 
            preview=preview[:2500]
        )
        
    def _log_usage(self, document: Document, usage: dict, provider: str):
        LLMUsageLog.objects.create(
            document=document,
            model_name=usage['model'],
            provider=provider,
            tokens_in=usage['tokens_in'],
            tokens_out=usage['tokens_out'],
            cost=usage['cost'],
            latency_seconds=usage['latency']
        )

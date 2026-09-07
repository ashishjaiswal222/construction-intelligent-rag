from document_metadata.schemas.extracted_metadata import ExtractedMetadata
from document_metadata.prompts.metadata_extraction_prompt import METADATA_EXTRACTION_PROMPT, DOC_TYPE_PRIORITY_FIELDS
import logging
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)

class MetadataExtractor:

    def __init__(self, groq_api_key: str = None):
        # Local Ollama (Primary)
        self.primary_llm = ChatOllama(
            model='llama3.2:latest',
            temperature=0.0,
            base_url='http://localhost:11434'
        )
        
        # Groq (Fallback)
        self.fallback_llm = None
        if groq_api_key:
            model = os.environ.get('GROQ_MODEL', 'qwen/qwen3.8-27b')
            self.fallback_llm = ChatGroq(
                model=model,
                api_key=groq_api_key,
                temperature=0.0,
            )

    def extract(
        self,
        cleaned_text: str,
        doc_type: str,
        document_id: str,
    ) -> ExtractedMetadata:
        """
        Sends first 3000 chars to Ollama. If it fails, falls back to Groq.
        Returns ExtractedMetadata schema.
        NEVER raises — returns confidence=0.0 on any failure.
        """
        text_preview = cleaned_text[:3000]
        prompt = METADATA_EXTRACTION_PROMPT.format(
            doc_type=doc_type,
            text_preview=text_preview,
        )

        try:
            # Try Primary (Local Ollama)
            result = self.primary_llm.with_structured_output(ExtractedMetadata).invoke(prompt)
            result.confidence = self._calculate_confidence(result, doc_type)
            
            # Force fallback if local model couldn't extract anything meaningful
            if result.confidence == 0.0:
                raise ValueError("Local Ollama returned 0.0 confidence (empty extraction).")
                
            return result
        except Exception as e:
            logger.warning(f'Local extraction failed or yielded 0.0 for {document_id}: {e}. Attempting Groq fallback...')
            
            if self.fallback_llm:
                try:
                    # Try Fallback (Groq)
                    result = self.fallback_llm.with_structured_output(ExtractedMetadata).invoke(prompt)
                    result.confidence = self._calculate_confidence(result, doc_type)
                    return result
                except Exception as fallback_e:
                    logger.warning(f'Groq fallback failed for {document_id}: {fallback_e}')
            
            return ExtractedMetadata(confidence=0.0)

    def _calculate_confidence(
        self,
        metadata: ExtractedMetadata,
        doc_type: str,
    ) -> float:
        """
        Calculate confidence based on priority fields for this doc_type.
        Priority fields are more important than generic fields.
        """
        priority = DOC_TYPE_PRIORITY_FIELDS.get(doc_type, [])
        if not priority:
            # Count non-null fields as fallback
            non_null = sum(
                1 for f in metadata.model_fields
                if f != 'confidence' and getattr(metadata, f) is not None
            )
            return min(non_null / 10, 1.0)

        found = sum(
            1 for f in priority
            if getattr(metadata, f, None) is not None
        )
        return round(found / len(priority), 2)

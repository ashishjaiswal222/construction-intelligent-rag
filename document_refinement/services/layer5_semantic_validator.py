import logging
from typing import Tuple
from document_refinement.prompts.semantic_repair_prompt import SEMANTIC_REPAIR_PROMPT
from document_refinement.services.providers.groq_provider import GroqRepairProvider
from document_refinement.services.providers.ollama_provider import OllamaRepairProvider

logger = logging.getLogger(__name__)

class Layer5SemanticValidator:
    def __init__(
        self,
        groq_provider: GroqRepairProvider,
        ollama_provider: OllamaRepairProvider,
    ):
        self.groq = groq_provider
        self.ollama = ollama_provider

    def should_run(self, refinement_level: str, quality: float, doc_type: str,
                   char_count: int, retry_count: int) -> bool:
        """
        Only run if ALL conditions are met.
        """
        HIGH_VALUE = {'contract', 'boq', 'drawing', 'specification'}
        return (
            refinement_level == 'HEAVY'
            and quality < 0.75
            and doc_type in HIGH_VALUE
            and char_count >= 150
            and retry_count == 0    # <- forever-loop killer
        )

    def repair(self, text: str, doc_type: str, page_number: int, refinement_level: str = 'MEDIUM') -> Tuple[str, bool]:
        sample = text[:800]
        prompt = SEMANTIC_REPAIR_PROMPT.format(
            doc_type=doc_type,
            page_number=page_number,
            text_sample=sample,
        )

        repaired = None
        provider_used = None

        # Try Ollama first (Local, no cost, no rate limit)
        try:
            if self.ollama.is_available():
                repaired = self.ollama.repair(prompt)
                provider_used = 'ollama'
        except Exception as e:
            logger.warning(f'Ollama failed for page {page_number}: {e}. Trying Groq fallback.')

        # Groq fallback if Ollama failed
        if repaired is None:
            try:
                repaired = self.groq.repair(prompt, retry_count=0)
                provider_used = 'groq'
            except Exception as e:
                logger.warning(f'Groq also failed for page {page_number}: {e}.')

        # If both failed: return original
        if repaired is None:
            return text, False

        # Hallucination guard: reject if too long
        multiplier = 1.5 if refinement_level == 'HEAVY' else 1.3
        if len(repaired) > len(sample) * multiplier:
            logger.warning(f"Semantic repair rejected: response too long (hallucination risk). Multiplier was {multiplier}x")
            return text, False

        # Replace the snippet in full text
        repaired_text = repaired + text[800:]
        return repaired_text, True

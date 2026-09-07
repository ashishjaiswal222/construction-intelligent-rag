from uuid import UUID
from typing import List

from document_refinement.schemas.refinement_result import RefinementResult
from document_refinement.services.layer1_structural_repair import Layer1StructuralRepair
from document_refinement.services.layer2_ocr_correction import Layer2OCRCorrection
from document_refinement.services.layer3_symbol_normalizer import Layer3SymbolNormalizer
from document_refinement.services.layer4_abbreviation_expander import Layer4AbbreviationExpander
from document_refinement.services.layer5_semantic_validator import Layer5SemanticValidator

class RefinementOrchestrator:

    def __init__(
        self,
        layer1: Layer1StructuralRepair,
        layer2: Layer2OCRCorrection,
        layer3: Layer3SymbolNormalizer,
        layer4: Layer4AbbreviationExpander,
        layer5: Layer5SemanticValidator,
        quality_calculator,
    ):
        self.layer1 = layer1
        self.layer2 = layer2
        self.layer3 = layer3
        self.layer4 = layer4
        self.layer5 = layer5
        self.quality_calculator = quality_calculator

    def refine(
        self,
        page_id: UUID,
        raw_text: str,
        refinement_level: str,   # LIGHT | MEDIUM | HEAVY
        layers_to_run: List[str],
        doc_type: str,
        page_number: int,
        retry_count: int,
    ) -> RefinementResult:

        text = raw_text
        applied = []
        quality_before = self._quality(text)
        flags = self._flags(text)

        try:
            if 'structural_repair' in layers_to_run:
                text, fixes = self.layer1.repair(text)
                if fixes: applied.append('L1:structural_repair')

            if 'ocr_correction' in layers_to_run:
                text, fixes = self.layer2.correct(text)
                if fixes: applied.append('L2:ocr_correction')

            if 'symbol_normalizer' in layers_to_run:
                text, fixes = self.layer3.normalize(text)
                if fixes: applied.append('L3:symbol_normalizer')

            if 'abbreviation_expander' in layers_to_run:
                text, fixes = self.layer4.expand(text)
                if fixes: applied.append('L4:abbreviation_expander')

            semantic_used = False
            if 'semantic_validator' in layers_to_run:
                mid_quality = self._quality(text)
                if self.layer5.should_run(
                    refinement_level, mid_quality, doc_type,
                    len(text), retry_count
                ):
                    text, semantic_used = self.layer5.repair(
                        text, doc_type, page_number, refinement_level
                    )
                    if semantic_used: applied.append('L5:semantic_validator')

        except Exception as e:
            flags.append('refinement_failed')
            # Text stays as whatever it was before the exception

        quality_after = self._quality(text)

        return RefinementResult(
            page_id=page_id,
            raw_text=raw_text,
            cleaned_text=text,
            refinement_level=refinement_level,
            layers_applied=applied,
            quality_before=quality_before,
            quality_after=quality_after,
            quality_delta=quality_after - quality_before,
            char_count_before=len(raw_text),
            char_count_after=len(text),
            processing_ms=0,
            semantic_validation_used=semantic_used if 'semantic_used' in locals() else False,
            passed_quality_gate=quality_after >= 0.65,
            needs_human_review=quality_after < 0.65,
            refinement_flags=flags,
        )

    def _quality(self, text: str) -> float:
        char_count = len(text)
        if char_count == 0: return 0.0
        alpha = sum(c.isalpha() for c in text) / char_count
        symbol = sum(not c.isalnum() and not c.isspace()
                     for c in text) / char_count
        words = len(text.split())
        score = 0.0
        if char_count > 200: score += 0.2
        if 0.4 < alpha < 0.85: score += 0.3
        if symbol < 0.15: score += 0.2
        if words > 20: score += 0.15
        if char_count > 500: score += 0.15
        return min(score, 1.0)

    def _flags(self, text: str) -> List[str]:
        flags = []
        if text.count('[?unclear]') > 3:
            flags.append('multiple_unclear_segments')
        if '[HW:' in text:
            flags.append('contains_handwriting_markers')
        if '[STAMP:' in text:
            flags.append('contains_stamp_markers')
        if len(text) < 100:
            flags.append('very_short_content')
        return flags

from pydantic import BaseModel
from typing import List

class RefinementRouteDecision(BaseModel):
    should_refine: bool
    refinement_level: str   # 'NONE' | 'LIGHT' | 'MEDIUM' | 'HEAVY'
    layers_to_run: List[str]
    reason: str

def route_to_refinement(
    raw_text: str,
    strategy: str,
    quality_score: float,
    doc_type: str,
) -> RefinementRouteDecision:
    if quality_score < 0.60:
        return RefinementRouteDecision(
            should_refine=False,
            refinement_level='NONE',
            layers_to_run=[],
            reason='Quality too low. Flag for human review. Skip refinement.'
        )
    elif strategy == 'TEXT_LAYER':
        return RefinementRouteDecision(
            should_refine=True,
            refinement_level='LIGHT',
            layers_to_run=['structural_repair', 'symbol_normalizer', 'abbreviation_expander'],
            reason='Digital text layer. No OCR errors. Layout + symbols only.'
        )
    elif strategy == 'GEMINI_VISION':
        return RefinementRouteDecision(
            should_refine=True,
            refinement_level='LIGHT',
            layers_to_run=['structural_repair', 'symbol_normalizer', 'abbreviation_expander'],
            reason='Gemini output is clean. No spell correction needed.'
        )
    elif strategy == 'PADDLE_OCR':
        return RefinementRouteDecision(
            should_refine=True,
            refinement_level='MEDIUM',
            layers_to_run=['structural_repair', 'ocr_correction', 'symbol_normalizer', 'abbreviation_expander'],
            reason='PaddleOCR needs character error correction.'
        )
    elif strategy == 'ENSEMBLE':
        return RefinementRouteDecision(
            should_refine=True,
            refinement_level='HEAVY',
            layers_to_run=['structural_repair', 'ocr_correction', 'symbol_normalizer', 'abbreviation_expander', 'semantic_validator'],
            reason='Ensemble path. Full 5-layer pipeline required.'
        )
    else:
        return RefinementRouteDecision(
            should_refine=True,
            refinement_level='MEDIUM',
            layers_to_run=['structural_repair', 'ocr_correction', 'symbol_normalizer', 'abbreviation_expander'],
            reason='Unknown strategy. Apply medium refinement as safe default.'
        )

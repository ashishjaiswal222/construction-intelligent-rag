import logging
from document_chunking.schemas.chunk_result import ChunkResult
from document_chunking.services.strategies.base_strategy import BaseChunkingStrategy
from document_chunking.services.strategies.contract_strategy import ContractChunkingStrategy
from document_chunking.services.strategies.boq_strategy import BOQChunkingStrategy
from document_chunking.services.strategies.specification_strategy import SpecificationChunkingStrategy
from document_chunking.services.strategies.drawing_strategy import DrawingChunkingStrategy
from document_chunking.services.strategies.rfi_strategy import RFIChunkingStrategy
from document_chunking.services.strategies.site_log_strategy import SiteLogChunkingStrategy
from document_chunking.services.strategies.email_strategy import EmailChunkingStrategy
from document_chunking.services.strategies.inspection_strategy import InspectionChunkingStrategy
from document_chunking.services.strategies.engineering_calc_strategy import EngineeringCalcChunkingStrategy
from document_chunking.services.strategies.generic_strategy import GenericChunkingStrategy

logger = logging.getLogger(__name__)

class ChunkingDispatcher:

    STRATEGY_MAP: dict[str, type[BaseChunkingStrategy]] = {
        'contract':    ContractChunkingStrategy,
        'boq':         BOQChunkingStrategy,
        'specification': SpecificationChunkingStrategy,
        'drawing':     DrawingChunkingStrategy,
        'rfi':         RFIChunkingStrategy,
        'site_log':    SiteLogChunkingStrategy,
        'email':       EmailChunkingStrategy,
        'inspection':  InspectionChunkingStrategy,
        'calc':        EngineeringCalcChunkingStrategy,
        'change_order': GenericChunkingStrategy,
        'invoice':     GenericChunkingStrategy,
        'safety':      GenericChunkingStrategy,
        'vendor_doc':  GenericChunkingStrategy,
        'schedule':    GenericChunkingStrategy,
        'po':          GenericChunkingStrategy,
        'unknown':     GenericChunkingStrategy,
    }

    def dispatch(
        self,
        doc_type: str,
        cleaned_text: str,
        page_id: str,
        page_number: int,
        document_metadata: dict,
        extracted_data: dict | None = None,
    ) -> list[ChunkResult]:
        strategy_class = self.STRATEGY_MAP.get(
            doc_type, GenericChunkingStrategy
        )
        strategy = strategy_class()
        try:
            chunks = strategy.chunk(
                cleaned_text=cleaned_text,
                page_id=page_id,
                page_number=page_number,
                document_metadata=document_metadata,
                extracted_data=extracted_data,
            )
            # If strategy returned empty list (no pattern found):
            # fall back to generic silently
            if not chunks:
                fallback = GenericChunkingStrategy()
                chunks = fallback.chunk(
                    cleaned_text=cleaned_text,
                    page_id=page_id,
                    page_number=page_number,
                    document_metadata=document_metadata,
                    extracted_data=None,
                )
                for c in chunks:
                    c.metadata['fallback_reason'] = (
                        f'{strategy_class.__name__} returned no chunks'
                    )
            return chunks
        except Exception as e:
            logger.error(
                f'Strategy {strategy_class.__name__} failed '
                f'for page {page_id}: {e}. Using generic fallback.'
            )
            fallback = GenericChunkingStrategy()
            return fallback.chunk(
                cleaned_text=cleaned_text,
                page_id=page_id,
                page_number=page_number,
                document_metadata=document_metadata,
                extracted_data=None,
            )

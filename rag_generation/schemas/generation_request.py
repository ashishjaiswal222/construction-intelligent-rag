from typing import Optional
from pydantic import BaseModel, ConfigDict
from document_retrieval.schemas.retrieval_result import RetrievalResult

class GenerationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    user_query:       str
    project_id:       Optional[str] = None
    retrieval_result: RetrievalResult
    chat_history:     list[dict] = []

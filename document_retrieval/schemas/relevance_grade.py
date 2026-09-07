from pydantic import BaseModel, ConfigDict

class RelevanceGrade(BaseModel):
    model_config = ConfigDict(extra='forbid')
    chunk_id:    str
    is_relevant: bool
    confidence:  float
    reason:      str

class BatchRelevanceGrade(BaseModel):
    model_config = ConfigDict(extra='forbid')
    grades: list[RelevanceGrade]

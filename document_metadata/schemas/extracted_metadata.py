from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

class ExtractedMetadata(BaseModel):
    model_config = ConfigDict(extra='ignore')

    title: Optional[str] = None
    description: Optional[str] = None
    doc_number: Optional[str] = None
    revision: Optional[str] = None
    revision_date: Optional[str] = None
    is_current: Optional[bool] = None
    approval_status: Optional[str] = None
    project_name: Optional[str] = None
    project_id: Optional[str] = None
    project_phase: Optional[str] = None
    contract_number: Optional[str] = None
    wbs_code: Optional[str] = None
    package_code: Optional[str] = None
    location: Optional[str] = None
    building: Optional[str] = None
    floor_level: Optional[str] = None
    zone: Optional[str] = None
    grid_reference: Optional[str] = None
    main_contractor: Optional[str] = None
    sub_contractor: Optional[str] = None
    consultant: Optional[str] = None
    vendor: Optional[str] = None
    author: Optional[str] = None
    approved_by: Optional[str] = None
    drawing_number: Optional[str] = None
    discipline: Optional[str] = None
    drawing_scale: Optional[str] = None
    contract_value: Optional[float] = None
    currency: Optional[str] = None
    document_date: Optional[str] = None
    issue_date: Optional[str] = None
    received_date: Optional[str] = None
    approved_date: Optional[str] = None
    trade: Optional[str] = None
    material_type: Optional[str] = None
    risk_level: Optional[str] = None
    confidence: float = 0.0

    @field_validator('approval_status', mode='before')
    @classmethod
    def validate_approval_status(cls, v):
        allowed = {'IFC', 'IFR', 'IFT', 'Superseded', 'Approved', 'Draft', 'Pending'}
        if v and v not in allowed:
            return None
        return v

    @field_validator('discipline', mode='before')
    @classmethod
    def validate_discipline(cls, v):
        allowed = {'structural', 'architectural', 'electrical', 'mechanical', 'hvac', 'plumbing', 'civil'}
        if v and v.lower() not in allowed:
            return None
        return v.lower() if v else v

    @field_validator('risk_level', mode='before')
    @classmethod
    def validate_risk_level(cls, v):
        allowed = {'high', 'medium', 'low'}
        if v and v.lower() not in allowed:
            return None
        return v.lower() if v else v

    @field_validator('revision_date', 'document_date', 'issue_date', 'received_date', 'approved_date', mode='before')
    @classmethod
    def validate_dates(cls, v):
        if not v:
            return None
        try:
            from dateutil.parser import parse
            parsed_date = parse(str(v))
            return parsed_date.strftime('%Y-%m-%d')
        except Exception:
            return None

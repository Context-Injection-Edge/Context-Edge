from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional
from datetime import datetime

class MetadataPayloadBase(BaseModel):
    cid: str
    metadata: Dict[str, Any]

class MetadataPayloadCreate(MetadataPayloadBase):
    pass

class MetadataPayloadUpdate(MetadataPayloadBase):
    pass

class MetadataPayload(BaseModel):
    id: int
    cid: str
    metadata: Dict[str, Any] = Field(alias="payload_data")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

# Context Store Schemas for Industrial RAG
class AssetMasterData(BaseModel):
    asset_id: str
    location: str
    model_number: str
    safety_rules: Dict[str, Any]

class OperatingThreshold(BaseModel):
    sensor_type: str
    warning_low: float
    warning_high: float
    critical_low: float
    critical_high: float
    unit: str

class RuntimeState(BaseModel):
    production_order_id: str
    current_recipe: str
    time_since_maintenance: int  # hours

class AIModelMetadata(BaseModel):
    version_id: str
    confidence_threshold: float
    model_type: str
    last_updated: datetime
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any
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
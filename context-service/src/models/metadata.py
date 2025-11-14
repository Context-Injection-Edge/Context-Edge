from sqlalchemy import Column, Integer, String, JSON, DateTime
from datetime import datetime
from ..database.database import Base

class MetadataPayload(Base):
    __tablename__ = "metadata_payloads"

    id = Column(Integer, primary_key=True, index=True)
    cid = Column(String, unique=True, index=True, nullable=False)
    payload_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
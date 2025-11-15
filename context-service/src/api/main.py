from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..models.metadata import MetadataPayload
from ..models.schemas import (
    MetadataPayloadCreate, MetadataPayloadUpdate, MetadataPayload as MetadataPayloadSchema,
    AssetMasterData, OperatingThreshold, RuntimeState, AIModelMetadata
)
import redis
import os
import json
import csv
import io
import time
from typing import List, Dict, Any
from datetime import datetime

app = FastAPI(title="Context Edge Service", version="1.0.0", description="Real-Time Ground-Truth Labeling System")

# CORS middleware for UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

redis_client = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True)

@app.get("/context/{cid}")
def get_metadata(cid: str, db: Session = Depends(get_db)):
    # Check Redis cache first
    cached = redis_client.get(f"metadata:{cid}")
    if cached:
        return json.loads(cached)
    
    # Query database
    payload = db.query(MetadataPayload).filter(MetadataPayload.cid == cid).first()
    if not payload:
        raise HTTPException(status_code=404, detail="Metadata not found")
    
    result = {
        "cid": payload.cid,
        "metadata": payload.payload_data,
        "timestamp": payload.updated_at.isoformat()
    }
    
    # Cache result
    redis_client.setex(f"metadata:{cid}", 3600, json.dumps(result))  # 1 hour TTL
    
    return result

@app.post("/context", response_model=MetadataPayloadSchema)
def create_metadata(payload: MetadataPayloadCreate, db: Session = Depends(get_db)):
    db_payload = MetadataPayload(cid=payload.cid, payload_data=payload.metadata)
    db.add(db_payload)
    db.commit()
    db.refresh(db_payload)
    
    # Invalidate cache
    redis_client.delete(f"metadata:{payload.cid}")
    
    return db_payload

@app.put("/context/{cid}", response_model=MetadataPayloadSchema)
def update_metadata(cid: str, payload: MetadataPayloadUpdate, db: Session = Depends(get_db)):
    db_payload = db.query(MetadataPayload).filter(MetadataPayload.cid == cid).first()
    if not db_payload:
        raise HTTPException(status_code=404, detail="Metadata not found")

    db_payload.payload_data = payload.metadata
    db.commit()
    db.refresh(db_payload)
    
    # Invalidate cache
    redis_client.delete(f"metadata:{cid}")
    
    return db_payload

@app.delete("/context/{cid}")
def delete_metadata(cid: str, db: Session = Depends(get_db)):
    db_payload = db.query(MetadataPayload).filter(MetadataPayload.cid == cid).first()
    if not db_payload:
        raise HTTPException(status_code=404, detail="Metadata not found")

    db.delete(db_payload)
    db.commit()

    # Invalidate cache
    redis_client.delete(f"metadata:{cid}")

    return {"message": "Metadata deleted"}

@app.get("/context", response_model=List[MetadataPayloadSchema])
def list_metadata(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all metadata payloads with pagination"""
    payloads = db.query(MetadataPayload).offset(skip).limit(limit).all()
    return payloads

@app.post("/context/bulk-import")
async def bulk_import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Bulk import metadata from CSV file (columns: cid, metadata_json)"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    contents = await file.read()
    csv_reader = csv.DictReader(io.StringIO(contents.decode('utf-8')))

    imported = 0
    errors = []

    for row in csv_reader:
        try:
            cid = row.get('cid', '').strip()
            metadata_json = row.get('metadata_json', '{}').strip()

            if not cid:
                errors.append(f"Skipping row with missing CID")
                continue

            metadata = json.loads(metadata_json)

            # Check if exists, update or create
            existing = db.query(MetadataPayload).filter(MetadataPayload.cid == cid).first()
            if existing:
                existing.payload_data = metadata
                redis_client.delete(f"metadata:{cid}")
            else:
                db_payload = MetadataPayload(cid=cid, payload_data=metadata)
                db.add(db_payload)

            imported += 1
        except Exception as e:
            errors.append(f"Error processing CID {cid}: {str(e)}")

    db.commit()

    return {
        "imported": imported,
        "errors": errors if errors else None,
        "message": f"Successfully imported {imported} metadata payloads"
    }

# Context Store APIs for Industrial RAG

@app.post("/context/assets")
def create_asset(asset: AssetMasterData):
    """Store asset master data in Redis Context Store"""
    key = f"asset:{asset.asset_id}"
    data = asset.model_dump()
    redis_client.set(key, json.dumps(data))
    return {"message": f"Asset {asset.asset_id} stored"}

@app.get("/context/assets/{asset_id}")
def get_asset(asset_id: str):
    """Retrieve asset master data"""
    key = f"asset:{asset_id}"
    data = redis_client.get(key)
    if not data:
        raise HTTPException(status_code=404, detail="Asset not found")
    return json.loads(data)

@app.post("/context/thresholds")
def create_threshold(threshold: OperatingThreshold):
    """Store operating thresholds"""
    key = f"thresholds:{threshold.sensor_type}"
    data = threshold.model_dump()
    redis_client.set(key, json.dumps(data))
    return {"message": f"Threshold for {threshold.sensor_type} stored"}

@app.get("/context/thresholds/{sensor_type}")
def get_threshold(sensor_type: str):
    """Retrieve operating thresholds"""
    key = f"thresholds:{sensor_type}"
    data = redis_client.get(key)
    if not data:
        raise HTTPException(status_code=404, detail="Threshold not found")
    return json.loads(data)

@app.post("/context/runtime")
def update_runtime_state(state: RuntimeState):
    """Update runtime state"""
    key = f"runtime:{state.production_order_id}"
    data = state.model_dump()
    redis_client.set(key, json.dumps(data))
    return {"message": f"Runtime state for order {state.production_order_id} updated"}

@app.get("/context/runtime/{order_id}")
def get_runtime_state(order_id: str):
    """Retrieve runtime state"""
    key = f"runtime:{order_id}"
    data = redis_client.get(key)
    if not data:
        raise HTTPException(status_code=404, detail="Runtime state not found")
    return json.loads(data)

@app.post("/context/models")
def update_model_metadata(metadata: AIModelMetadata):
    """Store AI model metadata"""
    key = f"model:{metadata.version_id}"
    data = metadata.model_dump()
    redis_client.set(key, json.dumps(data))
    return {"message": f"Model metadata for {metadata.version_id} stored"}

@app.get("/context/models/{version_id}")
def get_model_metadata(version_id: str):
    """Retrieve AI model metadata"""
    key = f"model:{version_id}"
    data = redis_client.get(key)
    if not data:
        raise HTTPException(status_code=404, detail="Model metadata not found")
    return json.loads(data)

# Feedback Loop for MLOps
@app.post("/feedback/low-confidence")
def submit_low_confidence_feedback(sensor_data: Dict[str, Any], prediction: Dict[str, Any], cid: str):
    """Collect low-confidence predictions for retraining"""
    feedback_data = {
        "sensor_data": sensor_data,
        "prediction": prediction,
        "cid": cid,
        "timestamp": time.time(),
        "needs_retraining": True
    }

    # Store in Redis for batch processing
    key = f"feedback:{int(time.time())}"
    redis_client.setex(key, 86400 * 7, json.dumps(feedback_data))  # 7 days TTL

    return {"message": "Feedback collected for retraining"}

@app.get("/feedback/batch")
def get_feedback_batch(limit: int = 100):
    """Retrieve batch of feedback data for retraining"""
    # Use SCAN instead of KEYS for production safety
    feedback_keys = []
    cursor = 0
    while True:
        cursor, keys = redis_client.scan(cursor, match="feedback:*", count=limit)
        feedback_keys.extend(keys)
        if cursor == 0 or len(feedback_keys) >= limit:
            break

    feedback_data = []
    for key in feedback_keys[:limit]:
        data = redis_client.get(key)
        if data:
            feedback_data.append(json.loads(data))

    return {"feedback": feedback_data, "count": len(feedback_data)}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        # Check Redis
        redis_client.ping()
        redis_status = "healthy"
    except:
        redis_status = "unhealthy"

    return {
        "status": "healthy",
        "redis": redis_status,
        "version": "1.0.0"
    }
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
import uuid

app = FastAPI(title="Context Edge Data Ingestion", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage configuration
STORAGE_PATH = os.getenv("STORAGE_PATH", "/app/storage/ldos")
Path(STORAGE_PATH).mkdir(parents=True, exist_ok=True)

# In-memory storage for LDO status (in production, use database)
ldo_registry = {}

class LDOStatus(BaseModel):
    id: str
    status: str
    filename: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: str
    size_bytes: Optional[int] = None

@app.get("/")
def root():
    return {
        "service": "Context Edge Data Ingestion",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/ingest/ldo")
async def ingest_ldo(
    video: UploadFile = File(...),
    metadata: str = Form(...)
):
    """
    Upload a Labeled Data Object (LDO)
    - video: Video file (MP4, AVI, etc.)
    - metadata: JSON string containing sensor data and context metadata
    """
    try:
        # Parse metadata
        metadata_dict = json.loads(metadata)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON metadata")

    # Generate unique LDO ID
    ldo_id = f"ldo_{uuid.uuid4().hex[:12]}_{int(datetime.now().timestamp())}"

    # Create LDO directory
    ldo_dir = Path(STORAGE_PATH) / ldo_id
    ldo_dir.mkdir(exist_ok=True)

    # Save video file
    video_path = ldo_dir / f"video{Path(video.filename).suffix}"
    with open(video_path, "wb") as f:
        shutil.copyfileobj(video.file, f)

    # Save metadata
    metadata_path = ldo_dir / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata_dict, f, indent=2)

    # Get file size
    file_size = os.path.getsize(video_path)

    # Register LDO
    ldo_status = LDOStatus(
        id=ldo_id,
        status="ingested",
        filename=video.filename,
        metadata=metadata_dict,
        created_at=datetime.now().isoformat(),
        size_bytes=file_size
    )
    ldo_registry[ldo_id] = ldo_status.dict()

    return {
        "id": ldo_id,
        "status": "ingested",
        "message": f"LDO successfully ingested",
        "size_bytes": file_size
    }

@app.get("/ingest/status/{ldo_id}", response_model=LDOStatus)
def get_ldo_status(ldo_id: str):
    """Get the status of an ingested LDO"""
    if ldo_id not in ldo_registry:
        raise HTTPException(status_code=404, detail="LDO not found")

    return ldo_registry[ldo_id]

@app.get("/ingest/list")
def list_ldos(skip: int = 0, limit: int = 100):
    """List all ingested LDOs"""
    ldos = list(ldo_registry.values())
    return {
        "total": len(ldos),
        "ldos": ldos[skip:skip+limit]
    }

@app.delete("/ingest/{ldo_id}")
def delete_ldo(ldo_id: str):
    """Delete an LDO"""
    if ldo_id not in ldo_registry:
        raise HTTPException(status_code=404, detail="LDO not found")

    # Delete files
    ldo_dir = Path(STORAGE_PATH) / ldo_id
    if ldo_dir.exists():
        shutil.rmtree(ldo_dir)

    # Remove from registry
    del ldo_registry[ldo_id]

    return {"message": f"LDO {ldo_id} deleted"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "storage_path": STORAGE_PATH,
        "total_ldos": len(ldo_registry),
        "version": "1.0.0"
    }
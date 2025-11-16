#!/usr/bin/env python3
"""
Context Edge - Edge Server Main Application
Receives CID from camera devices and orchestrates the fusion process
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
import logging
import httpx
import os
import json

from app.services.context_lookup import ContextLookupService
from app.services.fusion import FusionService
from app.services.ldo_generator import LDOGeneratorService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Context Edge - Edge Server",
    description="Receives CID from cameras, performs fusion, generates LDOs",
    version="0.1.0"
)

# Initialize services
context_service = ContextLookupService()
fusion_service = FusionService()
ldo_service = LDOGeneratorService()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CIDRequest(BaseModel):
    """Request from camera device with CID"""
    cid: str
    camera_id: str
    timestamp: str


class CIDResponse(BaseModel):
    """Response back to camera device"""
    status: str
    message: str
    ldo_id: Optional[str] = None


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "edge-server",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/cid", response_model=CIDResponse)
async def receive_cid(
    cid: str = Form(...),
    device_id: str = Form(...),
    timestamp: str = Form(...),
    video: Optional[UploadFile] = File(None),
    background_tasks: BackgroundTasks = None
):
    """
    Main endpoint: Receives CID + video from edge device

    Flow:
    1. Receive CID + video from edge device
    2. Fetch context from Redis
    3. Read PLC sensor data
    4. Fuse context + sensor data + video (CIM)
    5. Run AI inference
    6. Store video to data-ingestion
    7. Generate and store LDO
    """
    logger.info(f"📥 Received CID: {cid} from device: {device_id}")
    if video:
        logger.info(f"📹 Received video: {video.filename} ({video.size} bytes)")

    try:
        # Step 1: Fetch context metadata from Redis
        logger.info(f"🔍 Looking up context for CID: {cid}")
        context = await context_service.get_context(cid)

        if not context:
            logger.warning(f"⚠️  No context found for CID: {cid}")
            raise HTTPException(
                status_code=404,
                detail=f"Context not found for CID: {cid}"
            )

        logger.info(f"✅ Context found: {context.get('product_id', 'unknown')}")

        # Step 2: Read real-time sensor data from PLC
        logger.info(f"📊 Reading sensor data from device: {device_id}")
        sensor_data = await fusion_service.read_sensor_data(device_id)
        logger.info(f"✅ Sensor data: {sensor_data}")

        # Step 3: Fuse context + sensor data + video (CIM - Patented)
        logger.info(f"🔗 Fusing context + sensor + video (CIM)")
        fused_data = await fusion_service.fuse_data(
            cid=cid,
            context=context,
            sensor_data=sensor_data,
            camera_id=device_id,
            timestamp=timestamp,
            video_file=video.filename if video else None
        )
        logger.info(f"✅ Fusion complete")

        # Step 4: Run AI inference
        logger.info(f"🤖 Running AI inference")
        prediction = await fusion_service.run_inference(fused_data)
        logger.info(f"✅ Prediction: {prediction.get('result')} (confidence: {prediction.get('confidence')})")

        # Step 5: Store video to data-ingestion (if provided)
        video_storage_id = None
        if video:
            logger.info(f"📦 Uploading video to data-ingestion...")
            video_storage_id = await upload_video_to_data_ingestion(cid, video, fused_data, prediction)
            logger.info(f"✅ Video stored: {video_storage_id}")

        # Step 6: Generate and store LDO
        logger.info(f"💾 Generating LDO")
        ldo_id = await ldo_service.create_ldo(
            cid=cid,
            fused_data=fused_data,
            prediction=prediction,
            video_storage_id=video_storage_id
        )
        logger.info(f"✅ LDO created: {ldo_id}")

        return CIDResponse(
            status="success",
            message="LDO generated successfully",
            ldo_id=ldo_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing CID {cid}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal error processing CID: {str(e)}"
        )


async def upload_video_to_data_ingestion(
    cid: str,
    video: UploadFile,
    fused_data: Dict[str, Any],
    prediction: Dict[str, Any]
) -> str:
    """
    Upload video + metadata to data-ingestion service

    Args:
        cid: Context ID
        video: Video file upload
        fused_data: Fused data from CIM
        prediction: AI prediction results

    Returns:
        Storage ID from data-ingestion
    """
    data_ingestion_url = os.getenv("DATA_INGESTION_URL", "http://data-ingestion:8001")

    # Prepare metadata
    metadata = {
        "cid": cid,
        "context": fused_data["context"],
        "sensor_data": fused_data["sensor_data"],
        "prediction": prediction,
        "timestamp": fused_data["timestamp"],
        "device_id": fused_data["device_id"]
    }

    # Reset file pointer
    await video.seek(0)

    # Upload to data-ingestion
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{data_ingestion_url}/ingest/ldo",
            files={"video": (video.filename, await video.read(), video.content_type)},
            data={"metadata": json.dumps(metadata)}
        )

        if response.status_code != 200:
            logger.error(f"❌ Failed to upload video to data-ingestion: {response.text}")
            raise HTTPException(
                status_code=500,
                detail="Failed to store video"
            )

        result = response.json()
        return result["id"]


@app.get("/stats")
async def get_stats():
    """Get edge server statistics"""
    return {
        "service": "edge-server",
        "uptime": "running",
        "redis_connected": await context_service.health_check(),
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("=" * 60)
    logger.info("Context Edge - Edge Server Starting")
    logger.info("=" * 60)

    # Initialize Redis connection
    await context_service.connect()

    # Initialize protocol adapters
    await fusion_service.initialize()

    logger.info("✅ Edge Server ready to receive CIDs")
    logger.info("")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Edge Server shutting down...")
    await context_service.disconnect()
    await fusion_service.shutdown()
    logger.info("✅ Shutdown complete")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

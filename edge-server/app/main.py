#!/usr/bin/env python3
"""
Context Edge - Edge Server Main Application
Receives CID from camera devices and orchestrates the fusion process
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
import logging

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
async def receive_cid(request: CIDRequest, background_tasks: BackgroundTasks):
    """
    Main endpoint: Receives CID from camera device

    Flow:
    1. Receive CID from camera
    2. Fetch context from Redis
    3. Read PLC sensor data
    4. Fuse context + sensor data (CIM)
    5. Run AI inference
    6. Generate and store LDO
    """
    logger.info(f"📥 Received CID: {request.cid} from camera: {request.camera_id}")

    try:
        # Step 1: Fetch context metadata from Redis
        logger.info(f"🔍 Looking up context for CID: {request.cid}")
        context = await context_service.get_context(request.cid)

        if not context:
            logger.warning(f"⚠️  No context found for CID: {request.cid}")
            raise HTTPException(
                status_code=404,
                detail=f"Context not found for CID: {request.cid}"
            )

        logger.info(f"✅ Context found: {context.get('product_id', 'unknown')}")

        # Step 2: Read real-time sensor data from PLC
        logger.info(f"📊 Reading sensor data from device: {request.camera_id}")
        sensor_data = await fusion_service.read_sensor_data(request.camera_id)
        logger.info(f"✅ Sensor data: {sensor_data}")

        # Step 3: Fuse context + sensor data (CIM - Patented)
        logger.info(f"🔗 Fusing context + sensor data (CIM)")
        fused_data = await fusion_service.fuse_data(
            cid=request.cid,
            context=context,
            sensor_data=sensor_data,
            camera_id=request.camera_id,
            timestamp=request.timestamp
        )
        logger.info(f"✅ Fusion complete")

        # Step 4: Run AI inference
        logger.info(f"🤖 Running AI inference")
        prediction = await fusion_service.run_inference(fused_data)
        logger.info(f"✅ Prediction: {prediction.get('result')} (confidence: {prediction.get('confidence')})")

        # Step 5: Generate and store LDO
        logger.info(f"💾 Generating LDO")
        ldo_id = await ldo_service.create_ldo(
            cid=request.cid,
            fused_data=fused_data,
            prediction=prediction
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
        logger.error(f"❌ Error processing CID {request.cid}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal error processing CID: {str(e)}"
        )


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

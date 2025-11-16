"""
Device Management API
Plug-and-play device discovery, configuration, and monitoring
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import psycopg2
from psycopg2.extras import Json, RealDictCursor
import logging

from app.services.device_discovery import DeviceDiscoveryService

router = APIRouter(prefix="/api/admin/devices", tags=["admin", "devices"])
logger = logging.getLogger(__name__)

# Initialize discovery service
discovery_service = DeviceDiscoveryService()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class NetworkScanRequest(BaseModel):
    """Request to scan network for devices"""
    subnet: str = "192.168.1.0/24"
    protocols: Optional[List[str]] = ["modbus", "opcua", "http"]


class DeviceConfigRequest(BaseModel):
    """Request to configure a new device"""
    name: str
    template_id: Optional[str] = None
    protocol: str
    host: str
    port: int
    config: Dict[str, Any] = {}
    sensor_mappings: Dict[str, Any] = {}
    enabled: bool = True
    notes: Optional[str] = None


class TestConnectionRequest(BaseModel):
    """Request to test device connection"""
    device: Dict[str, Any]
    config: Dict[str, Any]


class DeviceResponse(BaseModel):
    """Device configuration response"""
    config_id: int
    name: str
    template_id: Optional[str]
    protocol: str
    host: str
    port: int
    enabled: bool
    created_at: datetime
    updated_at: datetime


# ============================================================================
# DATABASE HELPERS
# ============================================================================

def _get_connection():
    """Get database connection"""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "context_edge"),
        user=os.getenv("POSTGRES_USER", "context_user"),
        password=os.getenv("POSTGRES_PASSWORD", "context_pass")
    )


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/scan-network")
async def scan_network(request: NetworkScanRequest):
    """
    Scan network for industrial devices (PLCs, MES, ERP)

    Auto-discovers devices on the network and identifies:
    - Protocol (Modbus TCP, OPC UA, HTTP)
    - Vendor (Schneider, Siemens, etc.)
    - Model
    - Recommended template

    This is the "magic" that makes it plug-and-play!

    Request Body:
        subnet: Network range in CIDR notation (e.g., "192.168.1.0/24")
        protocols: List of protocols to scan ["modbus", "opcua", "http"]

    Returns:
        List of discovered devices with metadata
    """
    logger.info(f"🔍 Network scan requested: {request.subnet}")

    try:
        devices = await discovery_service.scan_network(
            subnet=request.subnet,
            protocols=request.protocols
        )

        logger.info(f"✅ Scan complete: Found {len(devices)} devices")

        return {
            "success": True,
            "devices": devices,
            "scan_time": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Network scan failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Network scan failed: {str(e)}")


@router.post("/test-connection")
async def test_connection(request: TestConnectionRequest):
    """
    Test connection to a device before saving configuration

    Shows live data from the device to verify:
    - Connection is successful
    - Register/node mappings are correct
    - Data is readable

    Request Body:
        device: Device info from network scan
        config: Configuration to test (sensor mappings, etc.)

    Returns:
        Connection test result with sample data
    """
    logger.info(f"🧪 Testing connection to {request.device.get('ip')}")

    try:
        result = await discovery_service.test_connection(
            device=request.device,
            config=request.config
        )

        logger.info(f"✅ Connection test complete: {result.get('success')}")

        return result

    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/configs")
async def get_device_configs():
    """
    Get all configured data sources

    Returns:
        List of configured devices with health status
    """
    try:
        conn = _get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Use the view that includes health status
        cur.execute("""
            SELECT * FROM v_data_sources_with_health
            ORDER BY name
        """)

        configs = cur.fetchall()
        cur.close()
        conn.close()

        return [dict(config) for config in configs]

    except Exception as e:
        logger.error(f"❌ Failed to fetch configs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch configs: {str(e)}")


@router.get("/configs/{config_id}")
async def get_device_config(config_id: int):
    """
    Get specific device configuration

    Path Parameters:
        config_id: Configuration ID

    Returns:
        Device configuration details
    """
    try:
        conn = _get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT * FROM data_source_configs
            WHERE config_id = %s
        """, (config_id,))

        config = cur.fetchone()
        cur.close()
        conn.close()

        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        return dict(config)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to fetch config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch config: {str(e)}")


@router.post("/configs")
async def create_device_config(request: DeviceConfigRequest):
    """
    Create new device configuration

    This is called after:
    1. Network scan finds device
    2. User selects template (or configures manually)
    3. User tests connection
    4. User clicks "Save"

    Request Body:
        name: Human-readable device name
        template_id: Optional template ID (auto-fills config)
        protocol: Protocol type (modbus_tcp, opcua, http)
        host: IP address or hostname
        port: Port number
        config: Connection configuration
        sensor_mappings: Sensor name → address/node mappings
        enabled: Whether device is enabled
        notes: Optional notes

    Returns:
        Created configuration
    """
    logger.info(f"💾 Creating device config: {request.name}")

    try:
        conn = _get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Insert configuration
        cur.execute("""
            INSERT INTO data_source_configs (
                name, template_id, protocol, host, port,
                config, sensor_mappings, enabled, notes
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            RETURNING config_id, name, template_id, protocol, host, port,
                      enabled, created_at, updated_at
        """, (
            request.name,
            request.template_id,
            request.protocol,
            request.host,
            request.port,
            Json(request.config),
            Json(request.sensor_mappings),
            request.enabled,
            request.notes
        ))

        config = cur.fetchone()

        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"✅ Device config created: {config['config_id']}")

        # Hot reload will pick this up automatically!
        logger.info("🔄 Config saved - hot reload will activate in 5 seconds")

        return dict(config)

    except psycopg2.IntegrityError as e:
        logger.error(f"❌ Device name already exists: {request.name}")
        raise HTTPException(status_code=400, detail="Device name already exists")
    except Exception as e:
        logger.error(f"❌ Failed to create config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create config: {str(e)}")


@router.put("/configs/{config_id}")
async def update_device_config(config_id: int, request: DeviceConfigRequest):
    """
    Update existing device configuration

    Path Parameters:
        config_id: Configuration ID to update

    Request Body:
        (Same as create)

    Returns:
        Updated configuration
    """
    logger.info(f"📝 Updating device config: {config_id}")

    try:
        conn = _get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            UPDATE data_source_configs
            SET name = %s,
                template_id = %s,
                protocol = %s,
                host = %s,
                port = %s,
                config = %s,
                sensor_mappings = %s,
                enabled = %s,
                notes = %s,
                updated_at = NOW()
            WHERE config_id = %s
            RETURNING config_id, name, template_id, protocol, host, port,
                      enabled, created_at, updated_at
        """, (
            request.name,
            request.template_id,
            request.protocol,
            request.host,
            request.port,
            Json(request.config),
            Json(request.sensor_mappings),
            request.enabled,
            request.notes,
            config_id
        ))

        config = cur.fetchone()

        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"✅ Device config updated: {config_id}")
        logger.info("🔄 Config updated - hot reload will activate in 5 seconds")

        return dict(config)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")


@router.delete("/configs/{config_id}")
async def delete_device_config(config_id: int):
    """
    Delete device configuration

    Path Parameters:
        config_id: Configuration ID to delete

    Returns:
        Success message
    """
    logger.info(f"🗑️  Deleting device config: {config_id}")

    try:
        conn = _get_connection()
        cur = conn.cursor()

        cur.execute("""
            DELETE FROM data_source_configs
            WHERE config_id = %s
        """, (config_id,))

        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Configuration not found")

        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"✅ Device config deleted: {config_id}")
        logger.info("🔄 Config deleted - hot reload will deactivate adapter in 5 seconds")

        return {"success": True, "message": "Configuration deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete config: {str(e)}")


@router.post("/configs/{config_id}/enable")
async def enable_device_config(config_id: int):
    """
    Enable device configuration

    Path Parameters:
        config_id: Configuration ID to enable

    Returns:
        Success message
    """
    logger.info(f"✅ Enabling device config: {config_id}")

    try:
        conn = _get_connection()
        cur = conn.cursor()

        cur.execute("""
            UPDATE data_source_configs
            SET enabled = true,
                updated_at = NOW()
            WHERE config_id = %s
        """, (config_id,))

        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Configuration not found")

        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"✅ Device config enabled: {config_id}")

        return {"success": True, "message": "Configuration enabled"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to enable config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to enable config: {str(e)}")


@router.post("/configs/{config_id}/disable")
async def disable_device_config(config_id: int):
    """
    Disable device configuration

    Path Parameters:
        config_id: Configuration ID to disable

    Returns:
        Success message
    """
    logger.info(f"⏸️  Disabling device config: {config_id}")

    try:
        conn = _get_connection()
        cur = conn.cursor()

        cur.execute("""
            UPDATE data_source_configs
            SET enabled = false,
                updated_at = NOW()
            WHERE config_id = %s
        """, (config_id,))

        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Configuration not found")

        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"✅ Device config disabled: {config_id}")

        return {"success": True, "message": "Configuration disabled"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to disable config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to disable config: {str(e)}")


@router.get("/health")
async def get_adapter_health():
    """
    Get health status of all configured adapters

    Returns:
        List of adapters with health metrics
    """
    try:
        conn = _get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT
                dsc.config_id,
                dsc.name,
                dsc.protocol,
                dsc.host,
                dsc.port,
                dsc.enabled,
                ah.status,
                ah.is_connected,
                ah.response_time_ms,
                ah.success_rate,
                ah.error_count,
                ah.last_error,
                ah.last_error_at,
                ah.checked_at
            FROM data_source_configs dsc
            LEFT JOIN adapter_health ah ON dsc.config_id = ah.config_id
            ORDER BY dsc.name
        """)

        health_data = cur.fetchall()
        cur.close()
        conn.close()

        return [dict(h) for h in health_data]

    except Exception as e:
        logger.error(f"❌ Failed to fetch health data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch health data: {str(e)}")

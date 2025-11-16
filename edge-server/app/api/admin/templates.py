"""
Device Templates API
Pre-configured templates for common industrial devices
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

router = APIRouter(prefix="/api/admin/templates", tags=["admin", "templates"])
logger = logging.getLogger(__name__)


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

@router.get("")
async def get_templates(
    protocol: Optional[str] = None,
    device_type: Optional[str] = None,
    vendor: Optional[str] = None
):
    """
    Get all available device templates

    Query Parameters:
        protocol: Filter by protocol (modbus_tcp, opcua, ethernet_ip, http)
        device_type: Filter by device type (plc, mes, erp, scada)
        vendor: Filter by vendor (Schneider, Siemens, etc.)

    Returns:
        List of device templates
    """
    try:
        conn = _get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Build query with optional filters
        query = "SELECT * FROM device_templates WHERE 1=1"
        params = []

        if protocol:
            query += " AND protocol = %s"
            params.append(protocol)

        if device_type:
            query += " AND device_type = %s"
            params.append(device_type)

        if vendor:
            query += " AND vendor ILIKE %s"
            params.append(f"%{vendor}%")

        query += " ORDER BY vendor, model"

        cur.execute(query, params)

        templates = cur.fetchall()
        cur.close()
        conn.close()

        return [dict(t) for t in templates]

    except Exception as e:
        logger.error(f"❌ Failed to fetch templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch templates: {str(e)}")


@router.get("/{template_id}")
async def get_template(template_id: str):
    """
    Get specific template details

    Path Parameters:
        template_id: Template identifier (e.g., "schneider_m340")

    Returns:
        Template details with default config and sensor mappings
    """
    try:
        conn = _get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT * FROM device_templates
            WHERE template_id = %s
        """, (template_id,))

        template = cur.fetchone()
        cur.close()
        conn.close()

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        return dict(template)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to fetch template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch template: {str(e)}")


@router.get("/protocols/supported")
async def get_supported_protocols():
    """
    Get list of supported protocols

    Returns:
        List of supported protocols with descriptions
    """
    return {
        "protocols": [
            {
                "id": "modbus_tcp",
                "name": "Modbus TCP",
                "description": "Modbus over TCP/IP (most common PLC protocol)",
                "default_port": 502,
                "device_types": ["plc"]
            },
            {
                "id": "opcua",
                "name": "OPC UA",
                "description": "OPC Unified Architecture (modern industrial standard)",
                "default_port": 4840,
                "device_types": ["plc", "scada"]
            },
            {
                "id": "ethernet_ip",
                "name": "Ethernet/IP",
                "description": "Common Industrial Protocol (Rockwell/Allen-Bradley)",
                "default_port": 44818,
                "device_types": ["plc"]
            },
            {
                "id": "profinet",
                "name": "Profinet",
                "description": "Siemens industrial Ethernet protocol",
                "default_port": None,
                "device_types": ["plc"]
            },
            {
                "id": "http",
                "name": "HTTP/REST",
                "description": "HTTP REST API (MES, ERP, SCADA)",
                "default_port": 80,
                "device_types": ["mes", "erp", "scada", "historian"]
            }
        ]
    }


@router.get("/vendors/popular")
async def get_popular_vendors():
    """
    Get list of popular industrial equipment vendors

    Returns:
        List of vendors with their common protocols
    """
    return {
        "vendors": [
            {
                "name": "Schneider Electric",
                "protocols": ["modbus_tcp", "opcua"],
                "common_models": ["M340", "M580", "TM221"]
            },
            {
                "name": "Siemens",
                "protocols": ["opcua", "profinet"],
                "common_models": ["S7-1200", "S7-1500", "S7-300"]
            },
            {
                "name": "Allen-Bradley (Rockwell)",
                "protocols": ["ethernet_ip", "modbus_tcp"],
                "common_models": ["CompactLogix", "ControlLogix", "Micro800"]
            },
            {
                "name": "Omron",
                "protocols": ["ethernet_ip", "opcua"],
                "common_models": ["NJ", "NX", "CP1"]
            },
            {
                "name": "Mitsubishi",
                "protocols": ["modbus_tcp", "ethernet_ip"],
                "common_models": ["iQ-R", "iQ-F", "FX5"]
            },
            {
                "name": "Wonderware",
                "protocols": ["http"],
                "common_models": ["MES", "System Platform"]
            },
            {
                "name": "SAP",
                "protocols": ["http"],
                "common_models": ["S/4HANA", "ERP"]
            }
        ]
    }

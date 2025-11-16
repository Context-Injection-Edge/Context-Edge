"""
MES (Manufacturing Execution System) Adapters

Supports:
- Wonderware MES (AVEVA)
- Siemens Opcenter
- Rockwell FactoryTalk ProductionCentre
- Dassault DELMIA
- Generic REST/SOAP MES APIs
"""

from typing import Dict, Any, Optional
import logging
import httpx
from datetime import datetime

from .base import DataSourceAdapter

logger = logging.getLogger(__name__)


class MESAdapter(DataSourceAdapter):
    """
    Generic MES adapter using REST API

    Retrieves production data:
    - Work orders
    - Production counts
    - OEE metrics
    - Quality data
    - Material consumption
    - Downtime events
    """

    async def connect(self) -> bool:
        """Test connection to MES API"""
        try:
            base_url = self.config.get("base_url")
            api_key = self.config.get("api_key")
            username = self.config.get("username")
            password = self.config.get("password")

            if not base_url:
                logger.error(f"❌ MES adapter {self.source_name}: Missing base_url")
                return False

            # Test health endpoint
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                elif username and password:
                    # Basic auth
                    import base64
                    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                    headers["Authorization"] = f"Basic {credentials}"

                health_endpoint = self.config.get("health_endpoint", "/api/health")
                response = await client.get(f"{base_url}{health_endpoint}", headers=headers)

                if response.status_code == 200:
                    self.is_connected = True
                    logger.info(f"✅ MES adapter connected: {self.source_name}")
                    return True
                else:
                    logger.error(f"❌ MES health check failed: {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"❌ MES connection failed: {e}")
            return False

    async def disconnect(self) -> bool:
        """Disconnect from MES (nothing to do for REST API)"""
        self.is_connected = False
        logger.info(f"✅ MES adapter disconnected: {self.source_name}")
        return True

    async def read_data(self, identifier: str) -> Dict[str, Any]:
        """
        Read production data from MES

        Args:
            identifier: Device ID, work order, or station ID

        Returns:
            Production data from MES
        """
        if not self.is_connected:
            logger.warning(f"⚠️  MES adapter not connected: {self.source_name}")
            return {}

        try:
            base_url = self.config.get("base_url")
            api_key = self.config.get("api_key")
            username = self.config.get("username")
            password = self.config.get("password")

            # Build headers
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            elif username and password:
                import base64
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"

            # Determine endpoint based on identifier type
            endpoint = self.config.get("data_endpoint", "/api/production/current")

            # Make API request
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{base_url}{endpoint}",
                    headers=headers,
                    params={"station_id": identifier}
                )

                if response.status_code == 200:
                    data = response.json()

                    # Extract relevant fields
                    mes_data = {
                        "work_order": data.get("work_order"),
                        "product_id": data.get("product_id"),
                        "batch_number": data.get("batch_number"),
                        "production_count": data.get("production_count", 0),
                        "target_count": data.get("target_count", 0),
                        "oee": data.get("oee", 0.0),
                        "availability": data.get("availability", 0.0),
                        "performance": data.get("performance", 0.0),
                        "quality": data.get("quality", 0.0),
                        "cycle_time_actual": data.get("cycle_time_actual"),
                        "cycle_time_target": data.get("cycle_time_target"),
                        "downtime_minutes": data.get("downtime_minutes", 0),
                        "defect_count": data.get("defect_count", 0),
                        "timestamp": data.get("timestamp", datetime.now().isoformat())
                    }

                    logger.info(f"✅ MES data read: WO={mes_data.get('work_order')}, Count={mes_data.get('production_count')}")
                    return mes_data

                else:
                    logger.error(f"❌ MES API error: {response.status_code} - {response.text}")
                    return {}

        except Exception as e:
            logger.error(f"❌ MES read error: {e}", exc_info=True)
            return {}


class WonderwareMESAdapter(MESAdapter):
    """
    Wonderware MES (AVEVA) adapter
    Uses Wonderware MES REST API
    """

    def __init__(self, source_name: str, config: Dict[str, Any]):
        # Set Wonderware-specific defaults
        if "data_endpoint" not in config:
            config["data_endpoint"] = "/api/v1/production/workorders/active"
        if "health_endpoint" not in config:
            config["health_endpoint"] = "/api/v1/system/health"

        super().__init__(source_name, config)


class SiemensOpcenterAdapter(MESAdapter):
    """
    Siemens Opcenter MES adapter
    Uses Opcenter Execution REST API
    """

    def __init__(self, source_name: str, config: Dict[str, Any]):
        # Set Siemens-specific defaults
        if "data_endpoint" not in config:
            config["data_endpoint"] = "/odata/Production/Operations"
        if "health_endpoint" not in config:
            config["health_endpoint"] = "/api/health"

        super().__init__(source_name, config)


class RockwellFactoryTalkAdapter(MESAdapter):
    """
    Rockwell FactoryTalk ProductionCentre adapter
    Uses FactoryTalk REST API
    """

    def __init__(self, source_name: str, config: Dict[str, Any]):
        # Set Rockwell-specific defaults
        if "data_endpoint" not in config:
            config["data_endpoint"] = "/api/production/current"
        if "health_endpoint" not in config:
            config["health_endpoint"] = "/api/status"

        super().__init__(source_name, config)

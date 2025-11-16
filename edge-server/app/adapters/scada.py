"""
SCADA (Supervisory Control and Data Acquisition) Adapters

Supports:
- Ignition (Inductive Automation)
- Siemens WinCC
- Wonderware System Platform
- GE iFIX
- Rockwell FactoryTalk View
"""

from typing import Dict, Any, Optional
import logging
import httpx
from datetime import datetime

from .base import DataSourceAdapter

logger = logging.getLogger(__name__)


class SCADAAdapter(DataSourceAdapter):
    """
    Generic SCADA adapter using REST/Web API

    Retrieves SCADA data:
    - Real-time tag values
    - Alarm status
    - Process variables
    - Equipment status
    - Historical trends
    """

    async def connect(self) -> bool:
        """Test connection to SCADA API"""
        try:
            base_url = self.config.get("base_url")
            api_key = self.config.get("api_key")
            username = self.config.get("username")
            password = self.config.get("password")

            if not base_url:
                logger.error(f"❌ SCADA adapter {self.source_name}: Missing base_url")
                return False

            # Test health endpoint
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {"Content-Type": "application/json"}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                elif username and password:
                    import base64
                    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                    headers["Authorization"] = f"Basic {credentials}"

                health_endpoint = self.config.get("health_endpoint", "/api/health")
                response = await client.get(f"{base_url}{health_endpoint}", headers=headers)

                if response.status_code in [200, 204]:
                    self.is_connected = True
                    logger.info(f"✅ SCADA adapter connected: {self.source_name}")
                    return True
                else:
                    logger.error(f"❌ SCADA health check failed: {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"❌ SCADA connection failed: {e}")
            return False

    async def disconnect(self) -> bool:
        """Disconnect from SCADA"""
        self.is_connected = False
        logger.info(f"✅ SCADA adapter disconnected: {self.source_name}")
        return True

    async def read_data(self, identifier: str) -> Dict[str, Any]:
        """
        Read real-time data from SCADA

        Args:
            identifier: Tag path, equipment ID, or area

        Returns:
            SCADA tag values and alarm status
        """
        if not self.is_connected:
            logger.warning(f"⚠️  SCADA adapter not connected: {self.source_name}")
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

            # Get tag list for this device/area
            tag_paths = self.config.get("tag_paths", [])
            if not tag_paths:
                logger.warning(f"⚠️  No tag_paths configured for {self.source_name}")
                return {}

            # Read tags endpoint
            endpoint = self.config.get("read_endpoint", "/api/tags/read")

            # Make API request
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{base_url}{endpoint}",
                    headers=headers,
                    json={"tags": tag_paths, "area": identifier}
                )

                if response.status_code == 200:
                    data = response.json()

                    # Extract tag values
                    scada_data = {
                        "equipment_status": data.get("equipment_status"),
                        "running": data.get("running", False),
                        "alarm_active": data.get("alarm_active", False),
                        "alarm_count": data.get("alarm_count", 0),
                        "mode": data.get("mode"),  # Auto, Manual, etc.
                        "setpoint": data.get("setpoint"),
                        "process_value": data.get("process_value"),
                        "output": data.get("output"),
                        "timestamp": data.get("timestamp", datetime.now().isoformat())
                    }

                    # Add custom tags
                    for tag in tag_paths:
                        tag_name = tag.split("/")[-1]  # Get last part of path
                        if tag_name in data:
                            scada_data[tag_name] = data[tag_name]

                    logger.info(f"✅ SCADA data read: {len(scada_data)} tags")
                    return scada_data

                else:
                    logger.error(f"❌ SCADA API error: {response.status_code} - {response.text}")
                    return {}

        except Exception as e:
            logger.error(f"❌ SCADA read error: {e}", exc_info=True)
            return {}


class IgnitionAdapter(SCADAAdapter):
    """
    Ignition SCADA adapter (Inductive Automation)
    Uses Ignition Web Dev Module or WebDev API
    """

    def __init__(self, source_name: str, config: Dict[str, Any]):
        # Set Ignition-specific defaults
        if "read_endpoint" not in config:
            config["read_endpoint"] = "/system/webdev/tagRead"
        if "health_endpoint" not in config:
            config["health_endpoint"] = "/system/webdev/ping"

        super().__init__(source_name, config)

    async def read_data(self, identifier: str) -> Dict[str, Any]:
        """Read tags from Ignition"""
        if not self.is_connected:
            return {}

        try:
            base_url = self.config.get("base_url")
            username = self.config.get("username")
            password = self.config.get("password")

            headers = {"Content-Type": "application/json"}
            if username and password:
                import base64
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"

            # Ignition tag paths
            tag_paths = self.config.get("tag_paths", [])

            # Read tags using Ignition WebDev
            endpoint = self.config.get("read_endpoint")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{base_url}{endpoint}",
                    headers=headers,
                    json={"tagPaths": tag_paths}
                )

                if response.status_code == 200:
                    data = response.json()

                    # Parse Ignition response
                    ignition_data = {
                        "timestamp": datetime.now().isoformat()
                    }

                    for i, tag_path in enumerate(tag_paths):
                        tag_name = tag_path.split("/")[-1]
                        if i < len(data):
                            ignition_data[tag_name] = data[i].get("value")
                            ignition_data[f"{tag_name}_quality"] = data[i].get("quality")

                    logger.info(f"✅ Ignition data read: {len(tag_paths)} tags")
                    return ignition_data

                else:
                    logger.error(f"❌ Ignition API error: {response.status_code}")
                    return {}

        except Exception as e:
            logger.error(f"❌ Ignition read error: {e}", exc_info=True)
            return {}


class SiemensWinCCAdapter(SCADAAdapter):
    """
    Siemens WinCC SCADA adapter
    Uses WinCC Web Navigator or REST API
    """

    def __init__(self, source_name: str, config: Dict[str, Any]):
        # Set WinCC-specific defaults
        if "read_endpoint" not in config:
            config["read_endpoint"] = "/api/data/read"
        if "health_endpoint" not in config:
            config["health_endpoint"] = "/api/system/status"

        super().__init__(source_name, config)


class WonderwareSCADAAdapter(SCADAAdapter):
    """
    Wonderware System Platform adapter (AVEVA)
    Uses Wonderware Online or REST API
    """

    def __init__(self, source_name: str, config: Dict[str, Any]):
        # Set Wonderware-specific defaults
        if "read_endpoint" not in config:
            config["read_endpoint"] = "/api/attributes/read"
        if "health_endpoint" not in config:
            config["health_endpoint"] = "/api/system/ping"

        super().__init__(source_name, config)

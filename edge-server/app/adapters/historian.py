"""
Historian Adapters (Time-Series Data)

Supports:
- OSIsoft PI (AVEVA PI System)
- Wonderware Historian
- GE Proficy Historian
- Rockwell FactoryTalk Historian
- InfluxDB
- TimescaleDB
"""

from typing import Dict, Any, Optional, List
import logging
import httpx
from datetime import datetime, timedelta

from .base import DataSourceAdapter

logger = logging.getLogger(__name__)


class HistorianAdapter(DataSourceAdapter):
    """
    Generic Historian adapter for time-series data

    Retrieves historical data:
    - Process variable trends
    - Equipment performance history
    - Quality metrics over time
    - Production statistics
    - Energy consumption
    """

    async def connect(self) -> bool:
        """Test connection to Historian API"""
        try:
            base_url = self.config.get("base_url")
            api_key = self.config.get("api_key")
            username = self.config.get("username")
            password = self.config.get("password")

            if not base_url:
                logger.error(f"❌ Historian adapter {self.source_name}: Missing base_url")
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
                    logger.info(f"✅ Historian adapter connected: {self.source_name}")
                    return True
                else:
                    logger.error(f"❌ Historian health check failed: {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"❌ Historian connection failed: {e}")
            return False

    async def disconnect(self) -> bool:
        """Disconnect from Historian"""
        self.is_connected = False
        logger.info(f"✅ Historian adapter disconnected: {self.source_name}")
        return True

    async def read_data(self, identifier: str) -> Dict[str, Any]:
        """
        Read historical data from Historian

        Args:
            identifier: Tag name, equipment ID, or area

        Returns:
            Historical statistics and trends
        """
        if not self.is_connected:
            logger.warning(f"⚠️  Historian adapter not connected: {self.source_name}")
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

            # Time window for historical data
            time_window = self.config.get("time_window_minutes", 60)
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=time_window)

            # Tags to read
            tag_list = self.config.get("tags", [])

            # Query endpoint
            endpoint = self.config.get("query_endpoint", "/api/data/query")

            # Make API request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{base_url}{endpoint}",
                    headers=headers,
                    json={
                        "tags": tag_list,
                        "start_time": start_time.isoformat(),
                        "end_time": end_time.isoformat(),
                        "aggregation": "summary"  # avg, min, max, count
                    }
                )

                if response.status_code == 200:
                    data = response.json()

                    # Extract statistical summary
                    historian_data = {
                        "time_window_minutes": time_window,
                        "start_time": start_time.isoformat(),
                        "end_time": end_time.isoformat(),
                        "timestamp": datetime.now().isoformat()
                    }

                    # Add aggregated values
                    for tag in tag_list:
                        tag_name = tag.split("/")[-1]
                        if tag in data:
                            tag_stats = data[tag]
                            historian_data[f"{tag_name}_avg"] = tag_stats.get("average")
                            historian_data[f"{tag_name}_min"] = tag_stats.get("minimum")
                            historian_data[f"{tag_name}_max"] = tag_stats.get("maximum")
                            historian_data[f"{tag_name}_stddev"] = tag_stats.get("std_dev")
                            historian_data[f"{tag_name}_count"] = tag_stats.get("count")

                    logger.info(f"✅ Historian data read: {len(tag_list)} tags over {time_window} minutes")
                    return historian_data

                else:
                    logger.error(f"❌ Historian API error: {response.status_code} - {response.text}")
                    return {}

        except Exception as e:
            logger.error(f"❌ Historian read error: {e}", exc_info=True)
            return {}


class OSIsoftPIAdapter(HistorianAdapter):
    """
    OSIsoft PI (AVEVA PI System) adapter
    Uses PI Web API
    """

    def __init__(self, source_name: str, config: Dict[str, Any]):
        # Set PI-specific defaults
        if "query_endpoint" not in config:
            config["query_endpoint"] = "/piwebapi/streamsets/summary"
        if "health_endpoint" not in config:
            config["health_endpoint"] = "/piwebapi/system"

        super().__init__(source_name, config)

    async def read_data(self, identifier: str) -> Dict[str, Any]:
        """Read from OSIsoft PI Web API"""
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

            # PI Web API uses WebIds
            tag_webids = self.config.get("tag_webids", [])
            time_window = self.config.get("time_window_minutes", 60)

            # Build stream set URLs
            webid_list = ";".join(tag_webids)

            # Query PI Web API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{base_url}/piwebapi/streamsets/summary",
                    headers=headers,
                    params={
                        "webId": webid_list,
                        "startTime": f"*-{time_window}m",
                        "endTime": "*",
                        "summaryType": "Average,Minimum,Maximum,StdDev"
                    }
                )

                if response.status_code == 200:
                    data = response.json()

                    pi_data = {
                        "time_window_minutes": time_window,
                        "timestamp": datetime.now().isoformat()
                    }

                    # Parse PI Web API response
                    items = data.get("Items", [])
                    for item in items:
                        tag_name = item.get("Name")
                        summaries = item.get("Items", [])

                        for summary in summaries:
                            summary_type = summary.get("Type")
                            value = summary.get("Value", {}).get("Value")

                            if summary_type == "Average":
                                pi_data[f"{tag_name}_avg"] = value
                            elif summary_type == "Minimum":
                                pi_data[f"{tag_name}_min"] = value
                            elif summary_type == "Maximum":
                                pi_data[f"{tag_name}_max"] = value
                            elif summary_type == "StdDev":
                                pi_data[f"{tag_name}_stddev"] = value

                    logger.info(f"✅ PI data read: {len(items)} tags")
                    return pi_data

                else:
                    logger.error(f"❌ PI Web API error: {response.status_code}")
                    return {}

        except Exception as e:
            logger.error(f"❌ PI read error: {e}", exc_info=True)
            return {}


class WonderwareHistorianAdapter(HistorianAdapter):
    """
    Wonderware Historian adapter (AVEVA)
    Uses Wonderware Historian REST API
    """

    def __init__(self, source_name: str, config: Dict[str, Any]):
        # Set Wonderware-specific defaults
        if "query_endpoint" not in config:
            config["query_endpoint"] = "/api/data/history"
        if "health_endpoint" not in config:
            config["health_endpoint"] = "/api/system/status"

        super().__init__(source_name, config)


class InfluxDBAdapter(HistorianAdapter):
    """
    InfluxDB adapter for time-series data
    Uses InfluxDB HTTP API
    """

    def __init__(self, source_name: str, config: Dict[str, Any]):
        # Set InfluxDB-specific defaults
        if "query_endpoint" not in config:
            config["query_endpoint"] = "/api/v2/query"
        if "health_endpoint" not in config:
            config["health_endpoint"] = "/health"

        super().__init__(source_name, config)

    async def read_data(self, identifier: str) -> Dict[str, Any]:
        """Query InfluxDB using Flux"""
        if not self.is_connected:
            return {}

        try:
            base_url = self.config.get("base_url")
            token = self.config.get("token")
            org = self.config.get("org")
            bucket = self.config.get("bucket")

            headers = {
                "Content-Type": "application/vnd.flux",
                "Authorization": f"Token {token}"
            }

            time_window = self.config.get("time_window_minutes", 60)
            measurement = self.config.get("measurement", "sensors")

            # Flux query
            flux_query = f'''
            from(bucket: "{bucket}")
                |> range(start: -{time_window}m)
                |> filter(fn: (r) => r._measurement == "{measurement}")
                |> filter(fn: (r) => r.device_id == "{identifier}")
                |> aggregateWindow(every: {time_window}m, fn: mean)
            '''

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{base_url}/api/v2/query",
                    headers=headers,
                    params={"org": org},
                    data=flux_query
                )

                if response.status_code == 200:
                    # Parse InfluxDB CSV response
                    influx_data = {
                        "time_window_minutes": time_window,
                        "timestamp": datetime.now().isoformat()
                    }

                    # TODO: Parse CSV response
                    # For now, return basic structure

                    logger.info(f"✅ InfluxDB data read")
                    return influx_data

                else:
                    logger.error(f"❌ InfluxDB error: {response.status_code}")
                    return {}

        except Exception as e:
            logger.error(f"❌ InfluxDB read error: {e}", exc_info=True)
            return {}

# OPC UA Protocol Adapter for industrial data acquisition

from opcua import Client
from typing import Dict, Any, Optional
import time
import logging

logger = logging.getLogger(__name__)


class OPCUAProtocol:
    def __init__(self, server_url: str, node_mappings: Dict[str, str], max_retries: int = 3):
        """
        Initialize OPC UA client
        Args:
            server_url: OPC UA server URL (e.g., "opc.tcp://localhost:4840")
            node_mappings: Dict of sensor names to OPC UA node IDs
            max_retries: Maximum connection retry attempts (default 3)
        """
        self.server_url = server_url
        self.node_mappings = node_mappings
        self.client: Optional[Client] = None
        self.max_retries = max_retries

    def connect(self):
        """Connect to OPC UA server with retry logic"""
        for attempt in range(self.max_retries):
            try:
                self.client = Client(self.server_url)
                self.client.connect()
                logger.info(f"✅ Connected to OPC UA server: {self.server_url}")
                return True
            except Exception as e:
                logger.warning(f"⚠️  Connection attempt {attempt + 1}/{self.max_retries} failed: {e}")
                self.client = None
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        logger.error(f"❌ Failed to connect to OPC UA server after {self.max_retries} attempts")
        return False

    def disconnect(self):
        """Disconnect from OPC UA server"""
        if self.client:
            self.client.disconnect()
            self.client = None

    def read_sensor_data(self) -> Dict[str, Any]:
        """
        Read sensor data from OPC UA nodes
        Returns dict of sensor_name: value
        """
        if not self.client:
            self.connect()
            if not self.client:
                return {}

        data = {}
        try:
            for sensor_name, node_id in self.node_mappings.items():
                node = self.client.get_node(node_id)
                value = node.get_value()
                data[sensor_name] = value
        except Exception as e:
            logger.error(f"❌ Error reading OPC UA data: {e}")
            # Try to reconnect on next call
            self.disconnect()

        return data

    def __del__(self):
        self.disconnect()

# EtherNet/IP Protocol Adapter for Rockwell/Allen-Bradley PLCs
# Uses CIP (Common Industrial Protocol) over TCP/IP

from pycomm3 import LogixDriver
from typing import Dict, Any, Optional
import time


class EtherNetIPProtocol:
    def __init__(self, host: str, tag_mappings: Dict[str, str], port: int = 44818, max_retries: int = 3):
        """
        Initialize EtherNet/IP client for Allen-Bradley/Rockwell PLCs

        Args:
            host: PLC IP address (e.g., "192.168.1.10")
            tag_mappings: Dict of sensor names to PLC tag names
                Example: {
                    "vibration": "Motor1_VibrationX",
                    "temperature": "Motor1_Temp",
                    "current": "Motor1_Current"
                }
            port: EtherNet/IP port (default 44818 for ControlLogix/CompactLogix)
            max_retries: Maximum connection retry attempts (default 3)
        """
        self.host = host
        self.port = port
        self.tag_mappings = tag_mappings
        self.max_retries = max_retries
        self.client: Optional[LogixDriver] = None

    def connect(self) -> bool:
        """Connect to PLC with retry logic"""
        for attempt in range(self.max_retries):
            try:
                self.client = LogixDriver(self.host, port=self.port)
                self.client.open()
                print(f"Connected to EtherNet/IP PLC: {self.host}:{self.port}")
                return True
            except Exception as e:
                print(f"Connection attempt {attempt + 1}/{self.max_retries} failed: {e}")
                self.client = None
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        print(f"Failed to connect to EtherNet/IP PLC after {self.max_retries} attempts")
        return False

    def disconnect(self):
        """Disconnect from PLC"""
        if self.client:
            try:
                self.client.close()
            except Exception as e:
                print(f"Error disconnecting: {e}")
            finally:
                self.client = None

    def read_sensor_data(self) -> Dict[str, Any]:
        """
        Read sensor data from PLC tags
        Returns dict of sensor_name: value
        """
        if not self.client:
            self.connect()
            if not self.client:
                return {}

        data = {}
        try:
            for sensor_name, tag_name in self.tag_mappings.items():
                result = self.client.read(tag_name)
                if result.error:
                    print(f"Error reading tag '{tag_name}': {result.error}")
                    continue
                data[sensor_name] = result.value
        except Exception as e:
            print(f"Error reading EtherNet/IP data: {e}")
            # Try to reconnect on next call
            self.disconnect()

        return data

    def write_tag(self, tag_name: str, value: Any) -> bool:
        """
        Write value to PLC tag
        WARNING: Use with extreme caution in production!
        Context Edge should be READ-ONLY in most deployments.

        Args:
            tag_name: PLC tag name (e.g., "Motor1_Enable")
            value: Value to write (int, float, bool, etc.)

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            self.connect()
            if not self.client:
                return False

        try:
            result = self.client.write(tag_name, value)
            if result.error:
                print(f"Error writing tag '{tag_name}': {result.error}")
                return False
            print(f"Successfully wrote {value} to tag '{tag_name}'")
            return True
        except Exception as e:
            print(f"Error writing EtherNet/IP tag: {e}")
            return False

    def get_plc_info(self) -> Dict[str, Any]:
        """Get PLC information (vendor, product, revision)"""
        if not self.client:
            self.connect()
            if not self.client:
                return {}

        try:
            info = {
                "vendor": getattr(self.client, "info", {}).get("vendor", "Unknown"),
                "product_type": getattr(self.client, "info", {}).get("product_type", "Unknown"),
                "product_code": getattr(self.client, "info", {}).get("product_code", "Unknown"),
                "revision": getattr(self.client, "info", {}).get("revision", "Unknown"),
                "serial": getattr(self.client, "info", {}).get("serial", "Unknown"),
            }
            return info
        except Exception as e:
            print(f"Error getting PLC info: {e}")
            return {}

    def __del__(self):
        self.disconnect()

# PROFINET/S7 Protocol Adapter for Siemens PLCs
# Uses S7 protocol over PROFINET/Ethernet
# Compatible with S7-300, S7-400, S7-1200, S7-1500 PLCs

import snap7
from snap7.util import get_real, get_int, get_dint, get_bool
from typing import Dict, Any, Optional
import time


class PROFINETProtocol:
    def __init__(
        self,
        host: str,
        rack: int = 0,
        slot: int = 1,
        db_mappings: Dict[str, Dict[str, Any]] = None,
        max_retries: int = 3
    ):
        """
        Initialize PROFINET/S7 client for Siemens PLCs

        Args:
            host: PLC IP address (e.g., "192.168.1.10")
            rack: PLC rack number (default 0 for S7-1200/1500, check CPU config for S7-300/400)
            slot: PLC slot number (default 1 for S7-1200/1500, typically 2 for S7-300/400)
            db_mappings: Dict of sensor names to DB (Data Block) configurations
                Example: {
                    "vibration": {
                        "db_number": 1,    # Data Block number
                        "start": 0,        # Byte offset in DB
                        "type": "real"     # Data type: "real", "int", "dint", "bool"
                    },
                    "temperature": {
                        "db_number": 1,
                        "start": 4,        # Real is 4 bytes, so next starts at 4
                        "type": "real"
                    }
                }
            max_retries: Maximum connection retry attempts (default 3)
        """
        self.host = host
        self.rack = rack
        self.slot = slot
        self.db_mappings = db_mappings or {}
        self.max_retries = max_retries
        self.client: Optional[snap7.client.Client] = None

    def connect(self) -> bool:
        """Connect to Siemens PLC with retry logic"""
        for attempt in range(self.max_retries):
            try:
                self.client = snap7.client.Client()
                self.client.connect(self.host, self.rack, self.slot)
                print(f"Connected to Siemens PLC at {self.host} (rack={self.rack}, slot={self.slot})")
                return True
            except Exception as e:
                print(f"Connection attempt {attempt + 1}/{self.max_retries} failed: {e}")
                self.client = None
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff

        print(f"Failed to connect to Siemens PLC after {self.max_retries} attempts")
        return False

    def disconnect(self):
        """Disconnect from PLC"""
        if self.client:
            try:
                self.client.disconnect()
            except Exception as e:
                print(f"Error disconnecting: {e}")
            finally:
                self.client = None

    def read_sensor_data(self) -> Dict[str, Any]:
        """
        Read sensor data from PLC Data Blocks
        Returns dict of sensor_name: value
        """
        if not self.client or not self.client.get_connected():
            self.connect()
            if not self.client or not self.client.get_connected():
                return {}

        data = {}
        try:
            for sensor_name, config in self.db_mappings.items():
                db_number = config["db_number"]
                start = config["start"]
                data_type = config.get("type", "real")

                # Determine how many bytes to read based on data type
                if data_type == "real":
                    size = 4  # REAL is 4 bytes (32-bit float)
                elif data_type == "dint":
                    size = 4  # DINT is 4 bytes (32-bit signed integer)
                elif data_type == "int":
                    size = 2  # INT is 2 bytes (16-bit signed integer)
                elif data_type == "bool":
                    size = 1  # BOOL is 1 byte
                else:
                    print(f"Unsupported data type '{data_type}' for sensor '{sensor_name}'")
                    continue

                # Read data block
                db_data = self.client.db_read(db_number, start, size)

                # Parse value based on type
                if data_type == "real":
                    value = get_real(db_data, 0)
                elif data_type == "dint":
                    value = get_dint(db_data, 0)
                elif data_type == "int":
                    value = get_int(db_data, 0)
                elif data_type == "bool":
                    value = get_bool(db_data, 0, 0)  # byte 0, bit 0
                else:
                    continue

                data[sensor_name] = value

        except Exception as e:
            print(f"Error reading PROFINET/S7 data: {e}")
            # Try to reconnect on next call
            self.disconnect()

        return data

    def write_db(self, db_number: int, start: int, value: Any, data_type: str = "real") -> bool:
        """
        Write value to PLC Data Block
        WARNING: Use with extreme caution in production!
        Context Edge should be READ-ONLY in most deployments.

        Args:
            db_number: Data Block number
            start: Byte offset in DB
            value: Value to write
            data_type: Data type ("real", "int", "dint", "bool")

        Returns:
            True if successful, False otherwise
        """
        if not self.client or not self.client.get_connected():
            self.connect()
            if not self.client or not self.client.get_connected():
                return False

        try:
            # Determine size based on type
            if data_type == "real":
                size = 4
                db_data = bytearray(size)
                snap7.util.set_real(db_data, 0, value)
            elif data_type == "dint":
                size = 4
                db_data = bytearray(size)
                snap7.util.set_dint(db_data, 0, value)
            elif data_type == "int":
                size = 2
                db_data = bytearray(size)
                snap7.util.set_int(db_data, 0, value)
            elif data_type == "bool":
                size = 1
                db_data = bytearray(size)
                snap7.util.set_bool(db_data, 0, 0, value)
            else:
                print(f"Unsupported data type '{data_type}'")
                return False

            self.client.db_write(db_number, start, db_data)
            print(f"Successfully wrote {value} to DB{db_number}.DBX{start}")
            return True

        except Exception as e:
            print(f"Error writing PROFINET/S7 data: {e}")
            return False

    def get_plc_info(self) -> Dict[str, Any]:
        """Get PLC CPU information"""
        if not self.client or not self.client.get_connected():
            self.connect()
            if not self.client or not self.client.get_connected():
                return {}

        try:
            cpu_info = self.client.get_cpu_info()
            return {
                "module_type_name": cpu_info.ModuleTypeName.decode('utf-8'),
                "serial_number": cpu_info.SerialNumber.decode('utf-8'),
                "as_name": cpu_info.ASName.decode('utf-8'),
                "copyright": cpu_info.Copyright.decode('utf-8'),
                "module_name": cpu_info.ModuleName.decode('utf-8')
            }
        except Exception as e:
            print(f"Error getting PLC info: {e}")
            return {}

    def get_cpu_state(self) -> str:
        """Get PLC CPU state (RUN, STOP, etc.)"""
        if not self.client or not self.client.get_connected():
            self.connect()
            if not self.client or not self.client.get_connected():
                return "DISCONNECTED"

        try:
            state = self.client.get_cpu_state()
            states = {
                0x00: "UNKNOWN",
                0x08: "RUN",
                0x04: "STOP"
            }
            return states.get(ord(state), f"UNKNOWN_STATE_{ord(state)}")
        except Exception as e:
            print(f"Error getting CPU state: {e}")
            return "ERROR"

    def __del__(self):
        self.disconnect()

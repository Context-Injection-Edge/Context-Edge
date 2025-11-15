# Modbus Protocol Adapter for industrial data acquisition

from pymodbus.client import ModbusTcpClient
from typing import Dict, Any, Optional
import time

class ModbusProtocol:
    def __init__(self, host: str, port: int = 502, register_mappings: Dict[str, Dict[str, Any]], max_retries: int = 3):
        """
        Initialize Modbus TCP client
        Args:
            host: Modbus server host
            port: Modbus server port (default 502)
            register_mappings: Dict of sensor names to register config
                e.g., {"temperature": {"address": 0, "type": "holding", "count": 1, "scale": 100.0}}
                - address: Register address
                - type: "holding" or "input"
                - count: Number of registers (1 for 16-bit, 2 for 32-bit)
                - scale: Optional scaling factor (default 1.0)
            max_retries: Maximum connection retry attempts (default 3)
        """
        self.host = host
        self.port = port
        self.register_mappings = register_mappings
        self.client: Optional[ModbusTcpClient] = None
        self.max_retries = max_retries

    def connect(self):
        """Connect to Modbus server with retry logic"""
        for attempt in range(self.max_retries):
            try:
                self.client = ModbusTcpClient(self.host, port=self.port)
                if self.client.connect():
                    print(f"Connected to Modbus server: {self.host}:{self.port}")
                    return True
                else:
                    print(f"Connection attempt {attempt + 1}/{self.max_retries} failed")
                    self.client = None
            except Exception as e:
                print(f"Connection attempt {attempt + 1}/{self.max_retries} error: {e}")
                self.client = None

            if attempt < self.max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff

        print(f"Failed to connect to Modbus server after {self.max_retries} attempts")
        return False

    def disconnect(self):
        """Disconnect from Modbus server"""
        if self.client:
            self.client.close()
            self.client = None

    def read_sensor_data(self) -> Dict[str, Any]:
        """
        Read sensor data from Modbus registers
        Returns dict of sensor_name: value
        """
        if not self.client:
            self.connect()
            if not self.client:
                return {}

        data = {}
        try:
            for sensor_name, config in self.register_mappings.items():
                address = config["address"]
                reg_type = config.get("type", "holding")
                count = config.get("count", 1)

                if reg_type == "holding":
                    result = self.client.read_holding_registers(address, count)
                elif reg_type == "input":
                    result = self.client.read_input_registers(address, count)
                else:
                    continue

                if result.isError():
                    print(f"Error reading {sensor_name}: {result}")
                    continue

                # Convert to float if needed (assuming 16-bit registers)
                if count == 1:
                    value = result.registers[0]
                else:
                    # Combine registers for 32-bit values
                    value = (result.registers[0] << 16) + result.registers[1]

                # Apply scaling factor if specified
                scale = config.get("scale", 1.0)
                value = value / scale

                data[sensor_name] = value

        except Exception as e:
            print(f"Error reading Modbus data: {e}")
            # Try to reconnect on next call
            self.disconnect()

        return data

    def __del__(self):
        self.disconnect()
# Modbus RTU Protocol Adapter for serial communication with PLCs
# Uses RS-232 or RS-485 serial connections

from pymodbus.client import ModbusSerialClient
from typing import Dict, Any, Optional
import time


class ModbusRTUProtocol:
    def __init__(
        self,
        port: str,
        register_mappings: Dict[str, Dict[str, Any]],
        slave_id: int = 1,
        baudrate: int = 9600,
        bytesize: int = 8,
        parity: str = 'N',
        stopbits: int = 1,
        max_retries: int = 3
    ):
        """
        Initialize Modbus RTU client for serial communication

        Args:
            port: Serial port (e.g., "/dev/ttyUSB0" on Linux, "COM3" on Windows)
            register_mappings: Dict of sensor names to register configurations
                Example: {
                    "temperature": {
                        "address": 0,
                        "type": "holding",  # "holding" or "input"
                        "count": 1,         # 1 for 16-bit, 2 for 32-bit
                        "scale": 10.0       # Divide by this to get actual value
                    }
                }
            slave_id: Modbus slave ID (default 1)
            baudrate: Serial baudrate (default 9600, common: 9600, 19200, 38400, 115200)
            bytesize: Data bits (default 8)
            parity: Parity ('N'=None, 'E'=Even, 'O'=Odd) (default 'N')
            stopbits: Stop bits (default 1)
            max_retries: Maximum connection retry attempts (default 3)
        """
        self.port = port
        self.register_mappings = register_mappings
        self.slave_id = slave_id
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.max_retries = max_retries
        self.client: Optional[ModbusSerialClient] = None

    def connect(self) -> bool:
        """Connect to Modbus RTU device with retry logic"""
        for attempt in range(self.max_retries):
            try:
                self.client = ModbusSerialClient(
                    port=self.port,
                    baudrate=self.baudrate,
                    bytesize=self.bytesize,
                    parity=self.parity,
                    stopbits=self.stopbits,
                    timeout=3
                )
                if self.client.connect():
                    print(f"Connected to Modbus RTU device on {self.port} at {self.baudrate} baud")
                    return True
                else:
                    print(f"Connection attempt {attempt + 1}/{self.max_retries} failed")
            except Exception as e:
                print(f"Connection attempt {attempt + 1}/{self.max_retries} failed: {e}")

            self.client = None
            if attempt < self.max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff

        print(f"Failed to connect to Modbus RTU device after {self.max_retries} attempts")
        return False

    def disconnect(self):
        """Disconnect from Modbus RTU device"""
        if self.client:
            try:
                self.client.close()
            except Exception as e:
                print(f"Error disconnecting: {e}")
            finally:
                self.client = None

    def read_sensor_data(self) -> Dict[str, Any]:
        """
        Read sensor data from Modbus RTU registers
        Returns dict of sensor_name: value
        """
        if not self.client or not self.client.is_socket_open():
            self.connect()
            if not self.client or not self.client.is_socket_open():
                return {}

        data = {}
        try:
            for sensor_name, config in self.register_mappings.items():
                address = config["address"]
                reg_type = config.get("type", "holding")
                count = config.get("count", 1)
                scale = config.get("scale", 1.0)

                # Read registers based on type
                if reg_type == "holding":
                    result = self.client.read_holding_registers(
                        address=address,
                        count=count,
                        slave=self.slave_id
                    )
                elif reg_type == "input":
                    result = self.client.read_input_registers(
                        address=address,
                        count=count,
                        slave=self.slave_id
                    )
                else:
                    print(f"Invalid register type '{reg_type}' for sensor '{sensor_name}'")
                    continue

                if result.isError():
                    print(f"Error reading {reg_type} register at address {address}: {result}")
                    continue

                # Process the register value
                if count == 1:
                    # Single 16-bit register
                    raw_value = result.registers[0]
                elif count == 2:
                    # Two 16-bit registers combined into 32-bit value
                    raw_value = (result.registers[0] << 16) | result.registers[1]
                else:
                    print(f"Unsupported register count {count} for sensor '{sensor_name}'")
                    continue

                # Apply scaling factor
                scaled_value = raw_value / scale
                data[sensor_name] = scaled_value

        except Exception as e:
            print(f"Error reading Modbus RTU data: {e}")
            # Try to reconnect on next call
            self.disconnect()

        return data

    def write_register(self, address: int, value: int, reg_type: str = "holding") -> bool:
        """
        Write value to Modbus register
        WARNING: Use with extreme caution in production!
        Context Edge should be READ-ONLY in most deployments.

        Args:
            address: Register address
            value: Value to write (16-bit integer)
            reg_type: Register type ("holding" or "coil")

        Returns:
            True if successful, False otherwise
        """
        if not self.client or not self.client.is_socket_open():
            self.connect()
            if not self.client or not self.client.is_socket_open():
                return False

        try:
            if reg_type == "holding":
                result = self.client.write_register(address, value, slave=self.slave_id)
            elif reg_type == "coil":
                result = self.client.write_coil(address, bool(value), slave=self.slave_id)
            else:
                print(f"Invalid register type '{reg_type}'")
                return False

            if result.isError():
                print(f"Error writing {reg_type} register at address {address}: {result}")
                return False

            print(f"Successfully wrote {value} to {reg_type} register {address}")
            return True

        except Exception as e:
            print(f"Error writing Modbus RTU register: {e}")
            return False

    def __del__(self):
        self.disconnect()

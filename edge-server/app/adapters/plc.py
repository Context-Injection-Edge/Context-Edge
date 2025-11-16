"""
PLC (Programmable Logic Controller) Adapters

Supports:
- Modbus TCP/RTU
- OPC UA
- Ethernet/IP (Allen-Bradley)
- Profinet (Siemens)
- FINS (Omron)
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime

from .base import DataSourceAdapter

logger = logging.getLogger(__name__)


class PLCAdapter(DataSourceAdapter):
    """Base class for PLC adapters"""

    async def connect(self) -> bool:
        """Connect to PLC"""
        raise NotImplementedError

    async def disconnect(self) -> bool:
        """Disconnect from PLC"""
        raise NotImplementedError

    async def read_data(self, identifier: str) -> Dict[str, Any]:
        """Read sensor data from PLC"""
        raise NotImplementedError

    async def write_register(
        self,
        address: int,
        value: float,
        data_type: str = "holding"
    ) -> bool:
        """
        Write value to PLC register (SAFETY-CRITICAL)

        This is where ML recommendations become physical actions!
        ONLY called after operator approval and safety validation.

        Args:
            address: Register address to write
            value: Value to write (will be scaled if needed)
            data_type: Register type ('holding', 'coil', etc.)

        Returns:
            True if write successful, False otherwise
        """
        raise NotImplementedError


class ModbusPLCAdapter(PLCAdapter):
    """
    Modbus TCP/RTU adapter
    Reads sensor data from Modbus registers
    """

    def __init__(self, source_name: str, config: Dict[str, Any]):
        super().__init__(source_name, config)
        self.client = None

    async def connect(self) -> bool:
        """Connect to Modbus PLC"""
        try:
            from pymodbus.client import ModbusTcpClient

            host = self.config.get("host")
            port = self.config.get("port", 502)

            if not host:
                logger.error(f"❌ Modbus adapter {self.source_name}: Missing host")
                return False

            self.client = ModbusTcpClient(host=host, port=port)
            connected = self.client.connect()

            if connected:
                self.is_connected = True
                logger.info(f"✅ Modbus adapter connected: {self.source_name} ({host}:{port})")
                return True
            else:
                logger.error(f"❌ Modbus connection failed: {host}:{port}")
                return False

        except Exception as e:
            logger.error(f"❌ Modbus connection error: {e}")
            return False

    async def disconnect(self) -> bool:
        """Disconnect from Modbus PLC"""
        try:
            if self.client:
                self.client.close()
            self.is_connected = False
            logger.info(f"✅ Modbus adapter disconnected: {self.source_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Modbus disconnect error: {e}")
            return False

    async def read_data(self, identifier: str) -> Dict[str, Any]:
        """
        Read sensor data from Modbus registers

        Args:
            identifier: Device ID (not used for Modbus, uses configured registers)

        Returns:
            Sensor readings from Modbus registers
        """
        if not self.is_connected or not self.client:
            logger.warning(f"⚠️  Modbus adapter not connected: {self.source_name}")
            return {}

        try:
            register_mappings = self.config.get("register_mappings", {})
            unit_id = self.config.get("unit_id", 1)

            sensor_data = {}

            for sensor_name, register_config in register_mappings.items():
                address = register_config.get("address")
                register_type = register_config.get("type", "holding")
                count = register_config.get("count", 1)
                scale = register_config.get("scale", 1.0)

                try:
                    # Read register based on type
                    if register_type == "holding":
                        result = self.client.read_holding_registers(address, count, unit=unit_id)
                    elif register_type == "input":
                        result = self.client.read_input_registers(address, count, unit=unit_id)
                    elif register_type == "coil":
                        result = self.client.read_coils(address, count, unit=unit_id)
                    elif register_type == "discrete":
                        result = self.client.read_discrete_inputs(address, count, unit=unit_id)
                    else:
                        logger.warning(f"⚠️  Unknown register type: {register_type}")
                        continue

                    # Check for errors
                    if result.isError():
                        logger.error(f"❌ Modbus read error for {sensor_name}: {result}")
                        continue

                    # Extract value
                    if hasattr(result, "registers"):
                        raw_value = result.registers[0]
                    elif hasattr(result, "bits"):
                        raw_value = result.bits[0]
                    else:
                        logger.warning(f"⚠️  Unknown result type for {sensor_name}")
                        continue

                    # Apply scale
                    value = raw_value / scale
                    sensor_data[sensor_name] = round(value, 2)

                except Exception as e:
                    logger.error(f"❌ Error reading {sensor_name}: {e}")

            sensor_data["timestamp"] = datetime.now().isoformat()
            logger.info(f"✅ Modbus data read: {len(sensor_data)-1} sensors")
            return sensor_data

        except Exception as e:
            logger.error(f"❌ Modbus read error: {e}", exc_info=True)
            return {}

    async def write_register(
        self,
        address: int,
        value: float,
        data_type: str = "holding"
    ) -> bool:
        """
        Write value to PLC register (SAFETY-CRITICAL)

        This method executes approved ML recommendations by writing to PLC registers.

        SAFETY NOTES:
        - Only called AFTER operator approval
        - Only called AFTER range validation
        - PLC logic provides final safety gate (Safety Gate 3)

        Args:
            address: Modbus register address (e.g., 40001)
            value: Value to write (will be converted to integer)
            data_type: Register type (default: 'holding')

        Returns:
            True if write successful, False otherwise
        """
        if not self.is_connected or not self.client:
            logger.error("❌ Cannot write - Modbus adapter not connected")
            return False

        try:
            unit_id = self.config.get("unit_id", 1)

            # Convert to integer (Modbus registers are 16-bit integers)
            int_value = int(value)

            logger.info(f"📝 SAFETY-CRITICAL WRITE: Modbus Register {address} = {int_value} (unit={unit_id})")

            # Write to register based on type
            if data_type == "holding":
                result = self.client.write_register(address, int_value, unit=unit_id)
            elif data_type == "coil":
                bool_value = bool(int_value)
                result = self.client.write_coil(address, bool_value, unit=unit_id)
            else:
                logger.error(f"❌ Unsupported write type: {data_type}")
                return False

            # Check result
            if result.isError():
                logger.error(f"❌ Modbus write error: {result}")
                return False

            logger.info(f"✅ PLC write successful: Register {address} = {int_value}")
            return True

        except Exception as e:
            logger.error(f"❌ PLC write failed: {e}", exc_info=True)
            return False


class OPCUAPLCAdapter(PLCAdapter):
    """
    OPC UA adapter
    Reads sensor data from OPC UA server
    """

    def __init__(self, source_name: str, config: Dict[str, Any]):
        super().__init__(source_name, config)
        self.client = None

    async def connect(self) -> bool:
        """Connect to OPC UA server"""
        try:
            from opcua import Client

            server_url = self.config.get("server_url")

            if not server_url:
                logger.error(f"❌ OPC UA adapter {self.source_name}: Missing server_url")
                return False

            self.client = Client(server_url)
            self.client.connect()

            self.is_connected = True
            logger.info(f"✅ OPC UA adapter connected: {self.source_name} ({server_url})")
            return True

        except Exception as e:
            logger.error(f"❌ OPC UA connection error: {e}")
            return False

    async def disconnect(self) -> bool:
        """Disconnect from OPC UA server"""
        try:
            if self.client:
                self.client.disconnect()
            self.is_connected = False
            logger.info(f"✅ OPC UA adapter disconnected: {self.source_name}")
            return True
        except Exception as e:
            logger.error(f"❌ OPC UA disconnect error: {e}")
            return False

    async def read_data(self, identifier: str) -> Dict[str, Any]:
        """
        Read sensor data from OPC UA nodes

        Args:
            identifier: Device ID (not used, uses configured nodes)

        Returns:
            Sensor readings from OPC UA nodes
        """
        if not self.is_connected or not self.client:
            logger.warning(f"⚠️  OPC UA adapter not connected: {self.source_name}")
            return {}

        try:
            node_mappings = self.config.get("node_mappings", {})

            sensor_data = {}

            for sensor_name, node_id in node_mappings.items():
                try:
                    node = self.client.get_node(node_id)
                    value = node.get_value()
                    sensor_data[sensor_name] = float(value) if value is not None else None

                except Exception as e:
                    logger.error(f"❌ Error reading OPC UA node {sensor_name} ({node_id}): {e}")

            sensor_data["timestamp"] = datetime.now().isoformat()
            logger.info(f"✅ OPC UA data read: {len(sensor_data)-1} nodes")
            return sensor_data

        except Exception as e:
            logger.error(f"❌ OPC UA read error: {e}", exc_info=True)
            return {}

    async def write_register(
        self,
        address: int,
        value: float,
        data_type: str = "holding"
    ) -> bool:
        """
        Write value to OPC UA node (SAFETY-CRITICAL)

        This method executes approved ML recommendations by writing to OPC UA nodes.

        SAFETY NOTES:
        - Only called AFTER operator approval
        - Only called AFTER range validation
        - PLC logic provides final safety gate (Safety Gate 3)

        Args:
            address: Node ID or parameter name (will be mapped to node)
            value: Value to write
            data_type: Not used for OPC UA (included for interface compatibility)

        Returns:
            True if write successful, False otherwise
        """
        if not self.is_connected or not self.client:
            logger.error("❌ Cannot write - OPC UA adapter not connected")
            return False

        try:
            # Map parameter name to node ID if needed
            node_mappings = self.config.get("node_mappings", {})

            # If address is a parameter name, look up the node ID
            if isinstance(address, str) and address in node_mappings:
                node_id = node_mappings[address]
            else:
                # Assume address is already a node ID
                node_id = str(address)

            logger.info(f"📝 SAFETY-CRITICAL WRITE: OPC UA Node {node_id} = {value}")

            # Get the node and write value
            node = self.client.get_node(node_id)
            node.set_value(value)

            logger.info(f"✅ PLC write successful: Node {node_id} = {value}")
            return True

        except Exception as e:
            logger.error(f"❌ PLC write failed: {e}", exc_info=True)
            return False


class EthernetIPAdapter(PLCAdapter):
    """
    Ethernet/IP adapter (Allen-Bradley)
    Uses pycomm3 library for Rockwell PLCs
    """

    def __init__(self, source_name: str, config: Dict[str, Any]):
        super().__init__(source_name, config)
        self.client = None

    async def connect(self) -> bool:
        """Connect to Allen-Bradley PLC via Ethernet/IP"""
        try:
            # TODO: Implement pycomm3 integration
            # from pycomm3 import LogixDriver
            # self.client = LogixDriver(self.config.get("host"))
            # self.client.open()

            logger.warning("⚠️  Ethernet/IP adapter not yet implemented (requires pycomm3)")
            return False

        except Exception as e:
            logger.error(f"❌ Ethernet/IP connection error: {e}")
            return False

    async def disconnect(self) -> bool:
        """Disconnect from PLC"""
        return True

    async def read_data(self, identifier: str) -> Dict[str, Any]:
        """Read tags from Allen-Bradley PLC"""
        logger.warning("⚠️  Ethernet/IP read not yet implemented")
        return {}

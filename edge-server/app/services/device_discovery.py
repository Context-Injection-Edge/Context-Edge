"""
Device Discovery Service
Auto-discovers industrial devices on the network (PLCs, MES, ERP, SCADA)
"""

import asyncio
import socket
import logging
import ipaddress
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DeviceDiscoveryService:
    """
    Auto-discover industrial devices on network

    Supports:
    - Modbus TCP devices (port 502)
    - OPC UA servers (port 4840)
    - HTTP/REST APIs (ports 80, 443)
    """

    def __init__(self):
        self.timeout = 2  # Connection timeout in seconds

    async def scan_network(
        self,
        subnet: str = "192.168.1.0/24",
        protocols: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Scan network for industrial devices

        Args:
            subnet: Network range (CIDR notation, e.g., "192.168.1.0/24")
            protocols: List of protocols to scan ["modbus", "opcua", "http"]
                      If None, scans all protocols

        Returns:
            List of discovered devices with metadata
        """
        logger.info(f"🔍 Starting network scan: {subnet}")

        if protocols is None:
            protocols = ["modbus", "opcua", "http"]

        # Generate IP addresses from subnet
        ips = self._generate_ip_range(subnet)
        logger.info(f"📡 Scanning {len(ips)} IP addresses for {protocols}")

        devices = []
        scan_tasks = []

        # Create scan tasks for each protocol
        for ip in ips:
            if "modbus" in protocols:
                scan_tasks.append(self._scan_modbus(ip))

            if "opcua" in protocols:
                scan_tasks.append(self._scan_opcua(ip))

            if "http" in protocols:
                scan_tasks.append(self._scan_http(ip))

        # Execute all scans in parallel (fast!)
        logger.info(f"⚡ Running {len(scan_tasks)} scan tasks in parallel...")
        results = await asyncio.gather(*scan_tasks, return_exceptions=True)

        # Filter out None and exceptions
        devices = [
            device for device in results
            if device and not isinstance(device, Exception)
        ]

        logger.info(f"✅ Network scan complete: Found {len(devices)} devices")
        return devices

    def _generate_ip_range(self, subnet: str) -> List[str]:
        """
        Generate list of IP addresses from CIDR subnet

        Args:
            subnet: CIDR notation (e.g., "192.168.1.0/24")

        Returns:
            List of IP addresses as strings
        """
        try:
            network = ipaddress.ip_network(subnet, strict=False)
            # Limit to 254 hosts max (avoid scanning huge networks)
            ips = [str(ip) for ip in list(network.hosts())[:254]]
            return ips
        except ValueError as e:
            logger.error(f"❌ Invalid subnet: {subnet} - {e}")
            return []

    async def _scan_modbus(self, ip: str, port: int = 502) -> Optional[Dict[str, Any]]:
        """
        Try to connect to Modbus TCP device

        Args:
            ip: IP address to scan
            port: Modbus TCP port (default 502)

        Returns:
            Device info dict if Modbus device found, None otherwise
        """
        try:
            # Try TCP connection to Modbus port
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=self.timeout
            )

            # Close connection immediately (just checking if port is open)
            writer.close()
            await writer.wait_closed()

            logger.info(f"✅ Modbus device found: {ip}:{port}")

            # Try to determine vendor (simplified version)
            vendor_info = await self._identify_modbus_vendor(ip, port)

            return {
                "ip": ip,
                "port": port,
                "protocol": "modbus_tcp",
                "vendor": vendor_info.get("vendor", "Unknown"),
                "model": vendor_info.get("model", "Modbus TCP Device"),
                "device_type": "plc",
                "recommended_template": vendor_info.get("template", "modbus_generic"),
                "discovered_at": datetime.now().isoformat()
            }

        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            # No Modbus device at this IP
            return None
        except Exception as e:
            logger.debug(f"Error scanning {ip}:{port} - {e}")
            return None

    async def _identify_modbus_vendor(self, ip: str, port: int) -> Dict[str, str]:
        """
        Try to identify Modbus vendor by reading device identification

        This is a simplified version. In production, would use pymodbus
        to read vendor ID registers.

        Args:
            ip: Device IP
            port: Modbus port

        Returns:
            Dict with vendor, model, template
        """
        # Placeholder for vendor detection
        # In production, would:
        # 1. Connect with pymodbus
        # 2. Read device identification (function code 0x2B/0x0E)
        # 3. Parse vendor ID, product code, revision
        # 4. Map to known vendors

        # For now, return generic
        return {
            "vendor": "Unknown",
            "model": "Modbus TCP Device",
            "template": "modbus_generic"
        }

    async def _scan_opcua(self, ip: str, port: int = 4840) -> Optional[Dict[str, Any]]:
        """
        Try to connect to OPC UA server

        Args:
            ip: IP address to scan
            port: OPC UA port (default 4840)

        Returns:
            Device info dict if OPC UA server found, None otherwise
        """
        try:
            # Try TCP connection to OPC UA port
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=self.timeout
            )

            writer.close()
            await writer.wait_closed()

            logger.info(f"✅ OPC UA server found: {ip}:{port}")

            server_url = f"opc.tcp://{ip}:{port}"

            # Try to get server info
            server_info = await self._identify_opcua_server(ip, port)

            return {
                "ip": ip,
                "port": port,
                "protocol": "opcua",
                "server_url": server_url,
                "vendor": server_info.get("vendor", "Unknown"),
                "model": server_info.get("model", "OPC UA Server"),
                "device_type": "plc",
                "recommended_template": server_info.get("template", "opcua_generic"),
                "discovered_at": datetime.now().isoformat()
            }

        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            return None
        except Exception as e:
            logger.debug(f"Error scanning OPC UA {ip}:{port} - {e}")
            return None

    async def _identify_opcua_server(self, ip: str, port: int) -> Dict[str, str]:
        """
        Try to identify OPC UA server vendor

        Args:
            ip: Server IP
            port: OPC UA port

        Returns:
            Dict with vendor, model, template
        """
        # Placeholder - in production would use opcua library to:
        # 1. Connect to server
        # 2. Read ServerStatus node
        # 3. Get ApplicationName, ProductName, etc.
        # 4. Map to known vendors (Siemens, B&R, etc.)

        return {
            "vendor": "Unknown",
            "model": "OPC UA Server",
            "template": "opcua_generic"
        }

    async def _scan_http(self, ip: str) -> Optional[Dict[str, Any]]:
        """
        Try to detect HTTP/REST API servers (MES, ERP, SCADA)

        Args:
            ip: IP address to scan

        Returns:
            Device info dict if HTTP server found, None otherwise
        """
        # Try common HTTP ports
        ports = [80, 8080, 443, 8443]

        for port in ports:
            try:
                # Try TCP connection
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, port),
                    timeout=self.timeout
                )

                writer.close()
                await writer.wait_closed()

                logger.info(f"✅ HTTP server found: {ip}:{port}")

                # Try to identify server type
                server_info = await self._identify_http_server(ip, port)

                if server_info:
                    return {
                        "ip": ip,
                        "port": port,
                        "protocol": "http",
                        "base_url": f"http://{ip}:{port}",
                        "vendor": server_info.get("vendor", "Unknown"),
                        "model": server_info.get("model", "HTTP Server"),
                        "device_type": server_info.get("device_type", "mes"),
                        "recommended_template": server_info.get("template", "http_generic"),
                        "discovered_at": datetime.now().isoformat()
                    }

            except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                continue
            except Exception as e:
                logger.debug(f"Error scanning HTTP {ip}:{port} - {e}")
                continue

        return None

    async def _identify_http_server(self, ip: str, port: int) -> Optional[Dict[str, str]]:
        """
        Try to identify HTTP server type (MES, ERP, SCADA)

        Args:
            ip: Server IP
            port: HTTP port

        Returns:
            Dict with vendor, model, device_type, template
        """
        # Placeholder - in production would use httpx to:
        # 1. Send HTTP GET request
        # 2. Check Server header
        # 3. Check common paths (/api, /scada, /mes)
        # 4. Identify Wonderware, Ignition, SAP, etc.

        # For now, return None (don't auto-discover HTTP servers)
        # User can add them manually
        return None

    async def test_connection(
        self,
        device: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Test connection to a device with specific configuration

        Args:
            device: Device info from scan
            config: Configuration to test (sensor mappings, etc.)

        Returns:
            Test result with live data if successful
        """
        protocol = device.get("protocol")

        if protocol == "modbus_tcp":
            return await self._test_modbus_connection(device, config)
        elif protocol == "opcua":
            return await self._test_opcua_connection(device, config)
        elif protocol == "http":
            return await self._test_http_connection(device, config)
        else:
            return {
                "success": False,
                "error": f"Unsupported protocol: {protocol}"
            }

    async def _test_modbus_connection(
        self,
        device: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test Modbus connection and read sample data"""
        try:
            from pymodbus.client import ModbusTcpClient

            client = ModbusTcpClient(
                host=device["ip"],
                port=device.get("port", 502),
                timeout=3
            )

            if not client.connect():
                return {
                    "success": False,
                    "error": "Connection failed"
                }

            # Try to read some registers from config
            sensor_mappings = config.get("sensor_mappings", {})
            sample_data = {}

            for sensor_name, sensor_config in list(sensor_mappings.items())[:3]:
                try:
                    address = sensor_config.get("address", 0)
                    result = client.read_holding_registers(address, 1, unit=1)

                    if not result.isError():
                        raw_value = result.registers[0]
                        scale = sensor_config.get("scale", 1.0)
                        value = raw_value / scale
                        sample_data[sensor_name] = round(value, 2)
                except Exception as e:
                    sample_data[sensor_name] = f"Error: {e}"

            client.close()

            return {
                "success": True,
                "sample_data": sample_data,
                "message": "Connection successful"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def _test_opcua_connection(
        self,
        device: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test OPC UA connection and read sample data"""
        try:
            from opcua import Client

            server_url = device.get("server_url")
            client = Client(server_url, timeout=3)
            client.connect()

            # Try to read some nodes from config
            node_mappings = config.get("node_mappings", {})
            sample_data = {}

            for sensor_name, node_id in list(node_mappings.items())[:3]:
                try:
                    node = client.get_node(node_id)
                    value = node.get_value()
                    sample_data[sensor_name] = float(value) if value is not None else None
                except Exception as e:
                    sample_data[sensor_name] = f"Error: {e}"

            client.disconnect()

            return {
                "success": True,
                "sample_data": sample_data,
                "message": "Connection successful"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def _test_http_connection(
        self,
        device: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test HTTP connection and read sample data"""
        try:
            import httpx

            base_url = device.get("base_url")

            async with httpx.AsyncClient(timeout=3.0) as client:
                # Try to connect to base URL
                response = await client.get(base_url)

                return {
                    "success": response.status_code < 400,
                    "status_code": response.status_code,
                    "message": "Connection successful" if response.status_code < 400 else "Connection failed"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

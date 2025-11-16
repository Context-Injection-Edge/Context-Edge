"""
Base Data Source Adapter
All data source adapters (PLC, MES, ERP, SCADA, Historian) inherit from this
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataSourceAdapter(ABC):
    """
    Base class for all data source adapters

    This provides a unified interface for reading data from:
    - PLCs (Modbus, OPC UA, Ethernet/IP)
    - MES systems (Wonderware, Siemens Opcenter, Rockwell FactoryTalk)
    - ERP systems (SAP, Oracle, Microsoft Dynamics)
    - SCADA systems (Ignition, WinCC)
    - Historians (OSIsoft PI, Wonderware Historian)
    """

    def __init__(self, source_name: str, config: Dict[str, Any]):
        """
        Initialize adapter

        Args:
            source_name: Human-readable name (e.g., "Modbus-PLC-Line1")
            config: Configuration dictionary specific to this adapter
        """
        self.source_name = source_name
        self.config = config
        self.is_connected = False
        logger.info(f"🔧 Initializing {self.__class__.__name__}: {source_name}")

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to data source

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Close connection to data source

        Returns:
            True if disconnection successful, False otherwise
        """
        pass

    @abstractmethod
    async def read_data(self, identifier: str) -> Dict[str, Any]:
        """
        Read data from the source

        Args:
            identifier: Source-specific identifier (device_id, work_order, etc.)

        Returns:
            Dictionary of data readings
        """
        pass

    async def health_check(self) -> bool:
        """
        Check if adapter is healthy and connected

        Returns:
            True if healthy, False otherwise
        """
        return self.is_connected

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get adapter metadata for logging/debugging

        Returns:
            Metadata dictionary
        """
        return {
            "adapter_type": self.__class__.__name__,
            "source_name": self.source_name,
            "is_connected": self.is_connected,
            "config": {k: v for k, v in self.config.items() if k not in ["password", "api_key", "secret"]}
        }


class MockDataSourceAdapter(DataSourceAdapter):
    """
    Mock adapter for testing without real data sources
    Generates realistic test data
    """

    async def connect(self) -> bool:
        """Mock connection always succeeds"""
        self.is_connected = True
        logger.info(f"✅ Mock adapter connected: {self.source_name}")
        return True

    async def disconnect(self) -> bool:
        """Mock disconnection"""
        self.is_connected = False
        logger.info(f"✅ Mock adapter disconnected: {self.source_name}")
        return True

    async def read_data(self, identifier: str) -> Dict[str, Any]:
        """Generate mock data based on adapter type"""
        import random

        # Generate timestamp
        timestamp = datetime.now().isoformat()

        # Return mock data with timestamp
        return {
            "mock": True,
            "source": self.source_name,
            "identifier": identifier,
            "timestamp": timestamp,
            "data": self.config.get("mock_data", {})
        }

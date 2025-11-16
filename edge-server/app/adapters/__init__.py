"""
Data Source Adapters

Unified interface for reading data from multiple sources:
- PLCs (Modbus, OPC UA, Ethernet/IP)
- MES (Wonderware, Siemens Opcenter, Rockwell FactoryTalk)
- ERP (SAP, Oracle, Microsoft Dynamics)
- SCADA (Ignition, WinCC, Wonderware)
- Historians (OSIsoft PI, Wonderware Historian, InfluxDB)
"""

from .base import DataSourceAdapter, MockDataSourceAdapter
from .plc import ModbusPLCAdapter, OPCUAPLCAdapter, EthernetIPAdapter
from .mes import MESAdapter, WonderwareMESAdapter, SiemensOpcenterAdapter, RockwellFactoryTalkAdapter
from .erp import ERPAdapter, SAPAdapter, OracleERPAdapter, MicrosoftDynamicsAdapter
from .scada import SCADAAdapter, IgnitionAdapter, SiemensWinCCAdapter, WonderwareSCADAAdapter
from .historian import HistorianAdapter, OSIsoftPIAdapter, WonderwareHistorianAdapter, InfluxDBAdapter

__all__ = [
    # Base
    "DataSourceAdapter",
    "MockDataSourceAdapter",

    # PLC Adapters
    "ModbusPLCAdapter",
    "OPCUAPLCAdapter",
    "EthernetIPAdapter",

    # MES Adapters
    "MESAdapter",
    "WonderwareMESAdapter",
    "SiemensOpcenterAdapter",
    "RockwellFactoryTalkAdapter",

    # ERP Adapters
    "ERPAdapter",
    "SAPAdapter",
    "OracleERPAdapter",
    "MicrosoftDynamicsAdapter",

    # SCADA Adapters
    "SCADAAdapter",
    "IgnitionAdapter",
    "SiemensWinCCAdapter",
    "WonderwareSCADAAdapter",

    # Historian Adapters
    "HistorianAdapter",
    "OSIsoftPIAdapter",
    "WonderwareHistorianAdapter",
    "InfluxDBAdapter",
]

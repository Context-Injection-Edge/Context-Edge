from datetime import datetime
import random

MOCK_ADAPTER_CONFIGS = [
    {
        "adapter_type": "modbus",
        "source_name": "Mock-Modbus-PLC-Line1",
        "config": {
            "host": "192.168.1.100",
            "port": 502,
            "unit_id": 1,
            "register_mappings": {
                "temperature": {"address": 0, "type": "holding", "count": 1, "scale": 100.0},
                "vibration": {"address": 2, "type": "holding", "count": 1, "scale": 100.0},
            }
        },
        "mock_data": {
            "temperature": round(random.gauss(75.0, 5.0), 2),
            "vibration": round(random.gauss(3.0, 0.5), 2),
            "timestamp": datetime.now().isoformat()
        }
    },
    {
        "adapter_type": "opcua",
        "source_name": "Mock-OPCUA-Server-Mixer",
        "config": {
            "server_url": "opc.tcp://192.168.1.101:4840",
            "node_mappings": {
                "pressure": "ns=2;i=1003",
                "flow_rate": "ns=2;i=1006",
            }
        },
        "mock_data": {
            "pressure": round(random.gauss(100.0, 10.0), 2),
            "flow_rate": round(random.gauss(500.0, 20.0), 2),
            "timestamp": datetime.now().isoformat()
        }
    },
    {
        "adapter_type": "mes",
        "source_name": "Mock-MES-System",
        "config": {
            "base_url": "http://mock-mes:8080",
            "api_key": "mock_key"
        },
        "mock_data": {
            "work_order": f"WO-{random.randint(10000, 99999)}",
            "production_count": random.randint(50, 200),
            "oee": round(random.uniform(0.75, 0.95), 2),
            "timestamp": datetime.now().isoformat()
        }
    },
    {
        "adapter_type": "erp",
        "source_name": "Mock-ERP-SAP",
        "config": {
            "base_url": "http://mock-erp:8000",
            "username": "mock_user"
        },
        "mock_data": {
            "material_number": f"MAT-{random.randint(1000, 9999)}",
            "batch_number": f"BATCH-{random.randint(100, 999)}",
            "timestamp": datetime.now().isoformat()
        }
    }
]

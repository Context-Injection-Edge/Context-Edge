from datetime import datetime

MOCK_DISCOVERED_DEVICES = [
    {
        "ip": "192.168.1.100",
        "port": 502,
        "protocol": "modbus_tcp",
        "vendor": "MockCo",
        "model": "Mock Modbus PLC",
        "device_type": "plc",
        "recommended_template": "modbus_generic",
        "discovered_at": datetime.now().isoformat()
    },
    {
        "ip": "192.168.1.101",
        "port": 4840,
        "protocol": "opcua",
        "server_url": "opc.tcp://192.168.1.101:4840",
        "vendor": "SimulatedCorp",
        "model": "Simulated OPC UA Server",
        "device_type": "plc",
        "recommended_template": "opcua_generic",
        "discovered_at": datetime.now().isoformat()
    },
    {
        "ip": "192.168.1.102",
        "port": 8080,
        "protocol": "http",
        "base_url": "http://192.168.1.102:8080",
        "vendor": "MockMES",
        "model": "Mock MES API",
        "device_type": "mes",
        "recommended_template": "mes_generic",
        "discovered_at": datetime.now().isoformat()
    },
    {
        "ip": "192.168.1.103",
        "port": 8000,
        "protocol": "http",
        "base_url": "http://192.168.1.103:8000",
        "vendor": "MockERP",
        "model": "Mock ERP API",
        "device_type": "erp",
        "recommended_template": "erp_generic",
        "discovered_at": datetime.now().isoformat()
    }
]

MOCK_TEST_CONNECTION_RESULTS = {
    "success": True,
    "sample_data": {
        "temperature": 78.5,
        "pressure": 92.1,
        "work_order_id": "WO-MOCK-123"
    },
    "message": "Mock connection successful, returning sample data."
}

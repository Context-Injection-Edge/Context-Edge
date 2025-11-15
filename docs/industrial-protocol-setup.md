# Industrial Protocol Setup Guide

Guide for configuring OPC UA and Modbus protocols with Context Edge.

---

## OPC UA Configuration

### Basic Setup

```python
from context_edge.opcua_protocol import OPCUAProtocol
from context_edge.context_injector import ContextInjectionModule

# Define node mappings (sensor name → OPC UA node ID)
node_mappings = {
    "vibration_x": "ns=2;i=1001",      # Vibration X-axis
    "vibration_y": "ns=2;i=1002",      # Vibration Y-axis
    "temperature": "ns=2;i=1003",      # Motor temperature
    "current": "ns=2;i=1004",          # Motor current
}

# Initialize OPC UA protocol
opcua = OPCUAProtocol(
    server_url="opc.tcp://192.168.1.100:4840",
    node_mappings=node_mappings,
    max_retries=3  # Retry 3 times with exponential backoff
)

# Connect to OPC UA server
if opcua.connect():
    print("Connected successfully")
else:
    print("Failed to connect after retries")

# Use with CIM
cim = ContextInjectionModule(
    context_service_url="http://localhost:8000",
    redis_host="localhost",
    data_protocol=opcua  # Pass OPC UA as data source
)

# CIM will automatically read from OPC UA
ldo = cim.inject_context(detected_cid="QR001")
print(ldo)
```

### Finding OPC UA Node IDs

Use `opcua-client` or UaExpert to browse your OPC UA server:

```bash
# Install OPC UA client
pip install opcua-client

# Browse server nodes
python -c "
from opcua import Client
client = Client('opc.tcp://192.168.1.100:4840')
client.connect()
root = client.get_root_node()
print('Objects node:', root.get_child(['0:Objects']))
client.disconnect()
"
```

---

## Modbus Configuration

### Basic Setup

```python
from context_edge.modbus_protocol import ModbusProtocol
from context_edge.context_injector import ContextInjectionModule

# Define register mappings
register_mappings = {
    "temperature": {
        "address": 0,           # Register address
        "type": "holding",      # "holding" or "input"
        "count": 1,             # 1 for 16-bit, 2 for 32-bit
        "scale": 10.0          # Divide by 10 to get actual value
    },
    "pressure": {
        "address": 2,
        "type": "holding",
        "count": 1,
        "scale": 100.0         # Divide by 100
    },
    "flow_rate": {
        "address": 4,
        "type": "input",       # Input register
        "count": 2,            # 32-bit value (2 registers)
        "scale": 1000.0
    }
}

# Initialize Modbus protocol
modbus = ModbusProtocol(
    host="192.168.1.200",
    port=502,
    register_mappings=register_mappings,
    max_retries=3
)

# Connect to Modbus server
if modbus.connect():
    print("Connected successfully")

# Use with CIM
cim = ContextInjectionModule(
    context_service_url="http://localhost:8000",
    data_protocol=modbus
)

# CIM will automatically read from Modbus
ldo = cim.inject_context(detected_cid="QR002")
```

### Determining Scaling Factors

Modbus registers are 16-bit integers. Scaling converts them to real values:

| Sensor Type | Register Value | Scale | Actual Value |
|-------------|----------------|-------|--------------|
| Temperature | 235 | 10.0 | 23.5°C |
| Pressure | 15000 | 100.0 | 150.00 bar |
| Flow Rate | 50000 | 1000.0 | 50.000 L/min |

**How to find the scale:**
1. Check your PLC documentation
2. Or: Read known value, compare to actual measurement
3. Example: Register shows 1250, actual temp is 12.5°C → scale = 100

---

## Complete CIM Example with Industrial Protocols

### Full Integration

```python
from context_edge.opcua_protocol import OPCUAProtocol
from context_edge.modbus_protocol import ModbusProtocol
from context_edge.context_injector import ContextInjectionModule
from context_edge.qr_decoder import QRDecoder
import time

# Choose your protocol
USE_OPCUA = True  # Set to False for Modbus

if USE_OPCUA:
    # OPC UA setup
    protocol = OPCUAProtocol(
        server_url="opc.tcp://192.168.1.100:4840",
        node_mappings={
            "vibration": "ns=2;i=1001",
            "temperature": "ns=2;i=1002"
        }
    )
else:
    # Modbus setup
    protocol = ModbusProtocol(
        host="192.168.1.200",
        port=502,
        register_mappings={
            "vibration": {"address": 0, "type": "holding", "count": 1, "scale": 100.0},
            "temperature": {"address": 1, "type": "holding", "count": 1, "scale": 10.0}
        }
    )

# Connect to protocol
if not protocol.connect():
    print("Failed to connect to industrial protocol!")
    exit(1)

# Initialize CIM with protocol
cim = ContextInjectionModule(
    context_service_url="http://localhost:8000",
    redis_host="localhost",
    data_protocol=protocol
)

# Initialize QR decoder
qr_decoder = QRDecoder()

# Main loop
while True:
    # Detect QR code from camera (simplified)
    detected_cid = qr_decoder.detect_qr()  # Returns CID or None

    # Inject context (reads from protocol automatically)
    ldo = cim.inject_context(detected_cid=detected_cid)

    print(f"Sensor Data: {ldo['sensor_data']}")
    print(f"Context: {ldo['context_metadata']}")
    print(f"Industrial Context: {ldo['industrial_context']}")

    # Upload LDO to data ingestion service
    # upload_ldo(ldo)

    time.sleep(1)
```

---

## Populating Redis Context Store

### Asset Master Data

```bash
curl -X POST http://localhost:8000/context/assets \
  -H "Content-Type: application/json" \
  -d '{
    "asset_id": "MOTOR-001",
    "location": "Production Line 3, Station 5",
    "model_number": "ABB-M3000",
    "safety_rules": {
      "max_temp": 85.0,
      "max_vibration": 2.5,
      "maintenance_interval_hours": 2000
    }
  }'
```

### Operating Thresholds

```bash
curl -X POST http://localhost:8000/context/thresholds \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_type": "vibration",
    "warning_low": 0.5,
    "warning_high": 1.5,
    "critical_low": 0.3,
    "critical_high": 2.0,
    "unit": "g"
  }'
```

### Runtime State

```bash
curl -X POST http://localhost:8000/context/runtime \
  -H "Content-Type: application/json" \
  -d '{
    "production_order_id": "ORDER-5002",
    "current_recipe": "High-Speed Stamping",
    "time_since_maintenance": 1850
  }'
```

### AI Model Metadata

```bash
curl -X POST http://localhost:8000/context/models \
  -H "Content-Type: application/json" \
  -d '{
    "version_id": "v1.2.3",
    "confidence_threshold": 0.85,
    "model_type": "anomaly_detection",
    "last_updated": "2025-11-15T10:30:00Z"
  }'
```

---

## Example: Enhanced LDO with Industrial Context

When you configure everything correctly, CIM generates LDOs like this:

```json
{
  "sensor_data": {
    "vibration": 1.7,
    "temperature": 72.3
  },
  "context_metadata": {
    "cid": "QR001",
    "metadata": {
      "product_name": "Widget A",
      "batch_number": "BATCH001"
    }
  },
  "industrial_context": {
    "asset": {
      "asset_id": "MOTOR-001",
      "location": "Production Line 3, Station 5",
      "model_number": "ABB-M3000"
    },
    "thresholds": {
      "vibration": {
        "warning_high": 1.5,
        "critical_high": 2.0,
        "unit": "g"
      },
      "temperature": {
        "warning_high": 75.0,
        "critical_high": 85.0,
        "unit": "C"
      }
    },
    "runtime": {
      "production_order_id": "ORDER-5002",
      "current_recipe": "High-Speed Stamping",
      "time_since_maintenance": 1850
    },
    "model": {
      "version_id": "v1.2.3",
      "confidence_threshold": 0.85
    }
  },
  "timestamp": 1700048400.123,
  "cid": "QR001"
}
```

This LDO can now answer questions like:
- **"Is vibration normal?"** → 1.7g exceeds warning threshold of 1.5g
- **"When was last maintenance?"** → 1850 hours ago (close to 2000hr interval)
- **"What model version detected this?"** → v1.2.3 with 85% confidence threshold

---

## Troubleshooting

### OPC UA Connection Issues

```python
# Test OPC UA connection
from opcua import Client

client = Client("opc.tcp://192.168.1.100:4840")
try:
    client.connect()
    print("Connected successfully!")

    # Test reading a node
    node = client.get_node("ns=2;i=1001")
    value = node.get_value()
    print(f"Node value: {value}")

    client.disconnect()
except Exception as e:
    print(f"Error: {e}")
```

**Common Issues:**
- Firewall blocking port 4840
- Wrong node IDs (use UaExpert to browse)
- OPC UA server not running
- Security policy mismatch

### Modbus Connection Issues

```python
# Test Modbus connection
from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient("192.168.1.200", port=502)
if client.connect():
    print("Connected!")

    # Read holding register 0
    result = client.read_holding_registers(0, 1)
    if not result.isError():
        print(f"Register 0 value: {result.registers[0]}")

    client.close()
else:
    print("Connection failed")
```

**Common Issues:**
- Firewall blocking port 502
- Wrong register addresses
- Wrong register type (holding vs input)
- PLC not configured for Modbus TCP

---

## Performance Tuning

### Reducing Latency

```python
# Read only essential sensors
node_mappings = {
    "critical_sensor": "ns=2;i=1001"  # Only read what you need
}

# Increase Redis cache TTL for stable metadata
cim.cache_ttl = 7200  # 2 hours instead of 1 hour
```

### Handling High-Frequency Data

```python
# Sample every Nth reading
sample_counter = 0
SAMPLE_RATE = 10  # Process every 10th reading

while True:
    sample_counter += 1
    if sample_counter % SAMPLE_RATE == 0:
        ldo = cim.inject_context(detected_cid=current_cid)
        upload_ldo(ldo)
```

---

## Security Considerations

1. **Use VPN/Firewall** for OPC UA/Modbus traffic
2. **Separate networks** for OT and IT
3. **Read-only access** for Context Edge (don't write to PLCs)
4. **Monitor anomalies** in industrial protocol traffic

---

## Next Steps

1. Configure your protocol (OPC UA or Modbus)
2. Populate Redis Context Store with assets, thresholds, runtime state
3. Test with CIM
4. Integrate with full pipeline (QR decoder → CIM → Data Ingestion)

For questions, see `CODE-REVIEW-KILO.md` and `FIXES-SUMMARY.md`.

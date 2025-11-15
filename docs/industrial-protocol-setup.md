# Industrial Protocol Setup Guide

Guide for configuring industrial protocols with Context Edge.

**Supported Protocols:**
- ✅ **OPC UA** - Universal protocol (Siemens, Allen-Bradley, ABB, B&R)
- ✅ **Modbus TCP** - Legacy PLCs, distributed I/O
- ✅ **EtherNet/IP** - Allen-Bradley, Rockwell Automation
- ✅ **PROFINET/S7** - Siemens S7-300/400/1200/1500 PLCs
- ✅ **Modbus RTU** - Serial communication (RS-232/RS-485)

**Market Coverage:** 85%+ of industrial PLCs worldwide

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

---

## EtherNet/IP Configuration

### Basic Setup (Allen-Bradley / Rockwell Automation)

```python
from context_edge.ethernetip_protocol import EtherNetIPProtocol
from context_edge.context_injector import ContextInjectionModule

# Define tag mappings (sensor name → PLC tag name)
tag_mappings = {
    "vibration_x": "Motor1_VibrationX",
    "temperature": "Motor1_Temp",
    "current": "Motor1_Current",
    "speed": "Conveyor1_Speed"
}

# Initialize EtherNet/IP protocol
ethernetip = EtherNetIPProtocol(
    host="192.168.1.10",  # PLC IP address
    tag_mappings=tag_mappings,
    port=44818,  # Default for ControlLogix/CompactLogix
    max_retries=3
)

# Connect to PLC
if ethernetip.connect():
    print("Connected to Allen-Bradley PLC")
else:
    print("Failed to connect")

# Use with CIM
cim = ContextInjectionModule(
    context_service_url="http://localhost:8000",
    redis_host="localhost",
    data_protocol=ethernetip
)

# CIM will automatically read from EtherNet/IP
ldo = cim.inject_context(detected_cid="QR003")
print(ldo)
```

### Finding PLC Tag Names

Use Rockwell Studio 5000 or RSLogix 5000:

```
1. Open Studio 5000
2. Connect to PLC
3. Go to Controller Tags
4. Browse available tags:
   - Motor1_Temp (REAL)
   - Motor1_VibrationX (REAL)
   - Conveyor1_Speed (DINT)
5. Copy tag names exactly (case-sensitive!)
```

**Common Tag Naming Conventions:**
- `Motor1_Temp` - Motor 1 temperature
- `Line1_Pressure` - Production line 1 pressure
- `Conveyor_Speed` - Conveyor belt speed
- `Robot1_Current` - Robot 1 motor current

### Troubleshooting EtherNet/IP

```python
# Test EtherNet/IP connection
from pycomm3 import LogixDriver

with LogixDriver('192.168.1.10') as plc:
    print(f"Connected: {plc}")
    print(f"PLC Info: {plc.info}")

    # Read a single tag
    result = plc.read('Motor1_Temp')
    print(f"Tag value: {result.value}")
```

**Common Issues:**
- Firewall blocking port 44818
- Wrong tag names (case-sensitive!)
- PLC not configured for EtherNet/IP messaging
- Security settings in PLC

---

## PROFINET/S7 Configuration

### Basic Setup (Siemens PLCs)

```python
from context_edge.profinet_protocol import PROFINETProtocol
from context_edge.context_injector import ContextInjectionModule

# Define Data Block mappings
db_mappings = {
    "temperature": {
        "db_number": 1,    # Data Block 1
        "start": 0,        # Byte 0
        "type": "real"     # REAL (32-bit float)
    },
    "vibration": {
        "db_number": 1,
        "start": 4,        # Byte 4 (REAL is 4 bytes)
        "type": "real"
    },
    "pressure": {
        "db_number": 1,
        "start": 8,
        "type": "real"
    },
    "conveyor_speed": {
        "db_number": 2,
        "start": 0,
        "type": "int"      # INT (16-bit integer)
    }
}

# Initialize PROFINET/S7 protocol
profinet = PROFINETProtocol(
    host="192.168.1.20",  # Siemens PLC IP
    rack=0,               # Usually 0 for S7-1200/1500
    slot=1,               # Usually 1 for S7-1200/1500
    db_mappings=db_mappings,
    max_retries=3
)

# Connect to PLC
if profinet.connect():
    print("Connected to Siemens PLC")
    print(f"PLC Info: {profinet.get_plc_info()}")
    print(f"CPU State: {profinet.get_cpu_state()}")
else:
    print("Failed to connect")

# Use with CIM
cim = ContextInjectionModule(
    context_service_url="http://localhost:8000",
    data_protocol=profinet
)

ldo = cim.inject_context(detected_cid="QR004")
```

### Finding Data Block Information

Use Siemens TIA Portal:

```
1. Open TIA Portal
2. Go to PLC Tags
3. Find Data Blocks (DB1, DB2, etc.)
4. Note:
   - DB number (e.g., DB1)
   - Byte offset (e.g., DBX0.0, DBX4.0)
   - Data type (REAL, INT, DINT, BOOL)

Example:
  DB1.DBD0  = Temperature (REAL at byte 0)
  DB1.DBD4  = Vibration (REAL at byte 4)
  DB1.DBD8  = Pressure (REAL at byte 8)
```

**Data Type Sizes:**
| Type | Size | Example |
|------|------|---------|
| BOOL | 1 byte | True/False |
| INT | 2 bytes | -32768 to 32767 |
| DINT | 4 bytes | -2147483648 to 2147483647 |
| REAL | 4 bytes | 32-bit float |

### Rack and Slot Configuration

| PLC Model | Typical Rack | Typical Slot |
|-----------|--------------|--------------|
| S7-1200 | 0 | 1 |
| S7-1500 | 0 | 1 |
| S7-300 | 0 | 2 |
| S7-400 | 0 | 2-3 |

**How to find rack/slot:**
- TIA Portal → Device Configuration → Properties
- Or check PLC physical slot position in rack

### Troubleshooting PROFINET/S7

```python
# Test S7 connection
import snap7

client = snap7.client.Client()
client.connect('192.168.1.20', 0, 1)  # IP, rack, slot

if client.get_connected():
    print("Connected!")
    cpu_info = client.get_cpu_info()
    print(f"CPU: {cpu_info.ModuleTypeName.decode('utf-8')}")

    # Read DB1 starting at byte 0, length 4 (REAL)
    data = client.db_read(1, 0, 4)
    value = snap7.util.get_real(data, 0)
    print(f"DB1.DBD0 value: {value}")

    client.disconnect()
```

**Common Issues:**
- Firewall blocking port 102
- Wrong rack/slot numbers
- PLC in STOP mode (must be in RUN mode)
- PUT/GET not enabled in PLC settings
- DB blocks not optimized (must be non-optimized for S7 access)

---

## Modbus RTU Configuration

### Basic Setup (Serial Communication)

```python
from context_edge.modbus_rtu_protocol import ModbusRTUProtocol
from context_edge.context_injector import ContextInjectionModule

# Define register mappings
register_mappings = {
    "temperature": {
        "address": 0,           # Register 0
        "type": "holding",      # Holding register
        "count": 1,             # 16-bit value
        "scale": 10.0          # Divide by 10 (register value 235 = 23.5°C)
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

# Initialize Modbus RTU protocol
modbus_rtu = ModbusRTUProtocol(
    port="/dev/ttyUSB0",       # Linux: /dev/ttyUSB0, Windows: COM3
    register_mappings=register_mappings,
    slave_id=1,                # Modbus slave ID (default 1)
    baudrate=9600,             # Common: 9600, 19200, 38400, 115200
    bytesize=8,
    parity='N',                # N=None, E=Even, O=Odd
    stopbits=1,
    max_retries=3
)

# Connect to device
if modbus_rtu.connect():
    print("Connected to Modbus RTU device")
else:
    print("Failed to connect")

# Use with CIM
cim = ContextInjectionModule(
    context_service_url="http://localhost:8000",
    data_protocol=modbus_rtu
)

ldo = cim.inject_context(detected_cid="QR005")
```

### Serial Port Configuration

**Linux:**
```bash
# List available serial ports
ls /dev/ttyUSB* /dev/ttyS*

# Common ports:
# /dev/ttyUSB0  - USB-to-Serial adapter
# /dev/ttyS0    - Built-in serial port

# Grant permissions
sudo chmod 666 /dev/ttyUSB0
# Or add user to dialout group
sudo usermod -a -G dialout $USER
```

**Windows:**
```
Device Manager → Ports (COM & LPT)
Look for: COM3, COM4, etc.

Use: "COM3" in Python code
```

### Common Baudrate Settings

| Baudrate | Use Case |
|----------|----------|
| 9600 | Most common, legacy devices |
| 19200 | Modern devices, faster |
| 38400 | High-speed applications |
| 115200 | Very high-speed (rare in industrial) |

**Finding your baudrate:**
1. Check device manual/datasheet
2. Common default: 9600 baud, 8 data bits, No parity, 1 stop bit (9600-8-N-1)

### Troubleshooting Modbus RTU

```python
# Test Modbus RTU connection
from pymodbus.client import ModbusSerialClient

client = ModbusSerialClient(
    port='/dev/ttyUSB0',
    baudrate=9600,
    timeout=3
)

if client.connect():
    print("Connected!")

    # Read holding register 0
    result = client.read_holding_registers(0, 1, slave=1)
    if not result.isError():
        print(f"Register 0: {result.registers[0]}")

    client.close()
else:
    print("Connection failed")
```

**Common Issues:**
- Wrong serial port
- Wrong baudrate/parity settings
- Cable wiring (RS-232 vs RS-485)
- Slave ID mismatch
- Permissions on Linux (/dev/ttyUSB0 requires dialout group)

**RS-485 Wiring:**
```
A+ (Data+) → A+ on device
B- (Data-) → B- on device
Ground     → Ground (optional but recommended)
```

---

## Protocol Selection Guide

### Which Protocol Should You Use?

| Your PLC Brand | Recommended Protocol | Alternative |
|----------------|---------------------|-------------|
| Allen-Bradley, Rockwell | **EtherNet/IP** ✅ | OPC UA |
| Siemens S7-1200/1500 | **OPC UA** ✅ | PROFINET/S7 |
| Siemens S7-300/400 | **PROFINET/S7** ✅ | OPC UA |
| Schneider Electric M340 | **Modbus TCP** ✅ | - |
| Schneider Electric M580 | **OPC UA** ✅ | Modbus TCP |
| ABB, B&R | **OPC UA** ✅ | - |
| Legacy PLC (pre-2000) | **Modbus RTU** ✅ | Modbus TCP |
| Unknown/Generic | **OPC UA** ✅ | Modbus TCP |

### Environment Variables Summary

**OPC UA:**
```bash
PROTOCOL_TYPE=opcua
OPCUA_URL=opc.tcp://192.168.1.10:4840
```

**Modbus TCP:**
```bash
PROTOCOL_TYPE=modbus
MODBUS_HOST=192.168.1.20
MODBUS_PORT=502
```

**EtherNet/IP:**
```bash
PROTOCOL_TYPE=ethernetip
ETHERNETIP_HOST=192.168.1.10
ETHERNETIP_PORT=44818
ETHERNETIP_TAG_MAPPINGS='{"temperature":"Motor1_Temp","vibration":"Motor1_Vib"}'
```

**PROFINET/S7:**
```bash
PROTOCOL_TYPE=profinet
PROFINET_HOST=192.168.1.20
PROFINET_RACK=0
PROFINET_SLOT=1
PROFINET_DB_MAPPINGS='{"temperature":{"db_number":1,"start":0,"type":"real"}}'
```

**Modbus RTU:**
```bash
PROTOCOL_TYPE=modbus_rtu
MODBUS_RTU_PORT=/dev/ttyUSB0
MODBUS_RTU_SLAVE_ID=1
MODBUS_RTU_BAUDRATE=9600
MODBUS_RTU_REGISTER_MAPPINGS='{"temperature":{"address":0,"type":"holding","count":1,"scale":10.0}}'
```

---

## Next Steps

1. Choose your protocol based on PLC brand
2. Gather required configuration (IP, node IDs, register addresses, etc.)
3. Configure protocol using examples above
4. Populate Redis Context Store with assets, thresholds, runtime state
5. Test with CIM
6. Integrate with full pipeline (QR decoder → CIM → Data Ingestion)

For questions, see main README.md and deployment guides.

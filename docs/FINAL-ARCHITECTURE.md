# Context Edge - Final Architecture

**Date:** 2025-01-16
**Status:** ✅ Implemented and Ready for Testing

---

## Overview

Correctly separated architecture with **modular edge devices** capturing CIDs via multiple input methods and **edge server** performing fusion and AI inference.

---

## Architecture Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                     Factory Floor (Edge)                       │
│                                                                │
│  ┌─────────────────────┐  ┌─────────────────────┐            │
│  │  Edge Device #1     │  │  Edge Device #2     │            │
│  │  (Raspberry Pi)     │  │  (Raspberry Pi)     │   ...      │
│  │                     │  │                     │            │
│  │  Input: Camera      │  │  Input: RFID        │            │
│  │  ├─ Video stream    │  │  ├─ RFID reader     │            │
│  │  ├─ QR decode       │  │  ├─ Tag read        │            │
│  │  └─ Extract CID     │  │  └─ Extract CID     │            │
│  │         │           │  │         │           │            │
│  └─────────┼───────────┘  └─────────┼───────────┘            │
│            │                        │                        │
│            └────────────┬───────────┘                        │
│                         │ HTTP POST {cid, device_id}         │
└─────────────────────────┼────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────────┐
│                  Plant Server (Local Edge Server)              │
│                  (Docker Compose)                              │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                    Edge Server                           │ │
│  │                                                          │ │
│  │  POST /cid ────► 1. Receive CID                         │ │
│  │                  2. Redis.get(CID) ──► Context metadata │ │
│  │                  3. PLC.read() ──────► Sensor data      │ │
│  │                  4. CIM Fusion ──────► Fused data       │ │
│  │                  5. AI Inference ────► Prediction       │ │
│  │                  6. Generate LDO ────► Store            │ │
│  │                                                          │ │
│  └──────────────────────────────────────────────────────────┘ │
│                          │                                    │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │   Redis    │  │  PostgreSQL  │  │  Protocol Adapters   │ │
│  │  (Context) │  │  (LDO Store) │  │  - Modbus TCP        │ │
│  │            │  │              │  │  - OPC UA            │ │
│  └────────────┘  └──────────────┘  └──────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘
                          │
                          ▼
                  Training Data / Cloud (Optional)
```

---

## Repository Structure

```
context-edge/
├── edge-device/                    ← Runs on Raspberry Pi/Jetson
│   ├── edge_app/
│   │   ├── inputs/
│   │   │   ├── camera_stream.py    ✅ Implemented (QR codes)
│   │   │   ├── rfid_reader.py      ⚠️ Placeholder
│   │   │   └── barcode_scanner.py  ⚠️ Placeholder
│   │   └── main.py                 ← Orchestrates input → send CID
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
│
├── edge-server/                    ← Runs on local plant server
│   ├── app/
│   │   ├── protocols/              ← PLC communication
│   │   │   ├── modbus_protocol.py  ✅ Modbus TCP
│   │   │   └── opcua_protocol.py   ✅ OPC UA
│   │   ├── services/
│   │   │   ├── context_lookup.py   ✅ Redis context fetching
│   │   │   ├── fusion.py           ✅ CIM fusion + AI inference
│   │   │   └── ldo_generator.py    ✅ LDO creation and storage
│   │   └── main.py                 ← FastAPI app
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
│
├── context-service/                ← Existing API service
├── data-ingestion/                 ← Existing API service
├── ui/                             ← Web UI (Next.js)
└── docker-compose.yml              ← Orchestrates edge server services
```

---

## Data Flow

### Step-by-Step Flow:

```
1. QR Code Creation (Before Production)
   ────────────────────────────────────
   Admin → Create QR code with CID
        → Context stored in Redis
          Key: "context:CID-PROD-12345"
          Value: {product_id, batch, operator, line, station}
        → QR code printed and attached to part

2. Production Line (Real-time)
   ────────────────────────────
   Part enters station
        ↓
   Edge Device (Raspberry Pi)
        ├─ Camera captures video (30 FPS)
        ├─ QR decoder finds code
        ├─ Extract: "CID-PROD-12345"
        └─ POST to Edge Server
             {
               "cid": "CID-PROD-12345",
               "camera_id": "EDGE-Line1-Station1",
               "timestamp": "2025-01-16T10:30:00"
             }
        ↓
   Edge Server (Plant Server)
        ├─ Receive CID
        ├─ Redis.get("context:CID-PROD-12345")
        │  Returns: {product_id: "WIDGET-A", batch: "B001", ...}
        │
        ├─ PLC.read() via Modbus/OPC UA
        │  Returns: {temp: 72.5, vib: 2.3, pressure: 98.5, ...}
        │
        ├─ CIM Fusion (PATENTED)
        │  Combines: context + sensor_data → fused_data
        │
        ├─ AI Inference
        │  Predicts: "good" with 0.95 confidence
        │
        └─ Generate LDO
           Stores in PostgreSQL
           Returns: "LDO-20250116103000-12345"
        ↓
   Response to Edge Device
        {
          "status": "success",
          "ldo_id": "LDO-20250116103000-12345"
        }
```

---

## Components

### 1. Edge Device (Modular)

**Location:** `/edge-device/`
**Runs on:** Raspberry Pi 4 or Jetson Nano
**Cost:** $80-150 per device

**Input Modules:**

| Module | Status | File | Description |
|--------|--------|------|-------------|
| Camera Stream | ✅ Implemented | `inputs/camera_stream.py` | Video capture + QR decode |
| RFID Reader | ⚠️ Placeholder | `inputs/rfid_reader.py` | RFID tag reading |
| Barcode Scanner | ⚠️ Placeholder | `inputs/barcode_scanner.py` | 1D/2D barcode scanning |
| OCR Scanner | ⚠️ Future | - | Optical character recognition |
| NFC Reader | ⚠️ Future | - | Near-field communication |

**Configuration:**
```bash
export INPUT_TYPE="camera"      # Select input type
export DEVICE_ID="EDGE-Line1-Station1"
export EDGE_SERVER_URL="http://edge-server:5000/cid"

# Camera-specific
export CAMERA_INDEX="0"
export SCAN_INTERVAL="1.0"

# Future: RFID/Barcode-specific
# export RFID_PORT="/dev/ttyUSB0"
# export RFID_BAUDRATE="9600"
```

**Deployment:**
```bash
# On Raspberry Pi
cd edge-device
pip3 install -r requirements.txt
python3 -m edge_app.main
```

---

### 2. Edge Server (Centralized Intelligence)

**Location:** `/edge-server/`
**Runs on:** Local plant server (Docker Compose)
**Cost:** $2000-5000 per server (handles 5-10 edge devices)

**Services:**

| Service | Purpose | File |
|---------|---------|------|
| Context Lookup | Fetch context from Redis | `services/context_lookup.py` |
| Fusion Service | CIM fusion + AI inference | `services/fusion.py` |
| LDO Generator | Create and store LDOs | `services/ldo_generator.py` |

**Protocol Adapters:**

| Protocol | Status | File | Use Case |
|----------|--------|------|----------|
| Modbus TCP | ✅ Implemented | `protocols/modbus_protocol.py` | Most PLCs |
| OPC UA | ✅ Implemented | `protocols/opcua_protocol.py` | Modern industrial systems |
| EtherNet/IP | ⚠️ Future | - | Allen-Bradley PLCs |
| PROFINET | ⚠️ Future | - | Siemens PLCs |
| S7 | ⚠️ Future | - | Siemens S7 protocol |

**Deployment:**
```bash
# Via Docker Compose
docker-compose up -d edge-server

# Services started:
# - Redis (context cache)
# - PostgreSQL (LDO storage)
# - Edge Server (fusion + AI)
```

---

### 3. Supporting Services

**Redis** (Context Cache)
- Stores context metadata with CID as key
- Sub-1ms lookup time
- 24-hour TTL default
- Port: 6379

**PostgreSQL** (Data Storage)
- `metadata_payloads` - Context + sensor data
- `predictions` - AI inference results
- `feedback_queue` - Low-confidence predictions
- Port: 5432

**Context Service** (Existing)
- API for managing contexts
- Port: 8000

**Data Ingestion** (Optional - Future Use)
- **Current Status**: Not used in base flow
- **Future Use Cases**:
  - Export LDOs from PostgreSQL to S3/MinIO for ML training
  - Store video clips (if edge devices capture video)
  - Cloud sync for multi-site deployments
  - Backup and archival
- **Current Flow**: Edge server stores LDOs directly in PostgreSQL
- Port: 8001

**UI** (Web Interface)
- Next.js frontend
- Port: 3000

---

## Why This Architecture Works

### ✅ Modular Edge Devices

**Benefits:**
- Camera is just ONE input type (not hardcoded)
- Easy to add RFID, barcode, OCR, NFC, etc.
- Same edge device platform for all input types
- Configure via environment variable: `INPUT_TYPE`

**Example:**
```bash
# Station 1: Camera for QR codes
INPUT_TYPE="camera" python3 -m edge_app.main

# Station 2: RFID reader for tags
INPUT_TYPE="rfid" python3 -m edge_app.main

# Station 3: Barcode scanner
INPUT_TYPE="barcode" python3 -m edge_app.main
```

### ✅ Centralized Intelligence

**Benefits:**
- All fusion, AI, and data processing on edge server
- Edge devices are simple and cheap ($80-150)
- Easy to update AI models (one server vs 50 devices)
- One edge server handles 5-10 devices

### ✅ Local-First Design

**Benefits:**
- Everything runs in the plant (no cloud dependency)
- Data stays on-premise (security/compliance)
- Cloud is optional add-on
- Works without internet

### ✅ Scalable

**Small (1-5 devices):**
- 1 Edge Server (Docker Compose)
- 1-5 Edge Devices (Raspberry Pi)
- Total: $2500-3500

**Medium (10-20 devices):**
- 2-3 Edge Servers (load balanced)
- 10-20 Edge Devices
- Total: $8000-15000

**Enterprise (50+ devices):**
- K3s cluster for edge servers
- 50+ Edge Devices
- Auto-scaling, high availability

---

## Configuration

### Edge Device Configuration

```bash
# Required
export EDGE_SERVER_URL="http://edge-server.local:5000/cid"
export DEVICE_ID="EDGE-Line1-Station1"

# Input Selection
export INPUT_TYPE="camera"  # or "rfid", "barcode"

# Camera (if INPUT_TYPE=camera)
export CAMERA_INDEX="0"
export SCAN_INTERVAL="1.0"

# RFID (if INPUT_TYPE=rfid)
# export RFID_PORT="/dev/ttyUSB0"
# export RFID_BAUDRATE="9600"

# Barcode (if INPUT_TYPE=barcode)
# export BARCODE_PORT="/dev/ttyUSB0"
# export BARCODE_BAUDRATE="9600"
```

### Edge Server Configuration

```bash
# Redis
export REDIS_HOST="redis"
export REDIS_PORT="6379"

# PostgreSQL
export POSTGRES_HOST="postgres"
export POSTGRES_PORT="5432"
export POSTGRES_DB="context_edge"
export POSTGRES_USER="context_user"
export POSTGRES_PASSWORD="context_pass"

# PLC Connections (optional)
export USE_MOCK_SENSORS="true"  # false for real PLCs
export MODBUS_HOST="192.168.1.10"
export MODBUS_PORT="502"
export OPCUA_SERVER_URL="opc.tcp://192.168.1.11:4840"
```

---

## Deployment

### Quick Start (Testing)

```bash
# 1. Start edge server
docker-compose up -d

# 2. Verify services
docker-compose ps

# 3. Seed test context
redis-cli SET "context:TEST-001" '{"product_id":"WIDGET-A","batch":"B001"}'

# 4. Run edge device (camera input)
cd edge-device
export INPUT_TYPE="camera"
export EDGE_SERVER_URL="http://localhost:5000/cid"
python3 -m edge_app.main

# 5. Scan QR code with CID "TEST-001"

# 6. Check LDO created
psql -U context_user -d context_edge -c "SELECT * FROM predictions LIMIT 5;"
```

### Production Deployment

```bash
# On each Raspberry Pi:
git clone https://github.com/yourorg/context-edge.git
cd context-edge/edge-device

# Configure for this station
cat > .env <<EOF
EDGE_SERVER_URL=http://edge-server.local:5000/cid
DEVICE_ID=EDGE-Line1-Station1
INPUT_TYPE=camera
CAMERA_INDEX=0
EOF

# Install and run
pip3 install -r requirements.txt
python3 -m edge_app.main

# Or use systemd for auto-start
sudo systemctl enable context-edge-device
sudo systemctl start context-edge-device
```

---

## Testing

```bash
# Test edge server health
curl http://localhost:5000/health

# Test CID submission
curl -X POST http://localhost:5000/cid \
  -H "Content-Type: application/json" \
  -d '{
    "cid": "TEST-001",
    "camera_id": "EDGE-Test",
    "timestamp": "2025-01-16T10:30:00"
  }'

# Expected response:
# {
#   "status": "success",
#   "message": "LDO generated successfully",
#   "ldo_id": "LDO-20250116103000-TEST"
# }
```

---

## Cost Breakdown

### Per Edge Device
- Raspberry Pi 4 (2GB): $45
- Camera OR RFID OR Barcode: $20-50
- Power supply + case: $15-20
- MicroSD card: $10
- **Total: $90-125 per device**

### Edge Server
- Server/PC (Intel NUC or similar): $1500-3000
- Or use existing plant PC: $0
- Network switch: $100-200
- **Total: $1600-3200 per server**

### Complete System (10 devices)
- 1 Edge Server: $2000
- 10 Edge Devices @ $100: $1000
- Network equipment: $200
- **Total: ~$3200 for 10-device system**

---

## Summary

| Aspect | Implementation |
|--------|---------------|
| **Edge Device** | Modular platform with pluggable input types |
| **Inputs Supported** | Camera (✅), RFID (⚠️), Barcode (⚠️), Future: OCR, NFC |
| **Edge Server** | Centralized fusion, AI, and LDO generation |
| **Protocols** | Modbus TCP (✅), OPC UA (✅), Future: EtherNet/IP, PROFINET |
| **Deployment** | Local-first (Docker Compose), Cloud optional |
| **Scalability** | 5-10 devices per edge server |
| **Cost** | $90-125 per edge device, $2000-3000 per edge server |
| **Status** | ✅ Ready for testing |

---

## Next Steps

1. ✅ Architecture implemented
2. ⏳ Test edge-device → edge-server → LDO flow
3. ⏳ Implement RFID input module
4. ⏳ Implement barcode input module
5. ⏳ Deploy to production hardware
6. ⏳ Load testing and optimization

**Architecture is complete and ready for testing!** 🚀

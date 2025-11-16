# Context Edge - NEW Architecture

**Status:** ✅ Implemented (2025-01-16)

## Overview

Properly separated architecture with **camera devices** sending CIDs to **edge server** for fusion and AI inference.

---

## Architecture Diagram

```
┌─────────────────────┐
│  Camera Device      │  Raspberry Pi / Jetson Nano
│  (Raspberry/Jetson) │  Cost: $50-150
│                     │
│  1. Video Capture   │  ◄── Camera input
│  2. QR Decode       │  ◄── Scans QR codes
│  3. Send CID ──────────────┐
│                     │      │
└─────────────────────┘      │ HTTP POST
                             │ {cid, camera_id, timestamp}
                             │
                             ▼
                    ┌────────────────────────┐
                    │   Edge Server          │  Local plant server
                    │   (Docker Compose)     │  Cost: $2000-5000
                    │                        │
                    │  1. Receive CID        │ ◄── From camera
                    │  2. Redis.get(CID)     │ ◄── Fetch context
                    │  3. PLC.read()         │ ◄── Read sensors
                    │  4. CIM Fusion ─────┐  │
                    │  5. AI Inference    │  │
                    │  6. Generate LDO ───┘  │
                    │                        │
                    └────────────────────────┘
                             │
                             ├──► PostgreSQL (LDO storage)
                             ├──► Redis (Context cache)
                             └──► Feedback Queue
```

---

## Components

### 1. Camera Device (NEW)

**Location:** `/camera-device/`

**Runs on:** Raspberry Pi 4 or Jetson Nano

**What it does:**
- Captures video from camera
- Decodes QR codes in real-time
- Sends CID to Edge Server

**Code:**
```python
# camera-device/camera_app/main.py
def send_cid(self, cid: str):
    payload = {
        "cid": cid,
        "camera_id": self.camera_id,
        "timestamp": datetime.now().isoformat()
    }
    requests.post(self.edge_server_url, json=payload)
```

**Deployment:**
```bash
# On Raspberry Pi
python3 -m camera_app.main
```

**Cost:** $50-150 per camera station

---

### 2. Edge Server (NEW)

**Location:** `/edge-server/`

**Runs on:** Local plant server (Docker Compose)

**What it does:**

#### Step 1: Receive CID
```python
@app.post("/cid")
async def receive_cid(request: CIDRequest):
    # Camera sends: {cid, camera_id, timestamp}
```

#### Step 2: Fetch Context from Redis
```python
context = await context_service.get_context(cid)
# Returns: {product_id, batch, operator, line, station, ...}
```

#### Step 3: Read PLC Sensor Data
```python
sensor_data = await fusion_service.read_sensor_data(camera_id)
# Returns: {temperature, vibration, pressure, humidity, cycle_time}
```

#### Step 4: CIM Fusion (PATENTED)
```python
fused_data = await fusion_service.fuse_data(
    cid=cid,
    context=context,        # From Redis
    sensor_data=sensor_data # From PLC
)
# Returns: Complete data package with context + sensors
```

#### Step 5: AI Inference
```python
prediction = await fusion_service.run_inference(fused_data)
# Returns: {result: "good"|"defective", confidence: 0.95}
```

#### Step 6: Generate LDO
```python
ldo_id = await ldo_service.create_ldo(cid, fused_data, prediction)
# Stores in PostgreSQL
# Adds to feedback queue if low confidence
```

**Services:**
- `ContextLookupService` - Redis context fetching
- `FusionService` - CIM fusion + AI inference
- `LDOGeneratorService` - LDO creation and storage

**Protocol Adapters:**
- Modbus TCP (`app/protocols/modbus_protocol.py`)
- OPC UA (`app/protocols/opcua_protocol.py`)
- Extensible for EtherNet/IP, PROFINET, S7

**Deployment:**
```bash
# Via Docker Compose
docker-compose up -d edge-server
```

**Scales to:** 5-10 cameras per edge server

---

### 3. Supporting Services

**Redis** - Context cache
- Stores context metadata (CID → context)
- Sub-1ms lookup time
- 24-hour TTL default

**PostgreSQL** - Data storage
- `metadata_payloads` - Context + sensor data
- `predictions` - AI inference results
- `feedback_queue` - Low-confidence predictions

**Context Service** (existing)
- API for managing contexts
- Port 8000

**Data Ingestion** (existing)
- LDO storage and retrieval
- Port 8001

---

## Data Flow

### Phase 1: QR Code Generation (Before Production)

```
Admin creates QR code
  │
  ├─► Context metadata stored in Redis
  │   Key: "context:CID-PROD-12345"
  │   Value: {product_id, batch, operator, line, station}
  │
  └─► QR code printed and attached to part
```

### Phase 2: Production Line (Real-time)

```
Part enters station
  │
  ▼
Camera scans QR code
  │
  ├─► Decode: "CID-PROD-12345"
  │
  ▼
Send to Edge Server
  POST /cid {cid: "CID-PROD-12345", camera_id: "CAM-Line1-Station1"}
  │
  ▼
Edge Server processes:
  │
  ├─► Redis.get("context:CID-PROD-12345")
  │   Returns: {product_id: "WIDGET-A", batch: "BATCH-001", operator: "OP-123"}
  │
  ├─► PLC.read() via Modbus/OPC UA
  │   Returns: {temperature: 72.5, vibration: 2.3, pressure: 98.5}
  │
  ├─► CIM Fusion
  │   Combines context + sensor data
  │
  ├─► AI Inference
  │   Predicts: "good" with 0.95 confidence
  │
  └─► Generate LDO
      Stores in PostgreSQL
      Returns: "LDO-20250116103000-12345"
```

---

## Why This Architecture?

### ✅ Correct Separation of Concerns

**Camera Device:**
- Simple, cheap ($50-150)
- Only does vision and QR decoding
- No PLC communication complexity
- Easy to deploy and maintain

**Edge Server:**
- Centralized intelligence
- Handles all fusion and AI
- One server supports 5-10 cameras
- Proper compute resources for AI

### ✅ Scalability

**Small Deployment (1-5 cameras):**
- 1 Edge Server (Docker Compose)
- 1-5 Camera Devices (Raspberry Pi)
- Total cost: $2500-3500

**Medium Deployment (10-20 cameras):**
- 2-3 Edge Servers (Docker Compose)
- 10-20 Camera Devices
- Load balanced

**Enterprise Deployment (50+ cameras):**
- K3s cluster for edge servers
- 50+ Camera Devices
- Auto-scaling, high availability

### ✅ Local-First Design

- Everything runs **in the plant** by default
- No cloud dependency (cloud is optional add-on)
- Companies want on-premise control
- Data stays local for security/compliance

### ✅ Maintainability

- Camera devices are stateless (just send CID)
- Edge server has all business logic
- Easy to update AI models (just restart edge-server)
- Protocol adapters isolated and testable

---

## Old Architecture (WRONG)

**Problem:** Everything bundled on edge device

```
❌ Edge Device (Jetson)
   ├─ Video capture
   ├─ QR decode
   ├─ PLC communication  ← Too complex for edge device
   ├─ Fusion (CIM)       ← Should be centralized
   ├─ AI inference       ← Expensive to replicate
   └─ LDO generation     ← Database connections on each device
```

**Why it was wrong:**
- Too expensive ($200-500 per device)
- Too complex to maintain
- Hard to update AI models on 50 devices
- PLC configuration per device
- Doesn't scale well

---

## New Architecture (CORRECT)

**Solution:** Split camera from edge server

```
✅ Camera Device (Raspberry Pi) - $80
   ├─ Video capture
   ├─ QR decode
   └─ Send CID ──────────┐
                         │
✅ Edge Server (Local)   │
   ├─ Receive CID  ◄─────┘
   ├─ Redis lookup (context)
   ├─ PLC read (sensors)
   ├─ Fusion (CIM)
   ├─ AI inference
   └─ LDO generation
```

**Why it's correct:**
- Camera devices are cheap and simple
- Centralized intelligence on edge server
- Easy to update models (one place)
- One edge server handles 5-10 cameras
- Scales economically

---

## Deployment

### Local Plant (Default)

```yaml
# docker-compose.yml
services:
  redis:        # Context cache
  postgres:     # Data storage
  edge-server:  # Fusion + AI
  context-service:
  data-ingestion:
```

```bash
# Start edge server
docker-compose up -d

# Deploy camera devices
# On each Raspberry Pi:
python3 -m camera_app.main
```

### Enterprise Scale (K3s)

```bash
# Deploy K3s cluster for edge servers
k3s kubectl apply -f k8s/edge-server-deployment.yaml

# Manage 50+ cameras with Helm
helm install context-edge ./helm-chart
```

---

## Testing

```bash
# 1. Start edge server
docker-compose up -d edge-server

# 2. Seed test context in Redis
redis-cli SET "context:TEST-CID-001" '{"product_id":"WIDGET-A","batch":"B001"}'

# 3. Send test CID from camera
curl -X POST http://localhost:5000/cid \
  -H "Content-Type: application/json" \
  -d '{
    "cid": "TEST-CID-001",
    "camera_id": "CAM-Test",
    "timestamp": "2025-01-16T10:30:00"
  }'

# 4. Verify LDO created
psql -U context_user -d context_edge -c "SELECT * FROM predictions ORDER BY created_at DESC LIMIT 1;"
```

---

## Summary

| Component | Old (Wrong) | New (Correct) |
|-----------|-------------|---------------|
| **Camera device** | Everything bundled | Just video + QR → send CID |
| **Edge server** | Didn't exist | Fusion + AI + LDO |
| **Cost per camera** | $200-500 | $80 |
| **Scalability** | Poor (each device complex) | Good (centralized server) |
| **Maintenance** | Update 50 devices | Update 1 server |
| **PLC communication** | Each device configures | Centralized adapters |
| **Deployment** | Complicated | Simple (Docker Compose) |
| **Local-first** | No | Yes (cloud optional) |

**NEW ARCHITECTURE IS CORRECT ✅**

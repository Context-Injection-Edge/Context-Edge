# Architecture Refactor: Split Edge Device into Camera + Edge Server

**Date**: 2025-01-16
**Priority**: CRITICAL - Core Architecture Change
**Status**: Planning

---

## Problem Statement

Current architecture bundles EVERYTHING into the edge device (Jetson/Pi):
- ❌ Camera + QR decoding
- ❌ PLC protocol adapters
- ❌ Context fetching
- ❌ Data fusion (CIM)
- ❌ AI inference
- ❌ LDO generation

**This is wrong!** It makes devices expensive, complex, and hard to scale.

---

## Correct Architecture (3-Tier)

```
┌──────────────────────────────────────────────────────────┐
│  TIER 1: CAMERA DEVICE (Jetson Nano / Raspberry Pi)     │
│  Role: Simple video capture + QR decode                 │
│  Cost: $50-$150                                          │
│  ──────────────────────────────────────────────────────  │
│  Components:                                             │
│  - Camera (USB / CSI)                                    │
│  - QR Decoder (OpenCV / pyzbar)                          │
│  - HTTP/MQTT Client (sends CID to Edge Server)          │
│                                                          │
│  Does NOT:                                               │
│  ✗ Read from PLCs                                        │
│  ✗ Fetch context metadata                               │
│  ✗ Do any fusion                                         │
│  ✗ Run AI models                                         │
│                                                          │
│  Output: POST http://edge-server:5000/cid               │
│          {"cid": "WIDGET-A-BATCH-12345",                │
│           "timestamp": "2025-01-16T10:30:00Z",          │
│           "camera_id": "CAM-001"}                       │
└──────────────────────────────────────────────────────────┘
                          ↓ HTTP/MQTT
┌──────────────────────────────────────────────────────────┐
│  TIER 2: EDGE SERVER (Industrial PC)                    │
│  Role: Data fusion + AI inference + LDO generation      │
│  Cost: $1,500-$3,000 (handles 5-10 cameras)             │
│  ──────────────────────────────────────────────────────  │
│  Components:                                             │
│  1. CID Receiver API (FastAPI)                          │
│     - Receives CID from camera devices                  │
│     - Queue for processing                              │
│                                                          │
│  2. Context Fetcher                                     │
│     - Queries cloud Context Service                     │
│     - Local Redis cache (works offline)                 │
│                                                          │
│  3. Protocol Adapters                                   │
│     - Modbus TCP/RTU                                    │
│     - OPC UA                                            │
│     - EtherNet/IP                                       │
│     - PROFINET                                          │
│     - Reads PLC data when CID arrives                   │
│                                                          │
│  4. Context Injection Module (CIM) ⚡ FUSION            │
│     - Combines: CID + Context + PLC Data                │
│     - Creates enriched feature vector                   │
│                                                          │
│  5. AI Inference Engine                                 │
│     - TensorRT / ONNX Runtime                           │
│     - Loads model from disk                             │
│     - Runs prediction on fused data                     │
│                                                          │
│  6. LDO Generator                                       │
│     - Creates Labeled Data Object                       │
│     - Includes ground truth from context                │
│                                                          │
│  7. Cloud Uploader                                      │
│     - Sends LDO to cloud                                │
│     - Retry logic, local storage if offline             │
│                                                          │
│  Output: POST http://cloud:8001/ldo                     │
│          {complete LDO with fusion + prediction}        │
└──────────────────────────────────────────────────────────┘
                          ↓ HTTP
┌──────────────────────────────────────────────────────────┐
│  TIER 3: CLOUD SERVER                                   │
│  Role: Metadata storage, LDO collection, model training │
│  Cost: Cloud hosting ($200-$500/month)                  │
│  ──────────────────────────────────────────────────────  │
│  Components:                                             │
│  - Context Service API (serves metadata)                │
│  - Data Ingestion API (receives LDOs)                   │
│  - PostgreSQL (stores everything)                       │
│  - Redis (caches context)                               │
│  - MLOps Pipeline (trains models)                       │
│  - Admin UI (Next.js)                                   │
└──────────────────────────────────────────────────────────┘
```

---

## Benefits of This Architecture

### 1. **Cost Savings**

**Old Architecture (Current - WRONG):**
```
Per Production Line:
- 1x Jetson Xavier NX (for AI + fusion): $600
- Must handle: Camera, PLC, AI, Fusion
- Total per line: $600

10 production lines = $6,000
```

**New Architecture (Correct):**
```
Per Production Line:
- 1x Raspberry Pi 4 (camera only): $75
- Connects to centralized Edge Server
- Total per line: $75

Shared Infrastructure:
- 1x Edge Server (handles 10 lines): $2,000

10 production lines = $750 + $2,000 = $2,750
Savings: $3,250 (54% cheaper!)
```

### 2. **Easier to Scale**

**Old:** Need new Jetson for each camera ($600)
**New:** Just add $75 Pi camera, edge server handles it

### 3. **Centralized PLC Connectivity**

**Old:** Each Jetson needs Modbus/OPC UA configured
**New:** Edge Server has ONE connection to all PLCs

### 4. **Easier Updates**

**Old:** Update AI model on 10 Jetsons (SSH to each)
**New:** Update Edge Server once, all cameras benefit

### 5. **Better AI Models**

**Old:** Limited by Jetson Nano GPU (4GB)
**New:** Edge Server can have RTX 4090 (24GB)

---

## File Structure Changes

### Current Structure (WRONG):

```
edge-device/
└── context_edge/
    ├── main.py                    ← Does EVERYTHING
    ├── vision_engine.py           ← Camera
    ├── qr_decoder.py              ← QR decode
    ├── context_injector.py        ← Fusion (CIM)
    ├── ldo_generator.py           ← LDO generation
    ├── opcua_protocol.py          ← PLC protocols
    ├── modbus_protocol.py         ← PLC protocols
    ├── ethernetip_protocol.py     ← PLC protocols
    └── ...
```

### New Structure (CORRECT):

```
camera-device/                     ← NEW: Lightweight camera app
├── camera_app/
│   ├── __init__.py
│   ├── main.py                    ← Simple: Camera → QR → POST CID
│   ├── vision_engine.py           ← Moved from edge-device
│   ├── qr_decoder.py              ← Moved from edge-device
│   └── cid_sender.py              ← NEW: Sends CID to Edge Server
├── requirements.txt               ← Minimal: opencv, pyzbar, requests
├── Dockerfile                     ← Lightweight image
└── README.md

edge-server/                       ← NEW: Fusion + AI + LDO
├── edge_app/
│   ├── __init__.py
│   ├── main.py                    ← FastAPI server receives CID
│   ├── cid_receiver.py            ← NEW: API endpoint for CID
│   ├── context_fetcher.py         ← NEW: Fetches from cloud
│   ├── context_injector.py        ← Moved from edge-device (CIM)
│   ├── ldo_generator.py           ← Moved from edge-device
│   ├── ai_inference.py            ← NEW: TensorRT/ONNX wrapper
│   ├── cloud_uploader.py          ← NEW: Sends LDO to cloud
│   └── protocols/                 ← Moved from edge-device
│       ├── opcua_protocol.py
│       ├── modbus_protocol.py
│       ├── ethernetip_protocol.py
│       ├── profinet_protocol.py
│       └── modbus_rtu_protocol.py
├── requirements.txt               ← Full stack: protocols, TensorRT
├── Dockerfile                     ← Heavier image with GPU support
├── docker-compose.yml             ← Runs Edge Server + Redis locally
└── README.md

edge-device/                       ← DEPRECATED (keep for reference)
└── ...

context-service/                   ← No changes
└── ...

data-ingestion/                    ← No changes
└── ...

ui/                                ← No changes
└── ...
```

---

## Data Flow (New Architecture)

### Step-by-Step Process:

```
1. Operator scans QR code on part
   ↓
2. CAMERA DEVICE:
   - Camera captures frame
   - QR decoder extracts: "WIDGET-A-BATCH-12345"
   - POST http://edge-server:5000/cid
     {
       "cid": "WIDGET-A-BATCH-12345",
       "camera_id": "CAM-Line1-Station1",
       "timestamp": "2025-01-16T10:30:15.123Z"
     }
   ↓
3. EDGE SERVER receives CID:
   a. Context Fetcher:
      - GET http://cloud:8000/context?cid=WIDGET-A-BATCH-12345
      - Returns: {
          "product": "Motor Assembly Type A",
          "expected_temp": 75,
          "vibration_max": 2.0
        }

   b. Protocol Adapter:
      - Connects to PLC via EtherNet/IP
      - plc.read('Motor1_Temp') → 82.5°F
      - plc.read('Motor1_Vibration') → 1.8 mm/s
      - plc.read('Motor1_Current') → 12.3 A

   c. Context Injection Module (CIM):
      - Fuses: CID + Context + PLC Data
      - Creates feature vector:
        {
          "sensor_data": {temp: 82.5, vib: 1.8, current: 12.3},
          "context": {product: "Type A", expected_temp: 75},
          "derived_features": {temp_deviation: 7.5, is_anomaly: true}
        }

   d. AI Inference:
      - model.predict(fused_data)
      - Result: "bearing_wear", confidence: 0.87

   e. LDO Generator:
      - Creates complete LDO:
        {
          "ldo_id": "LDO-2025-001",
          "cid": "WIDGET-A-BATCH-12345",
          "sensor_data": {...},
          "context": {...},
          "prediction": "bearing_wear",
          "confidence": 0.87,
          "ground_truth": "bearing_wear",  ← From context!
          "timestamp": "2025-01-16T10:30:15.456Z"
        }

   f. Cloud Uploader:
      - POST http://cloud:8001/ldo
      - Sends complete LDO
   ↓
4. CLOUD SERVER:
   - Stores LDO in PostgreSQL
   - If confidence < 70%: Add to feedback queue
   - If defect: Generate MER
   - UI shows in real-time
```

---

## Implementation Plan

### Phase 1: Create Camera Device (Week 1)

**New Files to Create:**

```bash
camera-device/
├── camera_app/
│   ├── main.py
│   ├── cid_sender.py
│   └── config.py
├── requirements.txt
├── Dockerfile
└── README.md
```

**camera_app/main.py:**
```python
import cv2
from pyzbar import pyzbar
import requests
import time

EDGE_SERVER_URL = "http://edge-server:5000/cid"
CAMERA_ID = "CAM-Line1-Station1"

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    # Decode QR codes
    barcodes = pyzbar.decode(frame)
    for barcode in barcodes:
        cid = barcode.data.decode('utf-8')

        # Send to Edge Server
        payload = {
            "cid": cid,
            "camera_id": CAMERA_ID,
            "timestamp": time.time()
        }

        try:
            response = requests.post(EDGE_SERVER_URL, json=payload, timeout=2)
            if response.status_code == 200:
                print(f"✅ Sent CID: {cid}")
            else:
                print(f"❌ Error: {response.status_code}")
        except Exception as e:
            print(f"❌ Connection error: {e}")

        time.sleep(1)  # Debounce
```

**Estimated Lines:** ~150 lines total

---

### Phase 2: Create Edge Server (Week 2)

**New Files to Create:**

```bash
edge-server/
├── edge_app/
│   ├── main.py             ← FastAPI server
│   ├── cid_receiver.py     ← API endpoint
│   ├── context_fetcher.py  ← Fetches metadata
│   ├── fusion_engine.py    ← CIM logic
│   ├── ai_inference.py     ← TensorRT wrapper
│   ├── ldo_generator.py    ← Moved from edge-device
│   └── protocols/          ← Moved from edge-device
│       └── ...
├── docker-compose.yml
└── requirements.txt
```

**edge_app/main.py:**
```python
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from .fusion_engine import FusionEngine
from .ai_inference import AIModel
from .ldo_generator import LDOGenerator
import requests

app = FastAPI()

fusion_engine = FusionEngine()
ai_model = AIModel("models/bearing-classifier.trt")
ldo_generator = LDOGenerator()

class CIDPayload(BaseModel):
    cid: str
    camera_id: str
    timestamp: float

@app.post("/cid")
async def receive_cid(payload: CIDPayload, background_tasks: BackgroundTasks):
    # Process in background to respond quickly to camera
    background_tasks.add_task(process_cid, payload)
    return {"status": "accepted", "cid": payload.cid}

def process_cid(payload: CIDPayload):
    # 1. Fetch context
    context = fusion_engine.fetch_context(payload.cid)

    # 2. Read PLC data
    sensor_data = fusion_engine.read_plc_data()

    # 3. Fuse data (CIM)
    fused_data = fusion_engine.fuse(payload.cid, context, sensor_data)

    # 4. AI inference
    prediction = ai_model.predict(fused_data)

    # 5. Generate LDO
    ldo = ldo_generator.generate(
        cid=payload.cid,
        sensor_data=sensor_data,
        context=context,
        prediction=prediction
    )

    # 6. Send to cloud
    requests.post("http://cloud:8001/ldo", json=ldo)

    print(f"✅ Processed CID: {payload.cid} → {prediction['result']}")
```

**Estimated Lines:** ~500 lines total

---

### Phase 3: Migrate & Test (Week 3)

1. ✅ Copy protocol adapters from `edge-device/` to `edge-server/protocols/`
2. ✅ Copy `context_injector.py` to `edge-server/fusion_engine.py`
3. ✅ Copy `ldo_generator.py` to `edge-server/`
4. ✅ Update imports and paths
5. ✅ Test with simulator:
   - Run camera-device (sends CID)
   - Run edge-server (receives, fuses, sends LDO)
   - Run cloud (receives LDO)
6. ✅ Update docs

---

## Deployment Strategy

### Development (Local Testing):

```bash
# Terminal 1: Cloud Server
cd context-edge
docker-compose up

# Terminal 2: Edge Server
cd edge-server
python edge_app/main.py

# Terminal 3: Camera Device (Simulated)
cd camera-device
python camera_app/main.py
```

### Production (Factory):

```
Camera Devices (Multiple):
├── Raspberry Pi #1 (Line 1) → edge-server
├── Raspberry Pi #2 (Line 2) → edge-server
└── Raspberry Pi #3 (QC) → edge-server

Edge Server (Factory):
└── Industrial PC
    ├── Runs edge-server Docker container
    ├── Connected to all PLCs (Modbus, OPC UA)
    └── Handles all camera CIDs

Cloud Server:
└── AWS/Azure
    ├── Context Service
    ├── Data Ingestion
    └── Admin UI
```

---

## Migration Checklist

### Code Changes:

- [ ] Create `camera-device/` directory
- [ ] Create `camera-device/camera_app/main.py`
- [ ] Move `vision_engine.py` to camera-device
- [ ] Move `qr_decoder.py` to camera-device
- [ ] Create `edge-server/` directory
- [ ] Create `edge-server/edge_app/main.py` (FastAPI)
- [ ] Move `context_injector.py` to `edge-server/fusion_engine.py`
- [ ] Move `ldo_generator.py` to edge-server
- [ ] Move `protocols/*.py` to edge-server
- [ ] Create `edge-server/edge_app/ai_inference.py`
- [ ] Create communication layer (HTTP between camera and edge server)
- [ ] Update Docker Compose for edge-server

### Documentation:

- [ ] Update `README.md` with new architecture
- [ ] Update `docs/ARCHITECTURE-AND-ASSESSMENT.md`
- [ ] Create `edge-server/README.md`
- [ ] Create `camera-device/README.md`
- [ ] Update deployment guides

### Testing:

- [ ] Test camera-device sending CID
- [ ] Test edge-server receiving CID
- [ ] Test edge-server fusion logic
- [ ] Test edge-server PLC reading
- [ ] Test edge-server AI inference
- [ ] Test edge-server LDO generation
- [ ] Test end-to-end flow

---

## Timeline

**Week 1 (Jan 16-22):** Create camera-device
**Week 2 (Jan 23-29):** Create edge-server
**Week 3 (Jan 30-Feb 5):** Migrate, test, document

**Total:** 3 weeks for complete refactor

---

## Risks & Mitigation

### Risk 1: Breaking Existing Code

**Mitigation:** Keep `edge-device/` intact, create new dirs alongside

### Risk 2: Network Latency (Camera → Edge Server)

**Mitigation:** Both on same factory LAN, <5ms latency

### Risk 3: Edge Server Single Point of Failure

**Mitigation:**
- Multiple camera devices keep working (queue CIDs)
- Edge server restarts, processes queue
- HA setup (2x edge servers with load balancer)

---

## Success Criteria

✅ Camera device is simple (<200 lines)
✅ Edge server handles 10+ cameras
✅ Total latency <100ms (CID → LDO)
✅ Works offline (edge server caches context)
✅ Cost per camera <$100
✅ Easy to deploy (Docker Compose)

---

**Next Steps:**

1. Get approval on this plan
2. Start Phase 1: Create camera-device
3. Test with one camera + edge server
4. Scale to multiple cameras
5. Deploy to factory

**Questions?** Review and approve before we begin refactor.

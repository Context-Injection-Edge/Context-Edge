# Video Capture and Fusion Architecture

**Updated:** 2025-01-16

---

## Overview

Context Edge now includes **video capture as part of the fusion process**. Video is the raw visual data that gets fused with context metadata and sensor data to create complete Labeled Data Objects (LDOs).

---

## Complete Data Flow

```
Edge Device (Raspberry Pi/Jetson)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Camera captures video stream (30 FPS)
2. QR code detected → Extract CID
3. Record video clip (configurable)
   ├─ 2 seconds BEFORE QR detection (buffer)
   └─ 3 seconds AFTER detection
   = 5-second clip total
4. Send CID + video clip + timestamp to Edge Server

Edge Server (Plant Server)
━━━━━━━━━━━━━━━━━━━━━━━━━━
5. Receive CID + video + timestamp
6. Fetch context from Redis (CID → product, batch, etc.)
7. Read PLC sensors (temperature, vibration, etc.)
8. **CIM FUSION** (PATENTED):
   ├─ Video footage (raw visual data)
   ├─ Context metadata (what the part IS)
   └─ Sensor data (how it was MADE)
   = Complete fused data package
9. Run AI inference on fused data
10. Store video to data-ingestion service
11. Store metadata + reference in PostgreSQL
12. Return LDO ID to edge device

Data Ingestion Service
━━━━━━━━━━━━━━━━━━━━━━
13. Store video file + metadata
14. Make available for ML training pipeline
```

---

## Video Capture Modes

**The manufacturer decides which mode based on their use case:**

### Mode 1: Event-Triggered (Default) ✅

**When**: QR code detected

**Duration**: 5 seconds (2s before + 3s after)

**Use Case**:
- Quality control with visual inspection
- Product tracking with video evidence
- Defect detection

**Configuration:**
```bash
export VIDEO_CAPTURE_MODE="event"
export VIDEO_DURATION="5.0"  # seconds
export VIDEO_BUFFER="2.0"     # seconds before event
```

---

### Mode 2: Continuous Recording

**When**: Always recording

**Duration**: Continuous

**Use Case**:
- Full production line recording
- Forensic analysis
- Compliance/audit trail

**Configuration:**
```bash
export VIDEO_CAPTURE_MODE="continuous"
export VIDEO_SEGMENT_DURATION="60.0"  # 1-minute segments
```

**Storage**: Much higher (30 FPS × 8 hours = ~50GB/day per camera)

---

### Mode 3: Alarm-Only

**When**: Only when anomaly/defect detected by AI

**Duration**: 10 seconds around alarm

**Use Case**:
- Predictive maintenance
- Anomaly detection
- Reduce storage costs

**Configuration:**
```bash
export VIDEO_CAPTURE_MODE="alarm"
export VIDEO_DURATION="10.0"
export VIDEO_BUFFER="5.0"  # 5s before alarm
```

---

### Mode 4: Hybrid

**When**: Always record low-res + high-res on events

**Duration**:
- Low-res: Continuous (480p, 15 FPS)
- High-res: 5s clips on QR/alarm (1080p, 30 FPS)

**Use Case**:
- Balance between full coverage and storage
- Forensic capability + quality inspection

**Configuration:**
```bash
export VIDEO_CAPTURE_MODE="hybrid"
export VIDEO_LOWRES_FPS="15"
export VIDEO_LOWRES_RESOLUTION="480p"
export VIDEO_HIGHRES_DURATION="5.0"
```

---

## CIM Fusion with Video

### The Complete Fusion

```python
fused_data = {
    # Raw visual data
    "video_file": "CID-PROD-12345_20250116_103000.mp4",

    # Context metadata (from Redis via QR)
    "context": {
        "product_id": "WIDGET-A",
        "batch_id": "BATCH-20250116-01",
        "operator_id": "OP-123",
        "line": "Line-1",
        "station": "Station-1"
    },

    # Sensor data (from PLC)
    "sensor_data": {
        "temperature": 72.5,
        "vibration": 2.3,
        "pressure": 98.5,
        "humidity": 45.2,
        "cycle_time": 18.7
    },

    # Timestamps
    "timestamp": "2025-01-16T10:30:00",
    "fusion_timestamp": "2025-01-16T10:30:00.123",

    # Metadata
    "device_id": "EDGE-Line1-Station1",
    "cid": "CID-PROD-12345"
}
```

### Why Video is Essential

**Visual Inspection Models:**
- Surface defects (cracks, scratches)
- Contamination detection
- Assembly verification
- Dimensional accuracy

**Forensic Analysis:**
- Why did this part fail?
- What was happening at the time?
- Operator actions

**Model Training:**
- 100% labeled video clips
- No manual annotation needed
- Ground truth from context + sensors

---

## Storage Architecture

### Edge Device

```
/tmp/context-edge-videos/
├── CID-PROD-12345_20250116_103000.mp4  (5s, ~2MB)
├── CID-PROD-12346_20250116_103015.mp4
└── ...

Auto-cleanup after successful upload
```

### Edge Server (Transient)

```
Video received → Immediately sent to data-ingestion
No long-term storage on edge server
```

### Data Ingestion (Permanent)

```
/app/storage/ldos/
├── ldo_abc123_1705420800/
│   ├── video.mp4
│   └── metadata.json
├── ldo_def456_1705420815/
│   ├── video.mp4
│   └── metadata.json
└── ...

OR

s3://context-edge-ldos/
├── ldo_abc123_1705420800/video.mp4
└── ldo_abc123_1705420800/metadata.json
```

### PostgreSQL (Metadata + Reference)

```sql
metadata_payloads:
├── cid (PK)
├── payload_data (JSON)
│   ├── context
│   ├── sensor_data
│   ├── video_storage_id  ← Reference to data-ingestion
│   └── video_file        ← Filename
├── created_at
└── is_mock
```

---

## Storage Estimates

### Event-Triggered Mode (5-second clips)

```
Assumptions:
- 1080p video at 30 FPS
- H.264 compression
- ~400 KB/second
- 5-second clips = ~2 MB per clip

Storage per day:
- 100 parts/day × 2 MB = 200 MB/day
- 1000 parts/day × 2 MB = 2 GB/day
- 10,000 parts/day × 2 MB = 20 GB/day

Monthly: 600 MB to 600 GB depending on volume
```

### Continuous Mode

```
Assumptions:
- 1080p at 30 FPS
- 8-hour shifts
- ~1.4 GB/hour

Storage per camera per day:
- 8 hours × 1.4 GB = ~11 GB/day/camera
- 10 cameras × 11 GB = 110 GB/day

Monthly: ~3.3 TB for 10 cameras

⚠️ Requires S3/MinIO for cost-effective storage
```

---

## API Changes

### Edge Device → Edge Server

**Old (CID only):**
```bash
POST /cid
Content-Type: application/json

{
  "cid": "CID-PROD-12345",
  "camera_id": "EDGE-Line1-Station1",
  "timestamp": "2025-01-16T10:30:00"
}
```

**New (CID + video):**
```bash
POST /cid
Content-Type: multipart/form-data

cid=CID-PROD-12345
device_id=EDGE-Line1-Station1
timestamp=2025-01-16T10:30:00
video=@CID-PROD-12345_20250116_103000.mp4
```

### Edge Server → Data Ingestion

```bash
POST /ingest/ldo
Content-Type: multipart/form-data

video=@video.mp4
metadata={
  "cid": "CID-PROD-12345",
  "context": {...},
  "sensor_data": {...},
  "prediction": {...},
  "timestamp": "2025-01-16T10:30:00",
  "device_id": "EDGE-Line1-Station1"
}
```

---

## Configuration Summary

### Edge Device

```bash
# Video capture mode
VIDEO_CAPTURE_MODE=event           # event, continuous, alarm, hybrid

# Event/alarm mode settings
VIDEO_DURATION=5.0                 # Total clip duration (seconds)
VIDEO_BUFFER=2.0                   # Seconds before event

# Continuous mode settings
VIDEO_SEGMENT_DURATION=60.0        # Segment length

# Hybrid mode settings
VIDEO_LOWRES_FPS=15
VIDEO_LOWRES_RESOLUTION=480p
VIDEO_HIGHRES_DURATION=5.0

# Storage
VIDEO_OUTPUT_DIR=/tmp/context-edge-videos
```

### Edge Server

```bash
# Data ingestion integration
DATA_INGESTION_URL=http://data-ingestion:8001
```

### Data Ingestion

```bash
# Storage backend
STORAGE_PATH=/app/storage/ldos     # Local filesystem
# OR
S3_BUCKET=context-edge-ldos        # S3/MinIO
S3_ENDPOINT=https://s3.amazonaws.com
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
```

---

## ML Training Integration

### LDO Format for Training

```json
{
  "ldo_id": "LDO-20250116103000-12345",
  "video_path": "/data/ldos/ldo_abc123/video.mp4",
  "context": {
    "product_id": "WIDGET-A",
    "batch_id": "BATCH-20250116-01"
  },
  "sensor_data": {
    "temperature": 72.5,
    "vibration": 2.3
  },
  "ground_truth": "defective",
  "defect_type": "surface_crack",
  "timestamp": "2025-01-16T10:30:00"
}
```

### Training Pipeline Reads:

1. **Video file**: For visual inspection models
2. **Context**: For multi-modal fusion models
3. **Sensors**: For correlation analysis
4. **Ground truth**: Perfect labels (no manual annotation!)

---

## Summary

| Aspect | Implementation |
|--------|---------------|
| **Video capture** | Configurable (event/continuous/alarm/hybrid) |
| **Video duration** | Default: 5 seconds (2s buffer + 3s post-event) |
| **Storage** | data-ingestion → filesystem or S3 |
| **Fusion** | Video + Context (Redis) + Sensors (PLC) |
| **Metadata** | PostgreSQL with video_storage_id reference |
| **ML training** | Reads video + metadata from data-ingestion |
| **Manufacturer choice** | Configure mode based on use case |

**Video is now a core part of the fusion, not optional!** 📹🔗🤖

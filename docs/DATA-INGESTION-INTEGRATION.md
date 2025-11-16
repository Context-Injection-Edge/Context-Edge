# Data Ingestion Service - Integration Guide

**Status:** Optional (not required for base operation)

---

## Overview

The data-ingestion service provides LDO storage to filesystem/S3 for ML training pipelines. In the current architecture, **it is optional** because edge-server stores LDOs directly in PostgreSQL.

---

## Current Architecture (Without data-ingestion)

```
Edge Device → Edge Server → PostgreSQL (LDOs stored here)
                                ↓
                          ML Training reads from PostgreSQL
```

**This works fine for:**
- Small to medium deployments (< 100K LDOs)
- PostgreSQL has sufficient storage
- No video clips needed
- Single-site deployments

---

## When to Add data-ingestion

### Use Case 1: Large-scale ML Training

**Problem:** PostgreSQL not ideal for storing millions of LDOs + large files

**Solution:**
```
Edge Server → PostgreSQL (metadata only)
            ↓
            └─→ data-ingestion → S3/MinIO (complete LDOs)
                                      ↓
                              ML Training Pipeline
```

**Implementation:**
```python
# In edge-server/app/services/ldo_generator.py
async def create_ldo(self, cid, fused_data, prediction):
    # 1. Store metadata in PostgreSQL
    ldo_id = await self._store_to_postgres(cid, fused_data, prediction)

    # 2. Optionally send to data-ingestion for S3 storage
    if os.getenv("USE_DATA_INGESTION", "false") == "true":
        await self._send_to_data_ingestion(ldo_id, fused_data)

    return ldo_id
```

---

### Use Case 2: Video Clip Storage

**Problem:** Need to store video evidence for visual inspection models

**Solution:**
```
Edge Device (with video capture):
├─ Scan QR → Extract CID
├─ Capture 5-second video clip
└─ Send both to Edge Server

Edge Server:
├─ Store metadata in PostgreSQL
└─ Upload video + LDO to data-ingestion
```

**Implementation:**

**Edge Device** (enhanced):
```python
# edge-device/edge_app/inputs/camera_stream.py
class CameraStreamInput:
    def _handle_cid_detected(self, cid: str):
        # Capture 5-second video clip
        video_clip = self.capture_video_clip(duration=5)

        # Send CID + video to edge server
        self.send_cid(cid, video_clip=video_clip)
```

**Edge Server** (enhanced):
```python
# edge-server/app/main.py
@app.post("/cid")
async def receive_cid(
    request: CIDRequest,
    video: Optional[UploadFile] = None
):
    # ... existing fusion logic ...

    # Upload to data-ingestion if video provided
    if video:
        await upload_to_data_ingestion(ldo_id, fused_data, video)
```

---

### Use Case 3: Multi-Site Cloud Sync

**Problem:** Multiple factories need to share training data

**Solution:**
```
Factory A → Edge Server A → PostgreSQL A ─┐
                                          ├─→ data-ingestion → S3 (central)
Factory B → Edge Server B → PostgreSQL B ─┘                     ↓
                                                    ML Training (cloud)
```

---

### Use Case 4: Backup and Archival

**Problem:** PostgreSQL storage fills up, need long-term archival

**Solution:**
```
Nightly batch job:
├─ Export old LDOs from PostgreSQL
├─ Upload to data-ingestion → S3 Glacier
└─ Delete from PostgreSQL (keep metadata only)
```

**Implementation:**
```bash
# Cron job: Export LDOs older than 90 days
0 2 * * * python3 /opt/scripts/export-old-ldos.py
```

```python
# export-old-ldos.py
import psycopg2
import requests

# Get old LDOs from PostgreSQL
ldos = get_ldos_older_than(days=90)

# Upload to data-ingestion
for ldo in ldos:
    requests.post(
        "http://data-ingestion:8001/ingest/ldo",
        files={"video": None},  # No video
        data={"metadata": json.dumps(ldo)}
    )

# Delete from PostgreSQL
delete_ldos(ldos)
```

---

## Decision Matrix

| Scenario | Use PostgreSQL Only | Add data-ingestion |
|----------|---------------------|-------------------|
| < 100K LDOs/year | ✅ | ❌ |
| > 1M LDOs/year | ❌ | ✅ |
| No video clips | ✅ | ❌ |
| Video clips needed | ❌ | ✅ |
| Single site | ✅ | ❌ |
| Multi-site deployment | ❌ | ✅ |
| PostgreSQL storage sufficient | ✅ | ❌ |
| Need S3/cloud storage | ❌ | ✅ |

---

## API Reference

### POST /ingest/ldo

Upload LDO to data-ingestion service.

**Request:**
```bash
curl -X POST http://localhost:8001/ingest/ldo \
  -F "video=@clip.mp4" \
  -F 'metadata={
    "ldo_id": "LDO-123",
    "sensor_data": {...},
    "context": {...},
    "prediction": {...}
  }'
```

**Response:**
```json
{
  "id": "ldo_abc123_1705420800",
  "status": "ingested",
  "size_bytes": 2457600
}
```

### GET /ingest/list

List all ingested LDOs.

**Request:**
```bash
curl http://localhost:8001/ingest/list?skip=0&limit=100
```

**Response:**
```json
{
  "total": 156,
  "ldos": [
    {
      "id": "ldo_abc123_1705420800",
      "status": "ingested",
      "filename": "clip.mp4",
      "created_at": "2025-01-16T10:30:00",
      "size_bytes": 2457600
    }
  ]
}
```

---

## Configuration

### Enable data-ingestion in edge-server

**docker-compose.yml:**
```yaml
edge-server:
  environment:
    USE_DATA_INGESTION: "true"
    DATA_INGESTION_URL: "http://data-ingestion:8001"
```

**Or environment variable:**
```bash
export USE_DATA_INGESTION=true
export DATA_INGESTION_URL=http://data-ingestion:8001
```

---

## Summary

**Current State (2025-01-16):**
- ✅ Edge server stores LDOs in PostgreSQL
- ✅ Works fine for most use cases
- ❌ data-ingestion **not required** for base operation

**Future Enhancements:**
- 📹 Add video clip capture and storage
- 🌐 Multi-site cloud sync via S3
- 📦 Archival of old LDOs
- 🚀 Large-scale ML training (millions of LDOs)

**Recommendation:** Start simple (PostgreSQL only), add data-ingestion when you need:
1. Video storage
2. S3/cloud storage
3. Multi-site deployments
4. > 1M LDOs/year

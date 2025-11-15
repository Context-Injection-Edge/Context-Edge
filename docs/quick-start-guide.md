# Context Edge - Quick Start Guide

Welcome to Context Edge! This guide will help you get started with the **Industrial AI Platform** in under 30 minutes.

Context Edge provides real-time monitoring, predictive maintenance, and automated quality control for manufacturing. The platform serves operators (live dashboards), engineers (MER smart work orders), and data scientists (perfect ML training data).

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [First Steps](#first-steps)
4. [Deploy Edge Device](#deploy-edge-device)
5. [Testing End-to-End](#testing-end-to-end)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Docker & Docker Compose** (v20.10+ recommended)
- **Python 3.9+** (for edge device development)
- **Node.js 18+** (for UI development)
- **Git**

### Optional

- **NVIDIA Jetson device** (for production edge deployment)
- **USB webcam** (for local testing)

### Hardware Requirements

- **Development Machine**: 4GB RAM, 10GB disk space
- **Edge Device**: NVIDIA Jetson Orin Nano/NX (recommended) or any Linux device with USB camera

---

## Local Development Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/context-edge.git
cd context-edge
```

### Step 2: Start the Services

```bash
# Start PostgreSQL, Redis, Context Service, and Data Ingestion
docker-compose up -d

# Verify services are running
docker-compose ps
```

Expected output:
```
NAME                      STATUS
context-edge-postgres-1           running
context-edge-redis-1              running
context-edge-context-service-1    running
context-edge-data-ingestion-1     running
```

### Step 3: Verify API Endpoints

```bash
# Check Context Service health
curl http://localhost:8000/health

# Check Data Ingestion health
curl http://localhost:8001/health

# View API documentation
open http://localhost:8000/docs
```

---

## First Steps

### Step 4: Start the Customer Portal UI

```bash
cd context-edge-ui
npm install
npm run dev
```

Visit: **http://localhost:3000**

### Step 5: Populate Demo Data

```bash
cd ../demo
python populate_demo_data.py
```

This creates sample metadata for QR codes: `QR001`, `QR002`, `QR003`

### Step 6: Access the Admin Panel

Navigate to: **http://localhost:3000/admin**

You should see the 3 demo metadata payloads listed.

**Try creating a new payload:**

1. Click "Create New Metadata Payload"
2. Enter CID: `QR004`
3. Enter metadata JSON:
```json
{
  "product_name": "Test Widget",
  "batch_number": "BATCH_TEST",
  "pressure_threshold": 60.0,
  "temperature_range": {"min": 15, "max": 35},
  "defect_criteria": ["scratch", "dent", "crack"]
}
```
4. Click "Create"

**Try bulk CSV import:**

1. Download sample CSV: `demo/sample_metadata.csv`
2. Click "Choose File" under "Bulk Import from CSV"
3. Select the CSV file
4. Click "Import CSV"

---

## Deploy Edge Device

### Step 7: Install the Edge SDK

```bash
cd edge-device
pip install -e .
```

This installs the `context-edge-sdk` package in development mode.

### Step 8: Test QR Detection (Without Camera)

Create a test script `test_qr.py`:

```python
from context_edge.context_injector import ContextInjectionModule
import json

# Initialize CIM
cim = ContextInjectionModule(
    context_service_url="http://localhost:8000",
    redis_host="localhost"
)

# Simulate sensor data
sensor_data = {
    "temperature": 25.5,
    "pressure": 1013.25,
    "vibration": 0.05
}

# Test context injection with QR001
ldo = cim.inject_context(sensor_data, detected_cid="QR001")

print("Generated LDO:")
print(json.dumps(ldo, indent=2))
```

Run:
```bash
python test_qr.py
```

Expected output:
```json
{
  "sensor_data": {
    "temperature": 25.5,
    "pressure": 1013.25,
    "vibration": 0.05
  },
  "context_metadata": {
    "cid": "QR001",
    "metadata": {
      "product_name": "Widget A",
      "batch_number": "BATCH001",
      "pressure_threshold": 50.5
    },
    "timestamp": "2024-11-14T..."
  },
  "timestamp": 1700000000.0,
  "cid": "QR001"
}
```

### Step 9: Run with Webcam (Optional)

If you have a USB webcam and a printed QR code:

1. Generate a QR code for `QR001` using https://www.qr-code-generator.com/
2. Print it or display it on your phone
3. Run the edge device:

```bash
context-edge-demo
```

The system will:
- Start capturing video from your webcam
- Scan for QR codes
- When a QR is detected, retrieve metadata from Context Service
- Generate LDOs in `ldo_output/` directory

---

## Testing End-to-End

### Step 10: Upload an LDO to Data Ingestion

Create a test video or use a sample:

```bash
# Create a simple test video (requires ffmpeg)
ffmpeg -f lavfi -i testsrc=duration=5:size=640x480:rate=30 -pix_fmt yuv420p test_video.mp4
```

Upload it via API:

```bash
curl -X POST http://localhost:8001/ingest/ldo \
  -F "video=@test_video.mp4" \
  -F 'metadata={"sensor_data": {"temp": 25}, "context_metadata": {"cid": "QR001"}, "timestamp": 1700000000}'
```

Response:
```json
{
  "id": "ldo_abc123_1700000000",
  "status": "ingested",
  "message": "LDO successfully ingested",
  "size_bytes": 12345
}
```

### Step 11: Verify LDO Storage

```bash
# List all LDOs
curl http://localhost:8001/ingest/list

# Check status of specific LDO
curl http://localhost:8001/ingest/status/ldo_abc123_1700000000
```

---

## Architecture Overview

```
┌─────────────────────┐
│  Customer Portal    │  (Next.js - Port 3000)
│  - Landing Page     │
│  - Admin Panel      │
│  - Downloads        │
└─────────────────────┘

┌─────────────────────┐
│  Context Service    │  (FastAPI - Port 8000)
│  - Rich Metadata DB │
│  - Redis Cache      │
│  - CRUD API         │
└─────────────────────┘
         ↑
         │ HTTP Requests
         │
┌─────────────────────┐
│   Edge Device       │  (Python SDK)
│  - QR Decoder       │
│  - CIM (Patent Core)│
│  - LDO Generator    │
└─────────────────────┘
         │
         ↓ Upload LDOs
┌─────────────────────┐
│ Data Ingestion      │  (FastAPI - Port 8001)
│  - LDO Storage      │
│  - ML Pipeline      │
└─────────────────────┘
```

---

## Troubleshooting

### Services Won't Start

**Problem:** `docker-compose up` fails

**Solution:**
```bash
# Check logs
docker-compose logs

# Restart services
docker-compose down
docker-compose up -d
```

### Database Connection Error

**Problem:** Context Service can't connect to PostgreSQL

**Solution:**
```bash
# Wait for PostgreSQL to initialize (takes ~10 seconds)
docker-compose logs postgres

# Restart context-service
docker-compose restart context-service
```

### Redis Connection Error

**Problem:** CIM can't connect to Redis

**Solution:**
```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker exec -it context-edge-redis-1 redis-cli ping
# Should return: PONG
```

### Admin Panel Shows Empty List

**Problem:** No metadata payloads appear

**Solution:**
```bash
# Check API is accessible
curl http://localhost:8000/context

# Repopulate demo data
cd demo
python populate_demo_data.py
```

### QR Code Not Detected

**Problem:** Edge device doesn't detect QR codes

**Solutions:**
1. Ensure good lighting
2. Print QR code at least 2x2 inches
3. Hold QR code steady in front of camera
4. Check camera permissions
5. Try different QR code generator: https://www.qr-code-generator.com/

### Import Errors in Python

**Problem:** `ModuleNotFoundError: No module named 'context_edge'`

**Solution:**
```bash
cd edge-device
pip install -e .
```

---

## Next Steps

### For Developers

1. **Explore API docs**: http://localhost:8000/docs
2. **Customize metadata schema** in Admin Panel
3. **Integrate with your ERP/MES** via Context Service API
4. **Deploy to Kubernetes** (see `k8s/` directory)

### For Production

1. **Deploy Context Service** to cloud or on-prem
2. **Configure SSL/TLS** for secure communications
3. **Set up authentication** for Admin Panel
4. **Deploy Edge SDK** to NVIDIA Jetson devices
5. **Integrate with ML training pipeline**

---

## Support

- **Documentation**: `/docs`
- **GitHub Issues**: https://github.com/yourusername/context-edge/issues
- **Email**: support@admoose.pro

---

## License

Proprietary - Contact for licensing information

---

**Congratulations!** You've successfully set up Context Edge. Start labeling data at the edge!

# ML Training Backend

**Separate from Runtime Services**

This directory contains the **training infrastructure** that customers run on their GPU servers (not edge devices).

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  RUNTIME BACKEND (Always Running)                      │
│                                                         │
│  context-service/     ← FastAPI (port 8000)            │
│  data-ingestion/      ← FastAPI (port 8001)            │
│  PostgreSQL           ← Metadata storage                │
│  Redis                ← Industrial RAG                  │
└─────────────────────────────────────────────────────────┘
               ↓ Provides LDOs to training
┌─────────────────────────────────────────────────────────┐
│  TRAINING BACKEND (Runs Monthly)                       │
│                                                         │
│  ml-training/         ← This directory                 │
│  ├── train.py         ← PyTorch training               │
│  ├── convert.py       ← TensorRT conversion            │
│  ├── deploy.py        ← K8s model deployment           │
│  ├── Dockerfile       ← GPU training container         │
│  └── requirements.txt ← PyTorch, TensorRT, etc.        │
└─────────────────────────────────────────────────────────┘
```

---

## How It Works

### **1. Runtime Backend (Always On)**
- Edge devices upload LDOs to `data-ingestion` service
- LDOs stored in S3/MinIO
- Metadata stored in PostgreSQL

### **2. Training Backend (Monthly Job)**
- Reads LDOs from S3
- Trains PyTorch model on GPU server
- Converts to TensorRT
- Deploys to edge devices via Kubernetes

**Key Point:** These are SEPARATE services!

---

## Deployment Options

### **Option A: Scheduled Job (Recommended)**

```bash
# Customer runs monthly cron job
0 0 1 * * /opt/context-edge/ml-training/train.sh
```

Training runs for 6-8 hours, then exits. Server can do other work rest of month.

### **Option B: On-Demand (Manual)**

```bash
# Engineer triggers when needed
cd ml-training/
docker run --gpus all -v /data:/data \
  context-edge/ml-training:latest \
  python train.py --samples 100000
```

### **Option C: GitHub Actions (Automated)**

```yaml
# .github/workflows/mlops.yml
on:
  schedule:
    - cron: '0 0 1 * *'  # 1st of month
  workflow_dispatch:      # Manual trigger

jobs:
  train:
    runs-on: [self-hosted, gpu]
    steps:
      - uses: actions/checkout@v2
      - run: docker run --gpus all ml-training/train.py
```

---

## Hardware Requirements

### **Runtime Backend**
- CPU: 4 cores
- RAM: 16GB
- GPU: Not needed
- Storage: 500GB SSD

### **Training Backend** (Only Runs Monthly)
- CPU: 16+ cores
- RAM: 64GB+
- GPU: 1-4x NVIDIA A100/H100 (or RTX 4090 for smaller deployments)
- Storage: 2TB SSD for LDO datasets

**Can be the same physical server!** Runtime uses CPU, training uses GPU.

---

## What We Provide

### **Software Components**

1. **Training Scripts** (`ml-training/`)
   - PyTorch model definitions
   - Training loop with validation
   - Hyperparameter configs
   - TensorRT conversion

2. **Docker Containers**
   - `context-edge/ml-training:latest`
   - Includes PyTorch, CUDA, TensorRT
   - Pre-configured for Jetson deployment

3. **Deployment Tools**
   - Kubernetes manifests for model rollout
   - Gradual deployment (pilot → full)
   - Automatic rollback on failures

4. **Monitoring Dashboards**
   - Training metrics (loss, accuracy)
   - Model performance tracking
   - A/B testing results

### **What Customer Provides**

1. **Hardware**
   - GPU server (or rent AWS p4d instances)
   - Kubernetes cluster (for orchestration)

2. **Operations**
   - Schedule training jobs (cron or GitHub Actions)
   - Monitor training progress
   - Approve model deployments

---

## Quick Start

### **Step 1: Setup Training Environment**

```bash
# On GPU server
git clone https://github.com/Context-Injection-Edge/Context-Edge.git
cd Context-Edge/ml-training

# Build training container
docker build -t context-edge/ml-training .
```

### **Step 2: Run Training**

```bash
# Train model on GPU
docker run --gpus all \
  -v /data/ldos:/data \
  context-edge/ml-training \
  python train.py \
    --data-path /data \
    --output-dir /models \
    --epochs 50
```

### **Step 3: Deploy Model**

```bash
# Convert to TensorRT
python convert.py \
  --model /models/model-v2.1.pth \
  --output /models/model-v2.1.trt

# Deploy to edge devices
kubectl apply -f k8s/model-deployment-v2.1.yaml
```

---

## Integration with Runtime Backend

The training backend **reads from** the runtime backend:

```python
# train.py
import psycopg2
import boto3

# 1. Query LDOs from PostgreSQL
conn = psycopg2.connect(
    host="context-service",  # Runtime backend
    database="contextedge"
)
cursor = conn.execute("""
    SELECT ldo_id, created_at
    FROM ldos
    WHERE validated=true
    ORDER BY created_at DESC
    LIMIT 100000
""")

# 2. Download LDO files from S3
s3 = boto3.client('s3')
for ldo_id, _ in cursor:
    s3.download_file(
        'context-edge-ldos',
        f'{ldo_id}.json',
        f'/tmp/{ldo_id}.json'
    )

# 3. Train model
model = train_pytorch_model(ldos)

# 4. Register new version
register_model(model, version="2.1")
```

---

## Cost Considerations

### **Runtime Backend**
- Runs 24/7
- Modest hardware
- **Cost:** $200-500/month (server rental)

### **Training Backend**
- Runs 6-8 hours/month
- Expensive GPU
- **Cost:**
  - Own GPU server: $20K upfront (4x RTX 4090)
  - Rent AWS p4d.24xlarge: $32/hour × 8 hours = $256/month

**Total Monthly Cost:** $450-750 (very affordable!)

---

## Summary

| Component | Purpose | Always Running? | Hardware |
|-----------|---------|-----------------|----------|
| **context-service** | Metadata/RAG | ✅ Yes | CPU |
| **data-ingestion** | LDO uploads | ✅ Yes | CPU |
| **ml-training** | Model training | ❌ Monthly (8h) | GPU |

**They are SEPARATE but connected:**
- Runtime backend provides data
- Training backend consumes data, produces models
- Edge devices use models from training backend

Customer can run both on the same physical server!

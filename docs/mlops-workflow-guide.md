# MLOps Workflow Guide
**Human-in-the-Loop Model Deployment with K3s**

---

## 🎯 Overview

This guide explains the **complete MLOps workflow** for Context Edge:

1. ✅ **Training in Docker containers** (NOT in K3s - runs on GPU server)
2. ✅ **Deployment via K3s** (pushes trained models to edge devices)
3. ✅ **Human approval** (Engineer reviews and approves via UI)
4. ❌ **NO LLM needed** (no GPT-4, Claude, etc.)
5. ❌ **NO training engine needed** (no MLflow, W&B - just PyTorch + Docker)

---

## 🏗️ Architecture: Training vs Deployment

### **Training (Docker + GPU)**
```
┌──────────────────────────────────────────────┐
│  GPU Server (On-prem or Cloud)              │
│                                              │
│  docker run --gpus all \                     │
│    -v /data:/data \                          │
│    context-edge/ml-training:latest \         │
│    python train.py --samples 100000          │
│                                              │
│  ├── Downloads 100K LDOs from S3             │
│  ├── Trains PyTorch model (6-8 hours)       │
│  ├── Converts to TensorRT                   │
│  ├── Uploads model-v2.1.trt to S3           │
│  └── Registers model via API                │
└──────────────────────────────────────────────┘
         ↓ (calls context-service API)
POST /mlops/models/register
{
  "version_id": "v2.1",
  "accuracy": 0.94,
  "model_path": "s3://models/model-v2.1.trt",
  "training_samples": 100000,
  "training_date": "2025-01-15"
}
```

### **Deployment (K3s)**
```
┌──────────────────────────────────────────────┐
│  K3s Cluster (Factory Server)                │
│                                              │
│  kubectl apply -f \                          │
│    k8s/model-deployment-v2.1.yaml            │
│                                              │
│  DaemonSet: model-updater                    │
│  ├── Runs on all edge nodes                 │
│  ├── Downloads model-v2.1.trt from S3        │
│  ├── Replaces /models/current.trt           │
│  └── Restarts inference service              │
└──────────────────────────────────────────────┘
         ↓ (model deployed to edge)
┌──────────────────────────────────────────────┐
│  Edge Devices (NVIDIA Jetson)                │
│                                              │
│  Jetson devices receive new model:          │
│  ├── edge-001: model-v2.1.trt loaded ✅     │
│  ├── edge-002: model-v2.1.trt loaded ✅     │
│  ├── edge-003: model-v2.1.trt loaded ✅     │
│  └── ...                                     │
└──────────────────────────────────────────────┘
```

---

## 🔄 Complete Workflow: Training → Deployment

### **Step 1: Training (Monthly Job)**

```bash
# On GPU server (NOT in K3s)
cd /opt/context-edge/ml-training

# Run training container
docker run --gpus all \
  -v /data/ldos:/data \
  -v /models:/models \
  -e POSTGRES_HOST=context-service.local \
  -e S3_ENDPOINT=http://minio:9000 \
  context-edge/ml-training:latest \
  python train.py \
    --data-path /data \
    --output-dir /models \
    --samples 100000 \
    --epochs 50
```

**What happens inside the container:**
```python
# train.py (runs INSIDE container)

# 1. Load data
ldos = load_ldos_from_postgres(limit=100000)
ldos = download_ldos_from_s3(ldos, output_dir='/data')

# 2. Train model
model = ContextEdgeModel()
model = train_model(model, train_loader, val_loader, epochs=50)

# 3. Save PyTorch model
torch.save(model.state_dict(), '/models/model-v2.1.pth')

# 4. Convert to TensorRT
import torch2trt
model_trt = torch2trt(model, ...)
torch.save(model_trt, '/models/model-v2.1.trt')

# 5. Upload to S3
s3.upload_file('/models/model-v2.1.trt', 'models', 'model-v2.1.trt')

# 6. Register with context-service
requests.post('http://context-service:8000/mlops/models/register', json={
    "version_id": "v2.1",
    "accuracy": 0.94,
    "model_path": "s3://models/model-v2.1.trt",
    "training_samples": 100000,
    "training_date": "2025-01-15T08:00:00Z"
})
```

**Training container exits after 6-8 hours**

---

### **Step 2: Engineer Reviews in UI**

Engineer opens http://localhost:3000/admin/models

**UI shows:**
```
╔═══════════════════════════════════════════════╗
║  🤖 New Model Available!                      ║
║                                               ║
║  Version: v2.1                                ║
║  Accuracy: 94% (+5% improvement!)             ║
║  Trained on: 100,000 LDOs                     ║
║  Training date: 2025-01-15 08:00              ║
║  Status: Ready for deployment                 ║
║                                               ║
║  [ Deploy to Pilot (5 devices) ]              ║
║  [ View Training Metrics ]                    ║
║  [ Reject Model ]                             ║
╚═══════════════════════════════════════════════╝
```

**Engineer clicks "Deploy to Pilot"**

---

### **Step 3: Pilot Deployment (5 Devices)**

**UI makes API call:**
```javascript
// UI calls context-service API
fetch('http://localhost:8000/mlops/models/v2.1/deploy-pilot', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    pilot_device_ids: ['edge-001', 'edge-002', 'edge-003', 'edge-004', 'edge-005']
  })
})
```

**Backend triggers K3s deployment:**
```bash
# context-service calls kubectl
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: model-updater-v2-1-pilot
spec:
  selector:
    matchLabels:
      app: model-updater
  template:
    metadata:
      labels:
        app: model-updater
        version: v2.1
    spec:
      nodeSelector:
        pilot: "true"  # Only pilot nodes
      containers:
      - name: model-updater
        image: context-edge/model-updater:latest
        env:
        - name: MODEL_VERSION
          value: "v2.1"
        - name: MODEL_PATH
          value: "s3://models/model-v2.1.trt"
        volumeMounts:
        - name: models
          mountPath: /models
      volumes:
      - name: models
        hostPath:
          path: /opt/context-edge/models
EOF
```

**What happens on edge devices:**
```bash
# DaemonSet pod runs on each pilot Jetson
# 1. Download model from S3
aws s3 cp s3://models/model-v2.1.trt /models/model-v2.1.trt

# 2. Replace current model
mv /models/current.trt /models/current.trt.backup
ln -s /models/model-v2.1.trt /models/current.trt

# 3. Restart inference service
systemctl restart context-edge-inference
```

**Pilot devices now running model v2.1!**

---

### **Step 4: Monitor Pilot (24-48 hours)**

**UI shows pilot metrics:**
```
╔═══════════════════════════════════════════════╗
║  📊 Pilot Deployment Metrics                  ║
║                                               ║
║  Version: v2.1                                ║
║  Pilot devices: 5/5 online                    ║
║  Monitoring duration: 36 hours                ║
║                                               ║
║  Predictions: 12,543 total                    ║
║  Accuracy (validated): 95.2%                  ║
║  False positive rate: 2.1% ✅                 ║
║  False negative rate: 2.7% ✅                 ║
║  Errors: 0 ✅                                 ║
║  Avg inference time: 87ms ✅                  ║
║                                               ║
║  [ ✅ Deploy to All (50 devices) ]            ║
║  [ ❌ Rollback to v2.0 ]                      ║
╚═══════════════════════════════════════════════╝
```

**Metrics look good! Engineer clicks "Deploy to All"**

---

### **Step 5: Full Deployment (50 Devices)**

**UI makes API call:**
```javascript
fetch('http://localhost:8000/mlops/models/v2.1/deploy-all', {
  method: 'POST'
})
```

**Backend triggers K3s deployment:**
```bash
# Remove nodeSelector to deploy to ALL nodes
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: model-updater-v2-1-all
spec:
  selector:
    matchLabels:
      app: model-updater
  template:
    metadata:
      labels:
        app: model-updater
        version: v2.1
    spec:
      # NO nodeSelector - runs on ALL nodes
      containers:
      - name: model-updater
        image: context-edge/model-updater:latest
        env:
        - name: MODEL_VERSION
          value: "v2.1"
        - name: MODEL_PATH
          value: "s3://models/model-v2.1.trt"
        volumeMounts:
        - name: models
          mountPath: /models
      volumes:
      - name: models
        hostPath:
          path: /opt/context-edge/models
EOF
```

**All 50 edge devices now running model v2.1!**

---

## 🚫 What We DON'T Need

### **1. NO LLM (Large Language Model)**

```python
# ❌ We DON'T use LLMs like this:
from openai import OpenAI
client = OpenAI()

# NO text generation
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Predict bearing failure"}]
)
```

**Why not?**
- ✅ We use **PyTorch neural network** (trained on sensor data)
- ✅ Structured prediction (5 failure modes)
- ✅ 1000x faster than LLMs (<100ms vs 2-5 seconds)
- ✅ 1000x cheaper (no API calls)
- ✅ Runs on edge (no internet required)

---

### **2. NO Training Engine/Platform**

```python
# ❌ We DON'T need MLflow, Weights & Biases, etc.

# Simple PyTorch training is enough:
model = ContextEdgeModel()
optimizer = optim.AdamW(model.parameters(), lr=1e-4)

for epoch in range(50):
    for batch in train_loader:
        loss = criterion(model(batch), labels)
        loss.backward()
        optimizer.step()

torch.save(model.state_dict(), 'model-v2.1.pth')
```

**Why not?**
- ✅ Training is simple (PyTorch + Docker)
- ✅ We can add MLflow later if needed (nice-to-have)
- ✅ For now: just train, save, deploy

---

### **3. NO Embedding Model for RAG**

```python
# ❌ We DON'T use vector embeddings like this:
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')

# NO vector search
query_embedding = model.encode("bearing failure")
results = vector_db.search(query_embedding)
```

**Why not?**
- ✅ Industrial RAG is **simple key-value lookup**
- ✅ Redis GET (not vector search)
- ✅ Sub-millisecond retrieval
- ✅ No embeddings needed

**Embeddings ARE used in the PyTorch model** (but NOT for RAG!):
```python
# Embeddings IN the model (train.py)
self.product_embedding = nn.Embedding(100, 16)  # Learned during training
self.recipe_embedding = nn.Embedding(50, 16)
self.asset_embedding = nn.Embedding(200, 16)

# These are part of the neural network weights
# NOT used for RAG - used for prediction
```

---

## 🖥️ UI Integration

### **Update MLOps Dashboard**

Update `ui/src/app/admin/models/page.tsx` to use new API endpoints:

```typescript
// Fetch pending models
const fetchPendingModels = async () => {
  const response = await fetch('http://localhost:8000/mlops/models/pending');
  const data = await response.json();
  setPendingModels(data.models);
};

// Deploy to pilot
const deployToPilot = async (versionId: string) => {
  const pilotDevices = ['edge-001', 'edge-002', 'edge-003', 'edge-004', 'edge-005'];

  const response = await fetch(`http://localhost:8000/mlops/models/${versionId}/deploy-pilot`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ pilot_device_ids: pilotDevices })
  });

  const result = await response.json();
  alert(result.message);

  // Start monitoring
  startPilotMonitoring(versionId);
};

// Monitor pilot metrics
const startPilotMonitoring = async (versionId: string) => {
  const interval = setInterval(async () => {
    const response = await fetch(`http://localhost:8000/mlops/deployment/${versionId}/metrics`);
    const metrics = await response.json();

    setPilotMetrics(metrics);

    // After 24-48 hours, engineer can deploy to all
    if (metrics.monitoring_duration_hours >= 24) {
      setCanDeployToAll(true);
    }
  }, 60000); // Poll every minute
};

// Deploy to all devices
const deployToAll = async (versionId: string) => {
  const response = await fetch(`http://localhost:8000/mlops/models/${versionId}/deploy-all`, {
    method: 'POST'
  });

  const result = await response.json();
  alert(result.message);
};

// Rollback
const rollback = async (versionId: string, rollbackToVersion: string) => {
  const response = await fetch(`http://localhost:8000/mlops/models/${versionId}/rollback`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ rollback_to_version: rollbackToVersion })
  });

  const result = await response.json();
  alert(result.message);
};
```

---

## 📅 Production Schedule

### **Monthly Training Workflow**

```bash
# cron job on GPU server (runs 1st of every month at 11pm)
0 23 1 * * /opt/context-edge/ml-training/run-training.sh
```

**`run-training.sh`:**
```bash
#!/bin/bash

echo "🚀 Starting monthly ML training..."

# Run training container
docker run --gpus all \
  -v /data/ldos:/data \
  -v /models:/models \
  -e POSTGRES_HOST=context-service.factory.local \
  -e S3_ENDPOINT=http://minio.factory.local:9000 \
  context-edge/ml-training:latest \
  python train.py \
    --data-path /data \
    --output-dir /models \
    --samples 100000 \
    --epochs 50

echo "✅ Training complete! Model registered for engineer review."
```

**Next morning:**
- Engineer arrives, sees notification: "New model v2.3 ready!"
- Reviews metrics
- Deploys to pilot
- Monitors 24-48 hours
- Deploys to all or rolls back

---

## 🎯 Summary

### **What We Built:**

1. ✅ **Training in Docker** (runs on GPU server, NOT in K3s)
2. ✅ **Deployment via K3s** (DaemonSet pushes models to edge)
3. ✅ **Human in the loop** (Engineer approves via UI)
4. ✅ **Gradual rollout** (Pilot → Monitor → All devices)
5. ✅ **Rollback capability** (If pilot fails, revert to previous version)

### **What We DON'T Need:**

1. ❌ **NO LLM** (GPT-4, Claude, etc.)
2. ❌ **NO training engine** (MLflow, W&B - optional later)
3. ❌ **NO vector embeddings** (for RAG - just Redis key-value)
4. ❌ **NO complex orchestration** (K3s handles deployment, not training)

### **Key Technologies:**

- **Training**: Docker + PyTorch + NVIDIA GPUs
- **Deployment**: K3s DaemonSet + S3/MinIO
- **Monitoring**: Redis + REST APIs
- **UI**: Next.js + React (human approval)

**That's it! Simple, effective, production-ready.**

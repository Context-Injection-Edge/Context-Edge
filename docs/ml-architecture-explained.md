# Context Edge ML Architecture: Complete Explanation

**How Machine Learning Works in Context Edge**

---

## Overview: Two Separate Loops

Context Edge uses a **dual-loop architecture**:

1. **⚡ Real-Time Inference Loop** (Edge) - Predictions happen in <100ms
2. **🔄 Continuous Learning Loop** (Cloud) - Models improve over weeks/months

These loops are **independent but connected** through Labeled Data Objects (LDOs).

---

## 🏗️ Complete ML Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  EDGE DEVICE (NVIDIA Jetson) - REAL-TIME INFERENCE LOOP        │
│                                                                 │
│  ┌──────────────┐                                              │
│  │ QR Scan      │ "QM-BATCH-12345"                             │
│  └──────┬───────┘                                              │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────────────────────────────┐                      │
│  │ Industrial RAG (Redis Context Store) │ <── NOT ML Training! │
│  │                                      │                      │
│  │ Retrieves in <10ms:                 │                      │
│  │ • Product: "Motor Assembly Type A"  │                      │
│  │ • Thresholds: temp_max=85°C         │                      │
│  │ • Asset data: "Installed 2024-01-15"│                      │
│  │ • Runtime state: "Cycle count: 1250"│                      │
│  └──────────────┬───────────────────────┘                      │
│                 │                                              │
│                 ▼                                              │
│  ┌──────────────────────────────────┐                         │
│  │ Sensor Fusion                   │                         │
│  │                                 │                         │
│  │ OPC UA/Modbus reads:            │                         │
│  │ • Vibration X: 1.8g             │                         │
│  │ • Vibration Y: 1.2g             │                         │
│  │ • Temperature: 82°C             │                         │
│  │ • Current: 12.5A                │                         │
│  └──────────────┬───────────────────┘                         │
│                 │                                              │
│                 ▼                                              │
│  ┌──────────────────────────────────────────┐                 │
│  │ AI Model Inference (TensorRT)           │                 │
│  │                                          │                 │
│  │ Input: [1.8, 1.2, 82, 12.5, ...context] │                 │
│  │         ↓                                │                 │
│  │ Neural Network (loaded from .trt file)  │                 │
│  │         ↓                                │                 │
│  │ Output:                                  │                 │
│  │ • Prediction: "Bearing Wear"            │                 │
│  │ • Confidence: 0.87                      │                 │
│  │ • Latency: 45ms                         │                 │
│  └──────────────┬───────────────────────────┘                 │
│                 │                                              │
│                 ▼                                              │
│  ┌──────────────────────────────────────────┐                 │
│  │ Decision Logic                           │                 │
│  │                                          │                 │
│  │ IF confidence > 0.8:                    │                 │
│  │   → Generate MER (Maintenance Event)    │                 │
│  │   → Alert engineer                      │                 │
│  │ ELSE:                                   │                 │
│  │   → Queue for human validation          │                 │
│  └──────────────┬───────────────────────────┘                 │
│                 │                                              │
│                 ▼                                              │
│  ┌──────────────────────────────────────────┐                 │
│  │ LDO Generator                            │                 │
│  │                                          │                 │
│  │ Creates Labeled Data Object:            │                 │
│  │ {                                       │                 │
│  │   "sensor_data": {...},                 │                 │
│  │   "context": {...from Redis RAG},       │                 │
│  │   "prediction": "Bearing Wear",         │                 │
│  │   "confidence": 0.87,                   │                 │
│  │   "ground_truth_label": "Bearing Wear", │ ← 100% accurate! │
│  │   "video_clip": "5sec.mp4",             │                 │
│  │   "timestamp": 1700000000               │                 │
│  │ }                                       │                 │
│  └──────────────┬───────────────────────────┘                 │
│                 │                                              │
│                 ▼ Upload to cloud                             │
└─────────────────┼───────────────────────────────────────────────┘
                  │
                  │
┌─────────────────┼───────────────────────────────────────────────┐
│  CLOUD/CENTRAL SERVER - CONTINUOUS LEARNING LOOP               │
│                 │                                              │
│                 ▼                                              │
│  ┌──────────────────────────────────────────┐                 │
│  │ LDO Storage (S3/MinIO)                  │                 │
│  │                                          │                 │
│  │ Stores millions of LDOs:                │                 │
│  │ • 100% accurately labeled                │                 │
│  │ • Sensor data + context + video         │                 │
│  │ • Perfect for training                   │                 │
│  └──────────────┬───────────────────────────┘                 │
│                 │                                              │
│                 ▼                                              │
│  ┌──────────────────────────────────────────┐                 │
│  │ Feedback Queue                           │                 │
│  │                                          │                 │
│  │ Low-confidence predictions (<60%):      │                 │
│  │ • Engineer validates: ✓ Correct / ✗ Wrong │              │
│  │ • Adds notes: "Belt was loose"          │                 │
│  │ • Triggers retraining when N=1000+      │                 │
│  └──────────────┬───────────────────────────┘                 │
│                 │                                              │
│                 ▼                                              │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Model Training Pipeline (Triggered by GitHub Actions)   │ │
│  │                                                          │ │
│  │ 1. Data Preparation:                                    │ │
│  │    • Pull 100K validated LDOs from S3                   │ │
│  │    • Split: 80% train, 10% val, 10% test               │ │
│  │    • Normalize sensor values                            │ │
│  │                                                          │ │
│  │ 2. Model Training (PyTorch):                            │ │
│  │    • Architecture: ResNet-50 backbone                   │ │
│  │    • Input: [vibration_x, vibration_y, temp, current, ..] │
│  │    • Output: [normal, bearing_wear, belt_slip, ...]    │ │
│  │    • Loss: CrossEntropy                                 │ │
│  │    • Optimizer: AdamW                                   │ │
│  │    • Epochs: 50 (with early stopping)                   │ │
│  │    • Hardware: 4x NVIDIA A100 GPUs                      │ │
│  │    • Duration: 6-8 hours                                │ │
│  │                                                          │ │
│  │ 3. Model Validation:                                    │ │
│  │    • Accuracy > 92%? ✓                                  │ │
│  │    • FPR < 5%? ✓                                        │ │
│  │    • Latency < 100ms on Jetson? ✓                      │ │
│  │                                                          │ │
│  │ 4. TensorRT Optimization:                               │ │
│  │    • Convert PyTorch → ONNX → TensorRT                 │ │
│  │    • INT8 quantization for Jetson                       │ │
│  │    • Size: 500MB → 50MB                                │ │
│  │    • Latency: 200ms → 45ms                             │ │
│  │                                                          │ │
│  │ 5. Model Versioning:                                    │ │
│  │    • v2.1 (new) vs v2.0 (current)                      │ │
│  │    • Tag in Git: model-v2.1                            │ │
│  │    • Upload to model registry                           │ │
│  └──────────────┬───────────────────────────────────────────┘ │
│                 │                                              │
│                 ▼                                              │
│  ┌──────────────────────────────────────────┐                 │
│  │ MLOps Dashboard                          │                 │
│  │                                          │                 │
│  │ Engineers review:                       │                 │
│  │ • Accuracy: 94.2% (+2% from v2.0)       │                 │
│  │ • FPR: 3.5% (-1% from v2.0)             │                 │
│  │ • Confusion matrix                       │                 │
│  │ • Training curves                        │                 │
│  │                                          │                 │
│  │ Decision:                                │                 │
│  │ ✓ Deploy to pilot (5 devices)           │                 │
│  │ Wait 1 week                              │                 │
│  │ ✓ Deploy to all devices (50+)           │                 │
│  └──────────────┬───────────────────────────┘                 │
│                 │                                              │
│                 ▼                                              │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Kubernetes Deployment (Edge Model Update)               │ │
│  │                                                          │ │
│  │ kubectl apply -f model-deployment-v2.1.yaml             │ │
│  │                                                          │ │
│  │ Rolling update to all Jetson devices:                   │ │
│  │ • Download model-v2.1.trt                               │ │
│  │ • Swap atomically (zero downtime)                       │ │
│  │ • Monitor for errors (rollback if needed)               │ │
│  └──────────────┬───────────────────────────────────────────┘ │
│                 │                                              │
│                 ▼ Model deployed to edge                      │
└─────────────────┼───────────────────────────────────────────────┘
                  │
                  ▼ (Loop back to top - edge devices now use v2.1)
```

---

## 🧠 Industrial RAG: What It Actually Does

**IMPORTANT**: Industrial RAG is **NOT** for training ML models!

### What Industrial RAG Does:
```python
# When QR code "QM-BATCH-12345" is scanned:

# 1. Fast lookup in Redis (sub-millisecond)
context = redis.get("context:QM-BATCH-12345")
# Returns:
{
  "product": "Motor Assembly Type A",
  "batch": "BATCH-12345",
  "recipe_id": "RECIPE-001",
  "expected_runtime": 3600,  # seconds
  "thresholds": {
    "temp_warning": 80,
    "temp_critical": 90,
    "vibration_max": 2.0
  }
}

# 2. Augment sensor data with this context
sensor_data = {
  "temp": 82,
  "vibration_x": 1.8,
  "vibration_y": 1.2,
  "current": 12.5
}

# 3. Feed BOTH to AI model
model_input = concat(sensor_data, context)
# [82, 1.8, 1.2, 12.5, product_id=5, recipe_id=1, ...]

# 4. AI model uses context to make BETTER predictions
prediction = model.predict(model_input)
# "Bearing Wear" with 87% confidence
```

### Why Context Improves AI:

**Without Context:**
```
Input:  [temp=82, vib=1.8]
Model:  "Normal" (60% confidence) ← Wrong! Doesn't know this product
                                     normally runs cooler
```

**With Context (Industrial RAG):**
```
Input:  [temp=82, vib=1.8, product=TypeA, normal_temp=75]
Model:  "Bearing Wear" (87% confidence) ← Correct! Knows 82°C is
                                           abnormal for Type A
```

### RAG vs Traditional Retrieval:

| Traditional RAG (LLMs) | Industrial RAG (Context Edge) |
|------------------------|-------------------------------|
| Retrieves text documents | Retrieves structured metadata |
| Augments prompt to LLM | Augments sensor data to ML model |
| Semantic search (embeddings) | Direct key-value lookup (Redis) |
| Latency: 100-500ms | Latency: <10ms |
| Use case: ChatGPT with docs | Use case: Real-time inference |

---

## 📊 Model Training: Step-by-Step

### Phase 1: Data Collection (Continuous)

Every production run generates LDOs:

```python
# Edge device generates LDO
ldo = {
  "ldo_id": "LDO-2025-001",
  "timestamp": 1700000000,
  "sensor_data": {
    "vibration_x": 1.8,
    "vibration_y": 1.2,
    "temperature": 82,
    "current": 12.5
  },
  "context": {
    "product": "Motor Assembly Type A",
    "batch": "BATCH-12345",
    "recipe_id": "RECIPE-001"
  },
  "ground_truth_label": "Bearing Wear",  # ← From QR code context!
  "video_clip": "s3://ldos/2025/001.mp4",
  "ai_prediction": "Bearing Wear",
  "ai_confidence": 0.87
}

# Upload to S3/MinIO
upload_to_storage(ldo)
```

**Key Point**: The label is **100% accurate** because it comes from the QR code metadata, not human annotation!

### Phase 2: Feedback Loop (Weekly)

```python
# Engineers validate low-confidence predictions
feedback_queue = get_ldos_where(confidence < 0.6)

for ldo in feedback_queue:
  # Engineer reviews:
  # - Sensor data: temp=82, vib=1.8
  # - AI said: "Bearing Wear" (55% confidence)
  # - Video shows: Belt was actually loose

  # Engineer corrects:
  ldo["ground_truth_label"] = "Belt Slippage"  # ← Correction
  ldo["validated_by"] = "engineer@company.com"
  ldo["notes"] = "Belt tension was 20% below spec"

  save_validated_ldo(ldo)

# When 1000+ corrections accumulate → trigger retraining
```

### Phase 3: Model Retraining (Monthly)

```python
# GitHub Actions workflow: .github/workflows/mlops.yml

# 1. Prepare dataset
ldos = fetch_from_s3(
  where="validated=true AND created_at > last_training_date",
  limit=100000
)

X_train = []
y_train = []
for ldo in ldos:
  # Features: sensor data + context embeddings
  features = [
    ldo["sensor_data"]["vibration_x"],
    ldo["sensor_data"]["vibration_y"],
    ldo["sensor_data"]["temperature"],
    ldo["sensor_data"]["current"],
    embed(ldo["context"]["product"]),      # Product type embedding
    embed(ldo["context"]["recipe_id"]),    # Recipe embedding
    # ... more context features
  ]
  X_train.append(features)

  # Label: ground truth (100% accurate!)
  y_train.append(ldo["ground_truth_label"])

# 2. Train PyTorch model
model = ResNet50(num_classes=5)  # [normal, bearing, belt, motor, other]
optimizer = AdamW(model.parameters(), lr=1e-4)
criterion = CrossEntropyLoss()

for epoch in range(50):
  for batch in DataLoader(X_train, y_train, batch_size=64):
    optimizer.zero_grad()
    predictions = model(batch.X)
    loss = criterion(predictions, batch.y)
    loss.backward()
    optimizer.step()

  # Validate on holdout set
  accuracy = validate(model, X_val, y_val)
  if accuracy > 0.92:
    break  # Early stopping

# 3. Convert to TensorRT for Jetson
torch.save(model.state_dict(), "model-v2.1.pth")
convert_to_tensorrt("model-v2.1.pth", "model-v2.1.trt")

# 4. Deploy to model registry
upload_to_registry("model-v2.1.trt", metadata={
  "version": "2.1",
  "accuracy": 0.942,
  "fpr": 0.035,
  "training_date": "2025-01-15"
})
```

### Phase 4: Gradual Deployment

```bash
# Week 1: Deploy to 5 pilot devices
kubectl set image deployment/edge-device \
  model=registry.company.com/models:v2.1 \
  --selector=pilot=true

# Monitor for 1 week:
# - Accuracy holding at 94%?
# - No crashes?
# - Latency <100ms?

# Week 2: Deploy to all 50 devices
kubectl set image deployment/edge-device \
  model=registry.company.com/models:v2.1

# Automatic rollback if FPR > 10%
```

---

## 🔄 The Complete Feedback Loop

```
1. Production Run
   ↓
   QR scan → Context RAG → Sensor fusion → AI inference
   ↓
2. LDO Generated (100% labeled)
   ↓
   Upload to S3
   ↓
3. Feedback Queue
   ↓
   IF confidence < 60%:
     → Engineer validates
     → Corrects label if wrong
   ↓
4. Accumulate Corrections
   ↓
   When N > 1000:
     → Trigger GitHub Actions workflow
   ↓
5. Model Retraining
   ↓
   PyTorch training on 4x A100 GPUs (6-8 hours)
   ↓
6. TensorRT Optimization
   ↓
   Convert for Jetson deployment
   ↓
7. MLOps Review
   ↓
   Engineer approves if accuracy > 92%
   ↓
8. Kubernetes Deployment
   ↓
   Rolling update to Jetson devices
   ↓
9. Back to Step 1 (with improved model!)
```

**Timeline:**
- **Real-time inference**: <100ms per prediction
- **LDO generation**: Continuous (every production run)
- **Feedback review**: Weekly batch
- **Model retraining**: Monthly (or when 1000+ corrections)
- **Deployment**: 1-2 weeks (pilot → full rollout)

---

## 🎯 Key Differences from Traditional ML

### Traditional Approach:

```
1. Collect raw data (weeks)
   ↓
2. Manually label data (weeks, $50K)
   ↓
3. Train model (days)
   ↓
4. Deploy to production
   ↓
5. Model never improves (static)
```

### Context Edge Approach:

```
1. Production runs generate labeled data automatically (day 1)
   ↓
2. No manual labeling needed (100% accurate from QR codes)
   ↓
3. Continuous improvement via feedback loop
   ↓
4. Models retrain monthly with fresh data
   ↓
5. Edge inference uses latest model (<100ms)
```

---

## 💡 Why This Architecture Works

### 1. **Separation of Concerns**
- **Edge**: Fast inference, low latency, no training
- **Cloud**: Slow training, high compute, no latency requirement

### 2. **100% Accurate Labels**
- QR codes provide ground truth
- No human error in labeling
- Perfect training data from day 1

### 3. **Continuous Improvement**
- Models get better over time
- Feedback loop catches edge cases
- New products/failures automatically incorporated

### 4. **Industrial RAG**
- Context makes predictions more accurate
- No need to train model on every product variant
- Metadata changes don't require retraining

### 5. **Zero Downtime**
- Rolling updates to edge devices
- Automatic rollback on failures
- A/B testing built-in

---

## 📈 Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| **Inference Latency** | <100ms | Edge (TensorRT on Jetson) |
| **Context Retrieval** | <10ms | Redis lookup |
| **Training Duration** | 6-8 hours | 4x A100 GPUs, 100K samples |
| **Model Update Frequency** | Monthly | Or when 1000+ corrections |
| **Labeling Accuracy** | 100% | QR code ground truth |
| **Model Accuracy** | 92-95% | Validated on holdout set |
| **False Positive Rate** | 3-5% | Monitored, triggers retraining if >10% |

---

## 🔬 Advanced: Model Architecture Details

### Input Layer:
```python
# Sensor data (4 features)
sensor_features = [vibration_x, vibration_y, temperature, current]

# Context embeddings (learned during training)
product_embedding = embed_product(product_id)  # 16-dim vector
recipe_embedding = embed_recipe(recipe_id)     # 16-dim vector
asset_embedding = embed_asset(asset_id)        # 16-dim vector

# Combine
input_vector = concat([
  sensor_features,      # 4 dims
  product_embedding,    # 16 dims
  recipe_embedding,     # 16 dims
  asset_embedding       # 16 dims
])  # Total: 52 dims
```

### Model Architecture:
```python
model = Sequential([
  Dense(128, activation='relu'),
  Dropout(0.3),
  Dense(64, activation='relu'),
  Dropout(0.2),
  Dense(32, activation='relu'),
  Dense(5, activation='softmax')  # 5 failure modes
])
```

### Output:
```python
# Softmax probabilities
output = [
  0.05,  # Normal
  0.87,  # Bearing Wear    ← Highest
  0.03,  # Belt Slippage
  0.04,  # Motor Overload
  0.01   # Other
]

# Prediction: "Bearing Wear" with 87% confidence
```

---

## 🚀 Future Enhancements

### 1. **Online Learning** (Experimental)
```python
# Update model weights incrementally on edge device
# (without full retraining)
model.partial_fit(X_new, y_new)
```

### 2. **Federated Learning**
```python
# Each edge device trains on local data
# Aggregate gradients centrally
# No raw data leaves the edge
```

### 3. **Active Learning**
```python
# Model requests labels for most uncertain examples
# Engineer validates only high-value cases
# Reduces feedback queue by 80%
```

### 4. **Multi-Modal Fusion**
```python
# Combine sensor data + video + audio
# LSTM for temporal patterns
# Vision model for visual defects
```

---

## Summary

**Real-time inference happens at the edge:**
- Industrial RAG retrieves context (<10ms)
- AI model predicts failures (<100ms)
- TensorRT-optimized for Jetson

**Model training happens in the cloud:**
- LDOs provide 100% accurate labels
- Feedback loop corrects low-confidence cases
- PyTorch training on GPUs (monthly)
- TensorRT conversion for edge deployment

**The system gets smarter over time:**
- Every production run generates training data
- Engineers validate edge cases
- Models retrain automatically
- New failure modes incorporated

**Industrial RAG is the secret sauce:**
- Makes predictions context-aware
- Eliminates need to retrain for every product variant
- Sub-10ms latency for real-time inference

This architecture delivers **both** real-time performance **and** continuous improvement!

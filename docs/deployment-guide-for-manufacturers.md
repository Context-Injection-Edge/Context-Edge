# Deployment Guide for Manufacturers
**Context Edge Platform - Model Deployment Options**

---

## 📋 **Table of Contents**

1. [Choose Your Deployment Method](#choose-your-deployment-method)
2. [Option 1: Manual Deployment (Small Sites)](#option-1-manual-deployment-1-10-devices)
3. [Option 2: Script-Based Deployment (Medium Sites)](#option-2-script-based-deployment-10-50-devices)
4. [Option 3: K3s Automated Deployment (Large Sites)](#option-3-k3s-automated-deployment-50-devices)
5. [Industry-Specific Examples](#industry-specific-examples)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 **Choose Your Deployment Method**

The Context Edge platform supports **three deployment methods** depending on your factory size:

| Deployment Size | Recommended Method | Setup Time | Skills Required |
|----------------|-------------------|------------|-----------------|
| **1-10 devices** | Manual SSH deployment | 15 minutes | Basic Linux/SSH |
| **10-50 devices** | Automated bash script | 30 minutes | Basic Linux/SSH |
| **50-500+ devices** | K3s orchestration | 2-4 hours | Kubernetes basics |

**All methods work with Docker OR Podman** - choose what your IT team prefers!

---

## **Option 1: Manual Deployment** (1-10 devices)

### **Best For:**
- ✅ Small factories (1-2 production lines)
- ✅ Pilot testing
- ✅ Proof-of-concept
- ✅ Development/demo

### **What You Need:**
- SSH access to edge devices
- Model file (`.trt` file from training)
- 5 minutes per device

### **Step-by-Step:**

#### **1. Get the Trained Model**

After training completes, you'll have a file like `model-v2.1.trt`

```bash
# Model is in ml-training/models/ after training
ls ml-training/models/
# Output: model-v2.1.trt
```

#### **2. Deploy to First Device (Pilot)**

```bash
# Copy model to edge device
scp ml-training/models/model-v2.1.trt nvidia@edge-001:/tmp/

# SSH to edge device
ssh nvidia@edge-001

# On the edge device:
# Backup current model
sudo cp /opt/context-edge/models/current.trt \
        /opt/context-edge/models/current.trt.backup

# Install new model
sudo mv /tmp/model-v2.1.trt /opt/context-edge/models/
sudo chmod 644 /opt/context-edge/models/model-v2.1.trt

# Activate new model
sudo rm -f /opt/context-edge/models/current.trt
sudo ln -s /opt/context-edge/models/model-v2.1.trt \
            /opt/context-edge/models/current.trt

# Restart inference service
sudo systemctl restart context-edge-inference

# Check if service started
sudo systemctl status context-edge-inference
# Should show "active (running)"

# Exit edge device
exit
```

#### **3. Test the Deployment**

Monitor the pilot device for 24 hours:

```bash
# Check logs
ssh nvidia@edge-001 "journalctl -u context-edge-inference -f"

# Should see:
# "Model v2.1 loaded successfully"
# "Inference time: 87ms"
# "Prediction: normal (confidence: 0.98)"
```

#### **4. Deploy to Remaining Devices**

Repeat step 2 for each device (edge-002, edge-003, etc.)

---

## **Option 2: Script-Based Deployment** (10-50 devices)

### **Best For:**
- ✅ Medium factories (3-10 production lines)
- ✅ Multi-site pilots
- ✅ Want automation without K3s complexity

### **What You Need:**
- SSH access to all edge devices
- Bash script (provided)
- 10-15 minutes total deployment time

### **Step-by-Step:**

#### **1. Configure Device List**

Edit `ml-training/deploy-model.sh`:

```bash
# Open the script
nano ml-training/deploy-model.sh

# Edit these arrays (lines 20-40):
PILOT_DEVICES=(
  "edge-001"  # Production Line 1
  "edge-002"  # Production Line 2
  "edge-003"  # Production Line 3
  "edge-004"  # Packaging
  "edge-005"  # Quality Control
)

ALL_DEVICES=(
  "edge-001"
  "edge-002"
  "edge-003"
  "edge-004"
  "edge-005"
  "edge-006"
  "edge-007"
  "edge-008"
  "edge-009"
  "edge-010"
  # Add your devices here...
)

# Save and exit (Ctrl+X, Y, Enter)
```

#### **2. Deploy to Pilot Devices (5 devices)**

```bash
cd ml-training/

# Deploy to pilot devices
./deploy-model.sh v2.1 --pilot

# Output:
# ════════════════════════════════════════════
#  Context Edge - Model Deployment
# ════════════════════════════════════════════
#
#  Model Version: v2.1
#  Mode: --pilot
#  Target: 5 pilot devices
#
# Continue? (y/n) y
#
# 📥 Downloading model v2.1 from S3...
# ✅ Model downloaded
#
# 📦 Deploying to edge-001...
#    - Copying model file...
#    - Installing model...
#    - Restarting inference service...
# ✅ edge-001 deployed successfully
#
# 📦 Deploying to edge-002...
# ✅ edge-002 deployed successfully
#
# ... (repeats for all pilot devices)
#
# ════════════════════════════════════════════
#  Deployment Complete!
# ════════════════════════════════════════════
#
#  Success: 5/5 devices
#  Failed: 0/5 devices
#
# ✅ All devices deployed successfully!
```

#### **3. Monitor Pilot Devices (24-48 hours)**

```bash
# Check all pilot devices
for device in edge-001 edge-002 edge-003 edge-004 edge-005; do
  echo "Checking $device..."
  ssh nvidia@$device "systemctl status context-edge-inference | grep Active"
done

# All should show: Active: active (running)
```

#### **4. Deploy to All Devices**

If pilot looks good:

```bash
# Deploy to all 10+ devices
./deploy-model.sh v2.1 --all

# Deploys to all devices in ALL_DEVICES array
```

#### **5. Rollback (If Needed)**

If something goes wrong:

```bash
# Rollback all devices to previous version
./deploy-model.sh v2.0 --rollback

# Uses the .backup files created during deployment
```

---

## **Option 3: K3s Automated Deployment** (50+ devices)

### **Best For:**
- ✅ Large factories (10+ production lines)
- ✅ Multi-site deployments
- ✅ Want full automation
- ✅ Cloud-native teams

### **What You Need:**
- K3s installed (one-time setup)
- kubectl CLI tool
- 2-4 hours for initial setup
- Basic Kubernetes knowledge

### **One-Time Setup (Do This Once)**

#### **1. Install K3s on Factory Server**

```bash
# On factory server
curl -sfL https://get.k3s.io | sh -

# Verify installation
sudo kubectl get nodes
# Should show your server as "Ready"
```

#### **2. Register Edge Devices as K3s Nodes**

On EACH edge device (one-time setup):

```bash
# Get K3s token from factory server
ssh factory-server "sudo cat /var/lib/rancher/k3s/server/node-token"
# Copy the token

# On edge device:
curl -sfL https://get.k3s.io | K3S_URL=https://factory-server:6443 \
  K3S_TOKEN=<paste-token-here> sh -

# Verify on factory server:
sudo kubectl get nodes
# Should show edge-001, edge-002, etc.
```

#### **3. Label Pilot Devices**

```bash
# Label 5 devices for pilot testing
kubectl label node edge-001 pilot=true
kubectl label node edge-002 pilot=true
kubectl label node edge-003 pilot=true
kubectl label node edge-004 pilot=true
kubectl label node edge-005 pilot=true
```

#### **4. Create Namespace**

```bash
kubectl create namespace context-edge
```

### **Deploy Models with K3s**

#### **1. Deploy to Pilot (5 devices)**

```bash
# Edit pilot config
nano k8s/model-updater-pilot.yaml
# Change line: version: "v2.1"  # Set your model version

# Deploy
kubectl apply -f k8s/model-updater-pilot.yaml

# Check deployment status
kubectl get pods -n context-edge
# Should show 5 pods (one per pilot device)

# Watch deployment
kubectl logs -n context-edge -l app=model-updater-pilot -f

# Output:
# 📥 [PILOT] Downloading model v2.1 from S3...
# ✅ Download complete
# 📦 [PILOT] Installing model v2.1...
# ✅ [PILOT] Model v2.1 deployed successfully
```

#### **2. Monitor Pilot (24-48 hours)**

```bash
# Check all pilot pods
kubectl get pods -n context-edge -l deployment=pilot

# Check logs
kubectl logs -n context-edge -l deployment=pilot --tail=100
```

#### **3. Deploy to All Devices (50+)**

If pilot succeeds:

```bash
# Deploy to ALL devices
kubectl apply -f k8s/model-updater-daemonset.yaml

# This automatically deploys to all 50+ devices in parallel!

# Watch deployment
kubectl get daemonset -n context-edge
# NAME             DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE
# model-updater    50        50        50      50           50
```

#### **4. Rollback (If Needed)**

```bash
# Delete current deployment
kubectl delete -f k8s/model-updater-daemonset.yaml

# Deploy previous version
# (edit version in ConfigMap first)
kubectl apply -f k8s/model-updater-daemonset.yaml
```

---

## 🏭 **Industry-Specific Examples**

### **Automotive Supplier (50+ devices)**

```
Factory Layout:
- 12 CNC machines (edge-001 to edge-012)
- 8 Assembly lines (edge-013 to edge-020)
- 6 Quality control stations (edge-021 to edge-026)
- 4 Packaging lines (edge-027 to edge-030)
- Total: 30 devices

Recommendation: Option 2 (Script-based)
Deployment time: 10 minutes
```

```bash
# Deploy to all 30 devices
./deploy-model.sh v2.1 --all
```

---

### **Pharmaceutical Company (100+ devices)**

```
Multi-Site Deployment:
- Site A (Boston): 40 devices
- Site B (Chicago): 35 devices
- Site C (Austin): 25 devices
- Total: 100 devices

Recommendation: Option 3 (K3s)
Deployment time: 5 minutes (automated)
```

```bash
# K3s deploys to all 100 devices automatically
kubectl apply -f k8s/model-updater-daemonset.yaml
```

---

### **Food Processing Plant (5 devices)**

```
Small Facility:
- 2 Conveyor belts (edge-001, edge-002)
- 1 Packaging line (edge-003)
- 1 Freezer (edge-004)
- 1 Quality control (edge-005)
- Total: 5 devices

Recommendation: Option 1 (Manual) or Option 2 (Script)
Deployment time: 5 minutes
```

```bash
# Simple script deployment
./deploy-model.sh v2.1 --pilot  # All 5 devices are "pilot"
```

---

## 🔧 **Troubleshooting**

### **Problem: SSH Connection Failed**

```bash
# Error: ssh: connect to host edge-001 port 22: Connection refused

# Solution: Check network connectivity
ping edge-001

# Check SSH is running on edge device
ssh nvidia@edge-001
# If password doesn't work, set up SSH keys
```

### **Problem: Service Failed to Start**

```bash
# Check service status
ssh nvidia@edge-001 "systemctl status context-edge-inference"

# Check logs
ssh nvidia@edge-001 "journalctl -u context-edge-inference -n 50"

# Common issues:
# 1. Model file corrupted - re-download
# 2. GPU not available - check nvidia-smi
# 3. Permissions - check file ownership
```

### **Problem: K3s Deployment Stuck**

```bash
# Check pod status
kubectl get pods -n context-edge

# Check pod logs
kubectl logs -n context-edge <pod-name>

# Describe pod for events
kubectl describe pod -n context-edge <pod-name>

# Common issues:
# 1. S3 credentials wrong - check Secret
# 2. Model not in S3 - verify upload
# 3. Node not ready - check kubectl get nodes
```

---

## 📞 **Support**

For deployment assistance:
- **Documentation**: [/docs](../docs/)
- **Issues**: [GitHub Issues](https://github.com/Context-Injection-Edge/Context-Edge/issues)
- **Email**: support@admoose.pro

---

**Built for manufacturing excellence** 🏭

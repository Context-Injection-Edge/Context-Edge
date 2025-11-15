# Kubernetes Manifests
**For K3s and Full Kubernetes**

---

## 🎯 **What's in This Folder?**

Kubernetes manifests for automated model deployment to edge devices.

**These manifests work with:**
- ✅ **K3s** (recommended for edge/industrial)
- ✅ **K8s** (full Kubernetes)
- ✅ **K0s, MicroK8s, etc.** (any Kubernetes distribution)

---

## 📁 **Files**

| File | Purpose | When to Use |
|------|---------|-------------|
| `model-updater-daemonset.yaml` | Deploy to ALL edge devices | Production (50-500+ devices) |
| `model-updater-pilot.yaml` | Deploy to PILOT devices only | Testing new models (5 devices) |

---

## 🚀 **Quick Start**

### **For K3s Users (Recommended)**

```bash
# 1. Install K3s on factory server (one-time setup)
curl -sfL https://get.k3s.io | sh -

# 2. Create namespace
kubectl create namespace context-edge

# 3. Deploy to pilot devices
kubectl apply -f model-updater-pilot.yaml

# 4. Monitor pilot
kubectl get pods -n context-edge

# 5. If successful, deploy to all
kubectl apply -f model-updater-daemonset.yaml
```

### **For Full K8s Users**

```bash
# Same commands work!
kubectl create namespace context-edge
kubectl apply -f model-updater-daemonset.yaml
```

---

## 🔧 **Why K3s?**

If you're unsure whether to use K3s or full K8s, here's our recommendation:

| Use K3s When... | Use Full K8s When... |
|----------------|---------------------|
| Factory/edge deployment | Cloud deployment |
| 50-500 devices | 1000+ devices |
| Resource-constrained servers | Dedicated K8s clusters |
| OT (Operational Technology) | IT infrastructure |
| Want lightweight, simple | Already have K8s expertise |

**For most manufacturers: Use K3s!**

---

## 📖 **Documentation**

- **Deployment Guide**: [docs/deployment-guide-for-manufacturers.md](../docs/deployment-guide-for-manufacturers.md)
- **MLOps Workflow**: [docs/mlops-workflow-guide.md](../docs/mlops-workflow-guide.md)
- **K3s Official Docs**: https://k3s.io/

---

## ❓ **FAQ**

### **Q: Why is the folder named `k8s/` if we recommend K3s?**
**A:** K3s uses the exact same manifest format as Kubernetes. The `k8s/` naming is the industry standard for Kubernetes manifests, regardless of which distribution you use.

### **Q: Will these work with my K3s cluster?**
**A:** Yes! These manifests are tested and work perfectly with K3s.

### **Q: Can I use these without K3s?**
**A:** Yes, but for 1-50 devices, we recommend simpler deployment methods (see [deployment guide](../docs/deployment-guide-for-manufacturers.md)).

### **Q: What if I want to use full K8s instead of K3s?**
**A:** No problem! These manifests work identically on K8s and K3s.

---

**Built for manufacturing excellence** 🏭

# Context Edge Deployment Progression Guide

**From Engineer's Laptop to Production Factory**

This guide walks through the three-stage deployment progression for Context Edge, from local development to full production deployment.

---

## Table of Contents

1. [Stage 1: Development (Engineer's Laptop)](#stage-1-development-engineers-laptop)
2. [Stage 2: Factory Pilot (Single Server)](#stage-2-factory-pilot-single-server)
3. [Stage 3: Production (Kubernetes Cluster + Edge Devices)](#stage-3-production-kubernetes-cluster--edge-devices)
4. [Network Architecture Comparison](#network-architecture-comparison)
5. [Security Considerations](#security-considerations)
6. [Troubleshooting](#troubleshooting)

---

## Stage 1: Development (Engineer's Laptop)

**Status: ✅ Currently Running**

### Architecture

```
┌──────────────────────────────────────────────────────┐
│  LAPTOP (localhost)                                  │
│                                                      │
│  Frontend (Port 3000)                                │
│  └─ Next.js Dev Server                              │
│  └─ React UI with Admin Dashboards                  │
│                                                      │
│  Backend (Podman Containers)                         │
│  ├─ context-service:8000      (FastAPI)             │
│  ├─ data-ingestion:8001       (FastAPI)             │
│  ├─ postgres:5432             (PostgreSQL 15)        │
│  └─ redis:6379                (Redis 7)              │
│                                                      │
│  No Edge Devices (using mock data)                   │
└──────────────────────────────────────────────────────┘
```

### What's Running Now

```bash
# Check current services
podman ps

# Expected output:
# context-edge_postgres_1         (healthy)
# context-edge_redis_1            (up)
# context-edge_context-service_1  (up)
# context-edge_data-ingestion_1   (up)

# Check UI server
ps aux | grep "next dev"
# Should show: node .../next dev on port 3000
```

### Access Points

- **UI Dashboard**: http://localhost:3000
- **Admin Panel**: http://localhost:3000/admin
- **Context Service API**: http://localhost:8000/docs
- **Data Ingestion API**: http://localhost:8001/docs
- **PostgreSQL**: localhost:5432 (user: contextedge, db: contextedge)
- **Redis**: localhost:6379

### Starting/Stopping

```bash
# Start backend services
cd /home/jeff/projects/OT\ Injection/context-edge
podman-compose up -d

# Start UI (in separate terminal)
cd ui/
npm run dev

# Stop everything
podman-compose down
pkill -f "next dev"
```

### Best For

- ✅ **Rapid development** - Hot reload, instant feedback
- ✅ **Code testing** - Full stack on one machine
- ✅ **Demos** - Take laptop to factory floor
- ✅ **Training** - New engineers learn the platform
- ✅ **API development** - Test endpoints locally
- ❌ **Production data** - Not connected to real PLCs
- ❌ **Scale testing** - Single machine limitations
- ❌ **24/7 operation** - Laptop sleeps/shuts down

---

## Stage 2: Factory Pilot (Single Server)

**Deploy Context Edge to a dedicated server in the factory for pilot testing**

### Architecture

```
┌────────────────────────────────────────────────┐
│  FACTORY SERVER (192.168.1.100)               │
│                                                │
│  Frontend (Port 80/443)                        │
│  └─ Next.js Production Build (nginx)          │
│                                                │
│  Backend (Docker/Podman)                       │
│  ├─ context-service:8000                       │
│  ├─ data-ingestion:8001                        │
│  ├─ postgres:5432 (persistent volume)          │
│  └─ redis:6379                                 │
└────────────────────────────────────────────────┘
          ↑                    ↑
          │                    │
    ┌─────────────┐      ┌─────────────┐
    │  EDGE-001   │      │  EDGE-002   │
    │  (Jetson)   │      │  (Jetson)   │
    │             │      │             │
    │  Modbus TCP │      │  OPC UA     │
    │     ↓       │      │     ↓       │
    │   PLC-A     │      │   PLC-B     │
    └─────────────┘      └─────────────┘
```

### Hardware Requirements

**Factory Server:**
- **CPU**: 4+ cores (8 recommended)
- **RAM**: 16GB minimum, 32GB recommended
- **Storage**: 500GB SSD (for database, time-series data)
- **Network**: Gigabit Ethernet, static IP on factory network
- **OS**: Ubuntu 22.04 LTS, Rocky Linux 9, or RHEL 9

**Edge Devices (NVIDIA Jetson):**
- Jetson Orin Nano (8GB) or higher
- 128GB+ SD card or NVMe
- Ethernet connection to factory network
- Access to PLC network (Modbus TCP / OPC UA)

### Deployment Steps

#### 1. Prepare Factory Server

```bash
# SSH into factory server
ssh admin@192.168.1.100

# Install Docker/Podman
sudo apt update
sudo apt install -y podman podman-compose git

# Clone repository
git clone https://github.com/Context-Injection-Edge/Context-Edge.git
cd Context-Edge

# Set environment variables
cat > .env <<EOF
POSTGRES_USER=contextedge
POSTGRES_PASSWORD=CHANGE_THIS_PASSWORD
POSTGRES_DB=contextedge
REDIS_PASSWORD=CHANGE_THIS_PASSWORD
NEXT_PUBLIC_API_BASE=http://192.168.1.100:8000
EOF

# Create persistent volumes
mkdir -p /data/context-edge/{postgres,redis,storage}

# Update docker-compose.yml with volume mounts
```

#### 2. Build Production UI

```bash
# On factory server
cd ui/

# Install dependencies
npm install

# Build production bundle
npm run build

# Install nginx for serving
sudo apt install -y nginx

# Configure nginx
sudo tee /etc/nginx/sites-available/context-edge <<EOF
server {
    listen 80;
    server_name 192.168.1.100;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/context-edge /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Start Next.js in production mode
npm run start
```

#### 3. Start Backend Services

```bash
cd /path/to/Context-Edge

# Start all services
podman-compose up -d

# Verify services are running
podman ps
curl http://localhost:8000/health
```

#### 4. Deploy Edge Devices

```bash
# On each Jetson device
cd /opt
sudo git clone https://github.com/Context-Injection-Edge/Context-Edge.git
cd Context-Edge/edge-device

# Install dependencies
sudo ./install.sh

# Configure edge device
sudo tee /etc/context-edge/config.yaml <<EOF
context_service_url: http://192.168.1.100:8000
data_ingestion_url: http://192.168.1.100:8001
redis_host: 192.168.1.100
redis_port: 6379
device_id: edge-001
protocols:
  - type: modbus_tcp
    host: 192.168.1.50
    port: 502
    tags:
      - address: 40001
        name: temperature
        scale: 0.1
      - address: 40002
        name: vibration_x
EOF

# Start edge service
sudo systemctl enable context-edge
sudo systemctl start context-edge

# Verify edge device is sending data
journalctl -u context-edge -f
```

#### 5. Test End-to-End Flow

```bash
# 1. Scan QR code on factory floor (or inject test metadata)
curl -X POST http://192.168.1.100:8000/context \
  -H "Content-Type: application/json" \
  -d '{
    "cid": "QM-BATCH-001",
    "metadata": {
      "product": "Widget A",
      "batch": "BATCH-12345",
      "start_time": 1700000000
    }
  }'

# 2. Check edge device is reading PLC data
curl http://192.168.1.100:8001/health

# 3. Verify LDOs are being created
curl http://192.168.1.100:8001/storage/recent

# 4. View in UI dashboard
# Navigate to: http://192.168.1.100/admin/mer-reports
```

### Best For

- ✅ **Pilot deployment** - Test with 2-5 production lines
- ✅ **Real sensor data** - Connected to actual PLCs
- ✅ **User acceptance testing** - Engineers validate features
- ✅ **ROI measurement** - Track actual production metrics
- ✅ **Training** - Operators learn on real system
- ❌ **High availability** - Single point of failure
- ❌ **Multi-site** - Limited to one factory
- ❌ **Scaling** - Capacity constraints on single server

---

## Stage 3: Production (Kubernetes Cluster + Edge Devices)

**Full production deployment with high availability, multi-site support, and enterprise features**

### Architecture

```
┌────────────────────────────────────────────────────────────┐
│  KUBERNETES CLUSTER (k8s.factory.local)                    │
│                                                            │
│  ┌──────────────────────────────────────────────────┐     │
│  │  INGRESS (Load Balancer)                         │     │
│  │  └─ context-edge.factory.local                   │     │
│  └──────────────────────────────────────────────────┘     │
│                     ↓                                      │
│  ┌──────────────────────────────────────────────────┐     │
│  │  FRONTEND POD (3 replicas)                       │     │
│  │  └─ Next.js Production                           │     │
│  └──────────────────────────────────────────────────┘     │
│                     ↓                                      │
│  ┌──────────────────────────────────────────────────┐     │
│  │  BACKEND PODS                                    │     │
│  │  ├─ context-service (3 replicas)                 │     │
│  │  └─ data-ingestion (3 replicas)                  │     │
│  └──────────────────────────────────────────────────┘     │
│                     ↓                                      │
│  ┌──────────────────────────────────────────────────┐     │
│  │  DATA LAYER                                      │     │
│  │  ├─ PostgreSQL (StatefulSet, 3 replicas)         │     │
│  │  └─ Redis Cluster (6 nodes)                      │     │
│  └──────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────┘
          ↑                    ↑                    ↑
          │                    │                    │
    ┌─────────────┐      ┌─────────────┐     ┌─────────────┐
    │  Factory A  │      │  Factory B  │     │  Factory C  │
    │  10 Edges   │      │  15 Edges   │     │   8 Edges   │
    └─────────────┘      └─────────────┘     └─────────────┘
```

### Infrastructure Requirements

**Kubernetes Cluster:**
- **Control Plane**: 3 nodes (4 CPU, 16GB RAM each)
- **Worker Nodes**: 5+ nodes (8 CPU, 32GB RAM each)
- **Storage**: Ceph/Longhorn for persistent volumes (5TB+)
- **Network**: 10Gbps backbone, VLANs for separation
- **Load Balancer**: MetalLB, HAProxy, or cloud provider LB

**Edge Devices per Factory:**
- NVIDIA Jetson Orin devices (quantity varies by lines)
- Local gateway for edge clustering
- Redundant network paths to cluster

### Deployment Steps

#### 1. Prepare Kubernetes Cluster

```bash
# Using provided k8s manifests
cd k8s/

# Create namespace
kubectl apply -f namespace.yaml

# Deploy PostgreSQL StatefulSet
kubectl apply -f postgres-statefulset.yaml

# Deploy Redis Cluster
kubectl apply -f redis-deployment.yaml

# Deploy backend services
kubectl apply -f context-service-deployment.yaml
kubectl apply -f data-ingestion-deployment.yaml

# Verify all pods are running
kubectl get pods -n context-edge
```

#### 2. Configure Ingress

```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml

# Create ingress for Context Edge
cat > ingress.yaml <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: context-edge-ingress
  namespace: context-edge
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: context-edge.factory.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ui-service
            port:
              number: 3000
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: context-service
            port:
              number: 8000
  tls:
  - hosts:
    - context-edge.factory.local
    secretName: context-edge-tls
EOF

kubectl apply -f ingress.yaml
```

#### 3. Deploy UI Frontend

```bash
# Build and push Docker image
cd ui/
docker build -t your-registry.com/context-edge-ui:latest .
docker push your-registry.com/context-edge-ui:latest

# Create Deployment
cat > ui-deployment.yaml <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ui
  namespace: context-edge
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ui
  template:
    metadata:
      labels:
        app: ui
    spec:
      containers:
      - name: ui
        image: your-registry.com/context-edge-ui:latest
        ports:
        - containerPort: 3000
        env:
        - name: NEXT_PUBLIC_API_BASE
          value: "http://context-service:8000"
---
apiVersion: v1
kind: Service
metadata:
  name: ui-service
  namespace: context-edge
spec:
  selector:
    app: ui
  ports:
  - port: 3000
    targetPort: 3000
EOF

kubectl apply -f ui-deployment.yaml
```

#### 4. Configure Edge Device Fleet

```bash
# Use Ansible/Terraform for fleet management
# Example Ansible playbook:

cat > deploy-edges.yaml <<EOF
---
- hosts: edge_devices
  become: yes
  vars:
    context_service_url: "https://context-edge.factory.local/api"
    redis_host: "context-edge.factory.local"

  tasks:
    - name: Install Context Edge SDK
      pip:
        name: context-edge-sdk
        state: latest

    - name: Deploy configuration
      template:
        src: templates/config.yaml.j2
        dest: /etc/context-edge/config.yaml

    - name: Restart edge service
      systemd:
        name: context-edge
        state: restarted
        enabled: yes
EOF

ansible-playbook -i inventory/production deploy-edges.yaml
```

#### 5. Enable Monitoring & Observability

```bash
# Deploy Prometheus + Grafana
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace

# Import Context Edge dashboards
kubectl apply -f monitoring/grafana-dashboards.yaml

# Configure alerts
kubectl apply -f monitoring/prometheus-rules.yaml
```

#### 6. Implement Backup & Disaster Recovery

```bash
# PostgreSQL backups with pg_dump
cat > backup-cronjob.yaml <<EOF
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: context-edge
spec:
  schedule: "0 2 * * *"  # 2 AM daily
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15
            command:
            - /bin/sh
            - -c
            - |
              pg_dump -h postgres -U contextedge contextedge | gzip > /backup/contextedge-\$(date +%Y%m%d).sql.gz
              # Upload to S3/NFS/etc
            volumeMounts:
            - name: backup-volume
              mountPath: /backup
          volumes:
          - name: backup-volume
            persistentVolumeClaim:
              claimName: backup-pvc
          restartPolicy: OnFailure
EOF

kubectl apply -f backup-cronjob.yaml
```

### Production Features

- ✅ **High Availability** - Multi-replica deployments, auto-healing
- ✅ **Horizontal Scaling** - Auto-scale based on load
- ✅ **Multi-Site Support** - Edge devices across factories
- ✅ **Zero-Downtime Deployments** - Rolling updates
- ✅ **Disaster Recovery** - Automated backups, geo-replication
- ✅ **Security** - TLS/SSL, RBAC, network policies
- ✅ **Monitoring** - Prometheus metrics, Grafana dashboards
- ✅ **Logging** - Centralized logging with ELK/Loki
- ✅ **CI/CD Integration** - GitHub Actions automated deployments

---

## Network Architecture Comparison

### Development (Laptop)

```
All services: localhost (127.0.0.1)
No firewall needed
No SSL/TLS
Mock data
```

### Factory Pilot (Single Server)

```
Server: Static IP on factory network (e.g., 192.168.1.100)
Edge Devices: Same subnet (192.168.1.101-110)
PLCs: Accessible via Modbus/OPC UA (192.168.1.50-60)

Firewall Rules:
- Allow 80/443 from factory network
- Allow 8000/8001 from edge devices
- Allow 5432/6379 only from localhost
- Block external access
```

### Production (Kubernetes)

```
Kubernetes Cluster: Private subnet (10.0.0.0/16)
Edge Devices: VPN or private WAN (site-to-site VPN)
External Access: Load balancer with SSL termination

Network Policies:
- Ingress traffic only through load balancer
- Pod-to-pod communication restricted by namespace
- Database accessible only from backend pods
- Edge devices authenticate via mTLS certificates
```

---

## Security Considerations

### Development
- ❌ **No authentication** - Open access for testing
- ❌ **No encryption** - HTTP only
- ✅ **Isolated environment** - Localhost only

### Factory Pilot
- ✅ **Basic authentication** - Username/password for UI
- ⚠️ **HTTP with local firewall** - Internal network only
- ✅ **PostgreSQL password** - Database credentials
- ⚠️ **No audit logging** - Limited tracking

### Production
- ✅ **SSO/LDAP integration** - Active Directory auth
- ✅ **HTTPS/TLS everywhere** - End-to-end encryption
- ✅ **Role-based access control** - Operator/Engineer/Admin roles
- ✅ **API keys for edge devices** - mTLS certificates
- ✅ **Audit logging** - All actions tracked
- ✅ **Secrets management** - Kubernetes Secrets / Vault
- ✅ **Network segmentation** - VLANs, firewalls
- ✅ **Regular security updates** - Automated patching

---

## Migration Checklist

### From Laptop → Factory Pilot

- [ ] Provision factory server hardware
- [ ] Install OS and Docker/Podman
- [ ] Configure static IP and firewall
- [ ] Clone repository and configure `.env`
- [ ] Build production UI bundle
- [ ] Start backend services
- [ ] Configure edge devices (2-5 devices)
- [ ] Test with real PLC data
- [ ] Train operators on UI
- [ ] Document pilot results

**Timeline**: 1-2 weeks

### From Factory Pilot → Production

- [ ] Provision Kubernetes cluster
- [ ] Set up persistent storage (Ceph/Longhorn)
- [ ] Configure load balancer and DNS
- [ ] Deploy PostgreSQL StatefulSet
- [ ] Deploy Redis cluster
- [ ] Deploy backend services (3 replicas)
- [ ] Build and push Docker images to registry
- [ ] Deploy UI frontend (3 replicas)
- [ ] Configure ingress with SSL/TLS
- [ ] Migrate data from pilot PostgreSQL
- [ ] Deploy monitoring (Prometheus/Grafana)
- [ ] Set up backup/disaster recovery
- [ ] Configure CI/CD pipeline
- [ ] Deploy edge device fleet (Ansible)
- [ ] Load testing and performance tuning
- [ ] Security hardening and penetration testing
- [ ] Operator training on production system
- [ ] Go-live and cutover

**Timeline**: 4-8 weeks

---

## Troubleshooting

### Development Issues

**UI not loading:**
```bash
# Check if Next.js dev server is running
ps aux | grep "next dev"

# Restart UI
pkill -f "next dev"
cd ui/ && npm run dev
```

**Backend not responding:**
```bash
# Check container status
podman ps

# View logs
podman logs context-edge_context-service_1

# Restart services
podman-compose restart
```

### Factory Pilot Issues

**Edge device can't connect:**
```bash
# On edge device, check connectivity
ping 192.168.1.100
curl http://192.168.1.100:8000/health

# Check firewall
sudo firewall-cmd --list-all

# View edge device logs
journalctl -u context-edge -f
```

**Database connection errors:**
```bash
# Check PostgreSQL is running
podman exec -it context-edge_postgres_1 psql -U contextedge -d contextedge

# Verify credentials in .env file
cat .env
```

### Production Issues

**Pod crashes (CrashLoopBackOff):**
```bash
# Check pod logs
kubectl logs -n context-edge <pod-name>

# Describe pod for events
kubectl describe pod -n context-edge <pod-name>

# Check resource limits
kubectl top pods -n context-edge
```

**High latency from edge devices:**
```bash
# Check network latency
kubectl exec -it -n context-edge <backend-pod> -- ping <edge-ip>

# Check Redis connection pool
kubectl exec -it -n context-edge <redis-pod> -- redis-cli INFO clients

# Scale up backend replicas
kubectl scale deployment context-service -n context-edge --replicas=5
```

---

## Support & Next Steps

For further assistance:
- **Documentation**: `/docs` folder in repository
- **GitHub Issues**: https://github.com/Context-Injection-Edge/Context-Edge/issues
- **API Docs**: http://localhost:8000/docs (dev), https://context-edge.factory.local/api/docs (prod)

**Recommended Next Steps:**
1. ✅ Run on laptop (current stage)
2. Plan factory pilot deployment (identify 2-5 production lines)
3. Provision factory server hardware
4. Deploy pilot and measure ROI (4-8 weeks)
5. Plan production Kubernetes deployment based on pilot results
6. Scale to full production (multi-site, HA)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-15
**Author**: Context Edge Team

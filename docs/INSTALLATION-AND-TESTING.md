# Installation & Testing Guide
## Complete Setup Instructions for Context Edge Platform

**Last Updated:** 2024-11-14

---

## 📋 **Table of Contents**

1. [Prerequisites](#prerequisites)
2. [Installation Steps](#installation-steps)
3. [Testing the System](#testing-the-system)
4. [User Flow Walkthrough](#user-flow-walkthrough)
5. [Troubleshooting](#troubleshooting)

---

## 1. Prerequisites

### **System Requirements**

**Minimum:**
- OS: Linux, macOS, or Windows (WSL2)
- CPU: 2 cores
- RAM: 4GB
- Disk: 10GB free space
- Internet: Required for initial setup

**Recommended:**
- OS: Linux (Ubuntu 22.04+)
- CPU: 4+ cores
- RAM: 8GB+
- Disk: 20GB+ SSD

---

### **Required Software**

#### **A. Docker & Docker Compose**

Check if installed:
```bash
docker --version
docker compose version
```

**Expected output:**
```
Docker version 24.0.0, build xyz
Docker Compose version v2.20.0
```

**If not installed:**

**Ubuntu/Debian:**
```bash
# Update package list
sudo apt-get update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (avoid sudo)
sudo usermod -aG docker $USER

# Log out and back in, then verify
docker run hello-world
```

**macOS:**
```bash
# Install Docker Desktop
brew install --cask docker

# Start Docker Desktop application
open /Applications/Docker.app
```

**Windows:**
- Download Docker Desktop: https://docs.docker.com/desktop/install/windows-install/
- Enable WSL2 integration

---

#### **B. Node.js & npm**

**Required for:** Customer Portal UI (Next.js)

Check if installed:
```bash
node --version
npm --version
```

**Expected output:**
```
v18.x.x or v20.x.x
9.x.x or 10.x.x
```

**If not installed:**

**Ubuntu/Debian:**
```bash
# Install Node.js 20.x (LTS)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify
node --version
npm --version
```

**macOS:**
```bash
# Using Homebrew
brew install node

# Verify
node --version
npm --version
```

**Windows:**
- Download installer: https://nodejs.org/en/download/
- Run installer and follow prompts

---

#### **C. Python 3.9+**

**Required for:** Edge Device SDK, demo scripts

Check if installed:
```bash
python3 --version
```

**Expected output:**
```
Python 3.9.x, 3.10.x, or 3.11.x
```

**If not installed:**

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv
```

**macOS:**
```bash
brew install python@3.11
```

---

#### **D. Git**

Check if installed:
```bash
git --version
```

**If not installed:**
```bash
# Ubuntu/Debian
sudo apt-get install -y git

# macOS
brew install git
```

---

## 2. Installation Steps

### **Step 1: Clone the Repository**

```bash
cd ~
mkdir -p projects
cd projects

# Clone (replace with your actual repo URL)
git clone https://github.com/yourusername/context-edge.git
cd context-edge

# Verify structure
ls -la
```

**Expected output:**
```
context-service/
edge-device/
data-ingestion/
context-edge-ui/
demo/
docs/
k8s/
docker-compose.yml
README.md
```

---

### **Step 2: Set Up Backend Services (Docker)**

```bash
# Navigate to project root
cd /home/jeff/projects/OT\ Injection/context-edge

# Start all services
docker compose up -d

# This will:
# 1. Download Docker images (first time: ~5 minutes)
# 2. Start PostgreSQL (port 5432)
# 3. Start Redis (port 6379)
# 4. Start Context Service (port 8000)
# 5. Start Data Ingestion (port 8001)
```

**Check status:**
```bash
docker compose ps
```

**Expected output:**
```
NAME                              STATUS
context-edge-context-service-1    Up (healthy)
context-edge-data-ingestion-1     Up (healthy)
context-edge-postgres-1           Up (healthy)
context-edge-redis-1              Up
```

**Check logs:**
```bash
# All services
docker compose logs

# Specific service
docker compose logs context-service
docker compose logs postgres
```

---

### **Step 3: Populate Demo Data**

```bash
# Navigate to demo directory
cd demo

# Install Python dependencies (if needed)
pip3 install requests

# Run demo data script
python3 populate_demo_data.py
```

**Expected output:**
```
Populating demo data...
✓ Created payload for CID: QR001
✓ Created payload for CID: QR002
✓ Created payload for CID: QR003

Demo data populated successfully!
You can now:
1. Visit the admin panel: http://localhost:3000/admin
2. View API docs: http://localhost:8000/docs
3. Test the edge SDK with the demo data
```

---

### **Step 4: Set Up Customer Portal (Next.js UI)**

```bash
# Navigate to UI directory
cd ../context-edge-ui

# Install dependencies (first time: ~2 minutes)
npm install

# Start development server
npm run dev
```

**Expected output:**
```
▲ Next.js 16.0.3
- Local:        http://localhost:3000
- Network:      http://192.168.1.100:3000

✓ Ready in 2.3s
```

**Keep this terminal open** (UI server runs here)

---

### **Step 5: Set Up Edge Device SDK (Optional - For Testing)**

Open a **new terminal**:

```bash
# Navigate to edge device directory
cd /home/jeff/projects/OT\ Injection/context-edge/edge-device

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -e .

# This installs:
# - opencv-python
# - numpy
# - requests
# - redis
# - pydantic
# and makes 'context_edge' package available
```

**Verify installation:**
```bash
python3 -c "from context_edge import ContextInjectionModule; print('✓ SDK installed successfully')"
```

---

## 3. Testing the System

### **Test 1: Verify All Services Are Running**

Open browser and check:

| Service | URL | Expected |
|---------|-----|----------|
| **Customer Portal** | http://localhost:3000 | Landing page |
| **Admin Panel** | http://localhost:3000/admin | Metadata management UI |
| **Downloads Page** | http://localhost:3000/downloads | SDK download page |
| **Context API Docs** | http://localhost:8000/docs | Swagger UI |
| **Data Ingestion Docs** | http://localhost:8001/docs | Swagger UI |
| **Health Check** | http://localhost:8000/health | `{"status": "healthy"}` |

**Screenshot what you should see:**
```
http://localhost:3000
┌─────────────────────────────────────────┐
│  Context Edge                            │
│  Real-Time Ground-Truth Labeling System  │
│                                          │
│  [Downloads] [Admin Panel]               │
│                                          │
│  Project Overview...                     │
└─────────────────────────────────────────┘
```

---

### **Test 2: Admin Panel - Create Metadata**

1. **Open Admin Panel:**
   ```
   http://localhost:3000/admin
   ```

2. **Verify demo data is visible:**
   - You should see 3 metadata payloads (QR001, QR002, QR003)

3. **Create new metadata:**
   - Click "Create New Metadata Payload"
   - CID: `TEST001`
   - Metadata (JSON):
     ```json
     {
       "product_name": "Test Widget",
       "batch_number": "BATCH_TEST",
       "temperature": 25.0,
       "test": true
     }
     ```
   - Click "Create"
   - Verify it appears in the list

4. **Test CSV Import:**
   - Download: `demo/sample_metadata.csv`
   - Click "Choose File" under CSV Import
   - Select the CSV file
   - Click "Import CSV"
   - Verify 5 new records appear

---

### **Test 3: API Testing (Context Service)**

**A. Test with curl (command line):**

```bash
# Get metadata for QR001
curl http://localhost:8000/context/QR001

# Expected response:
{
  "cid": "QR001",
  "metadata": {
    "product_name": "Widget A",
    "batch_number": "BATCH001",
    "pressure_threshold": 50.5,
    "temperature_range": {"min": 20, "max": 30},
    "defect_criteria": ["crack", "discoloration"]
  },
  "timestamp": "2024-11-14T12:00:00Z"
}

# List all metadata
curl http://localhost:8000/context

# Create new metadata
curl -X POST http://localhost:8000/context \
  -H "Content-Type: application/json" \
  -d '{
    "cid": "CURL_TEST",
    "metadata": {"test": "from curl"}
  }'

# Health check
curl http://localhost:8000/health
```

**B. Test with Swagger UI:**

1. Open: http://localhost:8000/docs
2. Try "GET /context/{cid}" endpoint:
   - Click "Try it out"
   - Enter CID: `QR001`
   - Click "Execute"
   - See response below

---

### **Test 4: Edge SDK Testing**

**A. Simple Python Test (No Camera):**

```bash
# Make sure virtual environment is activated
cd /home/jeff/projects/OT\ Injection/context-edge/edge-device
source venv/bin/activate

# Create test script
cat > test_sdk.py << 'EOF'
from context_edge.context_injector import ContextInjectionModule
import json

# Initialize CIM (points to local Context Service)
cim = ContextInjectionModule(
    context_service_url="http://localhost:8000",
    redis_host="localhost"
)

# Simulate sensor data
sensor_data = {
    "temperature": 25.5,
    "pressure": 1013.25,
    "vibration": 0.05,
    "timestamp": "2024-11-14T12:00:00"
}

# Test context injection with QR001
print("Testing Context Injection Module...")
ldo = cim.inject_context(sensor_data, detected_cid="QR001")

print("\n✓ Success! Generated LDO:")
print(json.dumps(ldo, indent=2))

# Test that metadata was cached
print("\n✓ Testing cache (2nd call should be instant)...")
ldo2 = cim.inject_context(sensor_data, detected_cid="QR001")
print("✓ Cache working!")

# Test with different CID
print("\n✓ Testing with different CID (QR002)...")
ldo3 = cim.inject_context(sensor_data, detected_cid="QR002")
print(json.dumps(ldo3, indent=2))
EOF

# Run test
python3 test_sdk.py
```

**Expected output:**
```
Testing Context Injection Module...

✓ Success! Generated LDO:
{
  "sensor_data": {
    "temperature": 25.5,
    "pressure": 1013.25,
    "vibration": 0.05,
    "timestamp": "2024-11-14T12:00:00"
  },
  "context_metadata": {
    "cid": "QR001",
    "metadata": {
      "product_name": "Widget A",
      "batch_number": "BATCH001",
      "pressure_threshold": 50.5
    },
    "timestamp": "2024-11-14T12:00:00Z"
  },
  "timestamp": 1700000000.123,
  "cid": "QR001"
}

✓ Testing cache (2nd call should be instant)...
✓ Cache working!

✓ Testing with different CID (QR002)...
{
  "sensor_data": { ... },
  "context_metadata": {
    "cid": "QR002",
    "metadata": {
      "product_name": "Widget B",
      ...
    }
  },
  ...
}
```

---

**B. QR Code Detection Test (With Webcam - Optional):**

```bash
# Generate QR code for testing
# Visit: https://www.qr-code-generator.com/
# Content: QR001
# Download/print the QR code

# Or generate with Python:
pip install qrcode pillow

python3 << 'EOF'
import qrcode
img = qrcode.make("QR001")
img.save("qr_test_QR001.png")
print("✓ QR code saved to qr_test_QR001.png")
print("  Display this on your phone or print it")
EOF

# Test QR detection
python3 << 'EOF'
from context_edge.qr_decoder import QRDecoder
import cv2

decoder = QRDecoder()

# Open webcam
cap = cv2.VideoCapture(0)

print("Point QR code at camera...")
print("Press 'q' to quit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Try to decode QR
    cid = decoder.detect_and_decode(frame)

    if cid:
        print(f"\n✓ Detected QR code: {cid}")

    # Show video
    cv2.imshow('QR Detection Test', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
EOF
```

---

### **Test 5: Data Ingestion Testing**

**Upload a test LDO:**

```bash
# Create a test video file (or use any MP4)
# Simple test video (1 second black screen)
ffmpeg -f lavfi -i color=black:s=640x480:d=1 -pix_fmt yuv420p test_video.mp4

# Upload to Data Ingestion Service
curl -X POST http://localhost:8001/ingest/ldo \
  -F "video=@test_video.mp4" \
  -F 'metadata={
    "sensor_data": {"temperature": 25.0},
    "context_metadata": {"cid": "QR001"},
    "timestamp": 1700000000
  }'

# Expected response:
{
  "id": "ldo_abc123_1700000000",
  "status": "ingested",
  "message": "LDO successfully ingested",
  "size_bytes": 12345
}

# List all LDOs
curl http://localhost:8001/ingest/list

# Check specific LDO status
curl http://localhost:8001/ingest/status/ldo_abc123_1700000000
```

---

### **Test 6: Full End-to-End Test**

**Complete workflow simulation:**

```bash
# 1. Create metadata (via Admin Panel or API)
curl -X POST http://localhost:8000/context \
  -H "Content-Type: application/json" \
  -d '{
    "cid": "E2E_TEST",
    "metadata": {
      "product": "End-to-End Test Widget",
      "test_run": true
    }
  }'

# 2. Edge device scans QR and generates LDO
cd edge-device
source venv/bin/activate

python3 << 'EOF'
from context_edge.context_injector import ContextInjectionModule
from context_edge.ldo_generator import LDOGenerator
import json

cim = ContextInjectionModule("http://localhost:8000", "localhost")
ldo_gen = LDOGenerator(output_dir="ldo_output")

# Simulate edge device workflow
sensor_data = {"temperature": 30.0, "status": "running"}
detected_cid = "E2E_TEST"

# Generate LDO
ldo = cim.inject_context(sensor_data, detected_cid)
ldo_id = ldo_gen.generate_ldo(ldo, frame=None)

print(f"✓ Generated LDO: {ldo_id}")
print(f"✓ Saved to: ldo_output/{ldo_id}/")

# Verify files
import os
ldo_path = f"ldo_output/{ldo_id}"
files = os.listdir(ldo_path)
print(f"✓ Files created: {files}")
EOF

# 3. Verify LDO was created
ls -la edge-device/ldo_output/

# 4. Upload to Data Ingestion (manual test)
# Use Admin Panel or curl to upload the LDO
```

---

## 4. User Flow Walkthrough

### **Scenario: New User Discovers Context Edge**

**Step 1: User visits website**
```
User types: http://your-domain.com (or localhost:3000)

Sees:
┌─────────────────────────────────────────────────┐
│  Context Edge                                    │
│  Real-Time Ground-Truth Labeling System          │
│                                                  │
│  [Get Started] [Admin Panel]                    │
│                                                  │
│  • 100% ground-truth accuracy                   │
│  • <100ms latency                               │
│  • 70%+ bandwidth reduction                     │
│  • 90%+ cost savings                            │
│                                                  │
│  [Architecture Overview]                        │
│  [Use Cases]                                    │
│  [Technology Stack]                             │
└─────────────────────────────────────────────────┘
```

**Step 2: User clicks "Get Started" → Downloads Page**
```
http://localhost:3000/downloads

Sees:
┌─────────────────────────────────────────────────┐
│  Downloads                                       │
│                                                  │
│  📦 Edge Device SDK                              │
│     Python SDK for NVIDIA Jetson devices        │
│     Install: pip install context-edge-sdk       │
│     [Download] [Documentation]                  │
│                                                  │
│  🐳 Context Service                              │
│     Docker Compose setup                        │
│     Install: docker-compose up -d               │
│     [Download] [Documentation]                  │
│                                                  │
│  📚 Quick Start Guide                            │
│     30-minute setup walkthrough                 │
│     [View Guide]                                │
└─────────────────────────────────────────────────┘
```

**Step 3: User follows Quick Start**
```
User clicks [View Guide] → Opens docs/quick-start-guide.md

Follows:
1. docker-compose up -d
2. python populate_demo_data.py
3. Open Admin Panel
4. Create metadata
5. Test Edge SDK
```

**Step 4: User accesses Admin Panel**
```
http://localhost:3000/admin

User can:
✓ View existing metadata
✓ Create new product metadata
✓ Edit existing metadata
✓ Delete metadata
✓ Bulk import from CSV
```

**Step 5: User deploys to factory**
```
User:
1. Installs Context Service (Docker) on factory server
2. Prints QR codes for products
3. Installs Edge SDK on Jetson device
4. Points camera at production line
5. System automatically generates labeled data
6. Data uploaded to cloud/data lake
7. ML engineer downloads for training
```

---

## 5. Troubleshooting

### **Problem: Docker containers won't start**

**Check Docker is running:**
```bash
docker ps

# If error: "Cannot connect to Docker daemon"
sudo systemctl start docker  # Linux
# Or start Docker Desktop app (macOS/Windows)
```

**Check logs:**
```bash
docker compose logs postgres
docker compose logs context-service
```

**Reset everything:**
```bash
docker compose down
docker compose up -d --force-recreate
```

---

### **Problem: Admin Panel shows "Error fetching payloads"**

**Check Context Service is running:**
```bash
curl http://localhost:8000/health

# If fails:
docker compose logs context-service
docker compose restart context-service
```

**Check CORS:**
- Context Service should allow `http://localhost:3000`
- Already configured in code (see `context-service/src/api/main.py`)

---

### **Problem: "Module not found" when running Edge SDK**

**Make sure virtual environment is activated:**
```bash
cd edge-device
source venv/bin/activate  # You should see (venv) in prompt

# If venv doesn't exist:
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

**Or install globally (not recommended):**
```bash
cd edge-device
pip3 install -e .
```

---

### **Problem: Next.js won't start**

**Check Node.js version:**
```bash
node --version  # Should be v18+ or v20+
```

**Clean install:**
```bash
cd context-edge-ui
rm -rf node_modules package-lock.json
npm install
npm run dev
```

**Port already in use:**
```bash
# Find what's using port 3000
lsof -i :3000  # macOS/Linux
netstat -ano | findstr :3000  # Windows

# Kill the process or use different port
npm run dev -- -p 3001
```

---

### **Problem: QR code detection not working**

**Check camera access:**
```bash
# List cameras
ls /dev/video*  # Linux

# Test camera
python3 << 'EOF'
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret:
    print("✓ Camera working")
    cv2.imwrite("test.jpg", frame)
else:
    print("✗ Camera not working")
cap.release()
EOF
```

**Check lighting:**
- QR codes need good lighting
- Avoid glare/reflections
- Hold QR code steady (not blurry)

---

### **Problem: Redis connection errors**

**Check Redis is running:**
```bash
docker compose ps redis

# Test connection
docker exec -it context-edge-redis-1 redis-cli ping
# Should return: PONG

# If fails, restart:
docker compose restart redis
```

---

## 6. Quick Command Reference

### **Start Everything:**
```bash
# Backend
cd /home/jeff/projects/OT\ Injection/context-edge
docker compose up -d

# Frontend
cd context-edge-ui
npm run dev

# Edge SDK (in new terminal)
cd edge-device
source venv/bin/activate
```

### **Stop Everything:**
```bash
# Stop UI (Ctrl+C in terminal where npm run dev is running)

# Stop backend
cd /home/jeff/projects/OT\ Injection/context-edge
docker compose down
```

### **Reset Everything:**
```bash
# WARNING: Deletes all data!
cd /home/jeff/projects/OT\ Injection/context-edge
docker compose down -v  # -v deletes volumes (database)
docker compose up -d
cd demo
python3 populate_demo_data.py
```

### **Check Status:**
```bash
# Backend services
docker compose ps

# Backend logs
docker compose logs -f

# Check ports
netstat -tuln | grep -E '3000|8000|8001|5432|6379'
```

---

## ✅ Success Checklist

After installation, you should be able to:

- [ ] Visit http://localhost:3000 (Landing page loads)
- [ ] Visit http://localhost:3000/admin (See 3+ metadata entries)
- [ ] Visit http://localhost:3000/downloads (See SDK download page)
- [ ] Visit http://localhost:8000/docs (Swagger UI for Context Service)
- [ ] Visit http://localhost:8001/docs (Swagger UI for Data Ingestion)
- [ ] Run `curl http://localhost:8000/health` (Returns `{"status":"healthy"}`)
- [ ] Create new metadata in Admin Panel
- [ ] Import CSV in Admin Panel
- [ ] Run Edge SDK test (Python script works)
- [ ] Upload test LDO via curl

**If all checkboxes pass: ✅ System is ready for production deployment!**

---

## 📞 Need Help?

- **Documentation**: `/docs/quick-start-guide.md`
- **API Reference**: http://localhost:8000/docs
- **GitHub Issues**: (for bug reports)
- **Email Support**: support@context-edge.com

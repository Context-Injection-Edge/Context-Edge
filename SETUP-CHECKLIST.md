# Setup Checklist - Quick Reference

## ✅ What You Need to Install

### 1. **Docker & Docker Compose** (REQUIRED)
- [ ] Docker installed (`docker --version`)
- [ ] Docker Compose installed (`docker compose version`)
- [ ] Docker daemon running (`docker ps`)

**Install:**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# macOS
brew install --cask docker

# Verify
docker run hello-world
```

---

### 2. **Node.js & npm** (For Customer Portal UI)
- [ ] Node.js v18+ or v20+ installed (`node --version`)
- [ ] npm installed (`npm --version`)

**Install:**
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# macOS
brew install node

# Verify
node --version  # Should show v18.x or v20.x
npm --version   # Should show 9.x or 10.x
```

---

### 3. **Python 3.9+** (For Edge Device SDK)
- [ ] Python 3.9+ installed (`python3 --version`)
- [ ] pip installed (`pip3 --version`)
- [ ] venv module available (`python3 -m venv --help`)

**Install:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv

# macOS
brew install python@3.11

# Verify
python3 --version  # Should show 3.9.x, 3.10.x, or 3.11.x
```

---

### 4. **Git** (For cloning repository)
- [ ] Git installed (`git --version`)

**Install:**
```bash
# Ubuntu/Debian
sudo apt-get install -y git

# macOS
brew install git
```

---

## 🚀 Quick Setup Commands

### **Backend Services (Docker)**
```bash
cd /home/jeff/projects/OT\ Injection/context-edge
docker compose up -d
```

**What this installs automatically (via Docker):**
- ✅ PostgreSQL 15 (database)
- ✅ Redis 7 (cache)
- ✅ Context Service (FastAPI)
- ✅ Data Ingestion Service (FastAPI)

**No manual installation needed!** Docker handles all Python dependencies for backend.

---

### **Customer Portal (Next.js)**
```bash
cd /home/jeff/projects/OT\ Injection/context-edge-ui
npm install  # Installs all Node.js packages
npm run dev  # Starts development server
```

**What `npm install` installs automatically:**
- ✅ Next.js 16.0.3
- ✅ React 19.2.0
- ✅ Tailwind CSS 4
- ✅ TypeScript 5
- ✅ ESLint 9
- ✅ Mermaid (for diagrams)
- ✅ ~50 other dependencies

**Stored in:** `context-edge-ui/node_modules/` (created automatically)

---

### **Edge Device SDK (Python)**
```bash
cd /home/jeff/projects/OT\ Injection/context-edge/edge-device

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# Install SDK and dependencies
pip install -e .
```

**What `pip install -e .` installs automatically:**
- ✅ opencv-python (QR code detection)
- ✅ numpy (array processing)
- ✅ requests (HTTP client)
- ✅ redis (cache client)
- ✅ pydantic (data validation)
- ✅ pyzbar (barcode support - ready for future)
- ✅ pillow (image processing)

**Stored in:** `edge-device/venv/` (isolated from system Python)

---

## 🧪 Testing

### **Run Automated Test Script**
```bash
cd /home/jeff/projects/OT\ Injection/context-edge
./test-system.sh
```

**What it checks:**
- ✅ Docker is running
- ✅ All 4 backend services are up
- ✅ Context Service API responds (port 8000)
- ✅ Data Ingestion API responds (port 8001)
- ✅ PostgreSQL is accessible
- ✅ Redis is accessible
- ✅ UI is running (port 3000)
- ✅ Python and Node.js are installed

---

## 📊 Port Usage

| Port | Service | URL |
|------|---------|-----|
| **3000** | Customer Portal (Next.js) | http://localhost:3000 |
| **8000** | Context Service API | http://localhost:8000/docs |
| **8001** | Data Ingestion API | http://localhost:8001/docs |
| **5432** | PostgreSQL | localhost:5432 (internal) |
| **6379** | Redis | localhost:6379 (internal) |

**Make sure these ports are free!**

Check:
```bash
# Linux/macOS
lsof -i :3000
lsof -i :8000

# Or
netstat -tuln | grep -E '3000|8000|8001'
```

---

## 🎯 User Flow After Setup

1. **User visits:** http://localhost:3000
   - Sees landing page
   - Clicks "Downloads" button

2. **Downloads page:** http://localhost:3000/downloads
   - Downloads Docker Compose setup
   - Downloads Edge SDK
   - Views quick-start guide

3. **Admin panel:** http://localhost:3000/admin
   - Creates metadata for products
   - Bulk imports from CSV
   - Manages QR code mappings

4. **Factory deployment:**
   - Install Context Service (Docker) on factory server
   - Print QR codes for products
   - Install Edge SDK on Jetson/camera devices
   - System automatically generates labeled data

---

## ❓ Common Questions

### Q: Do I need to install PostgreSQL manually?
**A:** No! Docker Compose handles it. Just run `docker compose up -d`

### Q: Do I need to install FastAPI/Python packages for backend?
**A:** No! All backend dependencies are in Docker containers.

### Q: What about the Edge SDK - do I need Python there?
**A:** Yes, but only if you're testing locally. In production, it runs on Jetson devices.

### Q: Can I skip the virtual environment for Edge SDK?
**A:** You can, but it's not recommended. Virtual environment keeps dependencies isolated.

### Q: What if I don't have a webcam?
**A:** You can still test everything except QR detection. Use the Python API test instead.

### Q: Do customers need all this setup?
**A:** No! Customers get:
  - **Backend:** Pre-built Docker images (one command to deploy)
  - **Edge SDK:** PyPI package (`pip install context-edge-sdk`)
  - **UI:** Hosted by you OR they deploy Docker image

---

## 🐛 Quick Troubleshooting

### Backend won't start
```bash
# Check Docker
docker ps

# View logs
docker compose logs context-service

# Restart everything
docker compose down
docker compose up -d
```

### UI won't start
```bash
# Check Node version
node --version  # Must be v18+

# Clean install
cd context-edge-ui
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Edge SDK import error
```bash
# Make sure venv is activated
cd edge-device
source venv/bin/activate  # Should see (venv) in prompt

# Reinstall
pip install -e .

# Test
python3 -c "from context_edge import ContextInjectionModule; print('OK')"
```

---

## ✅ Success Checklist

After setup, you should have:

- [ ] Docker containers running (4 services)
- [ ] Customer Portal accessible at http://localhost:3000
- [ ] Admin Panel showing demo data (QR001, QR002, QR003)
- [ ] API docs accessible at http://localhost:8000/docs
- [ ] `./test-system.sh` passes all tests
- [ ] Edge SDK importable (`python3 -c "import context_edge"`)

**If all checked:** ✅ **System ready for demos and deployment!**

---

## 📚 More Info

- **Full installation guide:** [docs/INSTALLATION-AND-TESTING.md](docs/INSTALLATION-AND-TESTING.md)
- **Quick start (30 min):** [docs/quick-start-guide.md](docs/quick-start-guide.md)
- **Strategy docs:** [docs/CURRENT-STATE-AND-RECOMMENDATION.md](docs/CURRENT-STATE-AND-RECOMMENDATION.md)

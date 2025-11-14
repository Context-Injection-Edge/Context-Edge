#!/bin/bash
# Context Edge - Smart Startup Script (Docker/Podman Auto-Detection)

set -e

echo "========================================="
echo "Context Edge - Platform Initialization"
echo "========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Detect container runtime
if command -v docker &> /dev/null && docker info &> /dev/null 2>&1; then
    RUNTIME="docker"
    COMPOSE_CMD="docker compose"
    echo -e "${GREEN}✓ Detected: Docker${NC}"
elif command -v podman &> /dev/null; then
    RUNTIME="podman"
    if command -v podman-compose &> /dev/null; then
        COMPOSE_CMD="podman-compose"
        echo -e "${GREEN}✓ Detected: Podman with podman-compose${NC}"
    else
        echo -e "${RED}✗ Podman detected but podman-compose not found${NC}"
        echo "  Install with: pip3 install podman-compose"
        exit 1
    fi
else
    echo -e "${RED}✗ Neither Docker nor Podman found${NC}"
    echo "  Install Docker from: https://docs.docker.com/get-docker/"
    echo "  Or install Podman from: https://podman.io/getting-started/installation"
    exit 1
fi

echo ""
echo "Starting services with $RUNTIME..."
echo ""

# Start backend services
$COMPOSE_CMD up -d

echo ""
echo "Waiting for services to be ready..."
sleep 8

# Check service health
echo ""
echo "Health Checks:"
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo -e "${GREEN}✓ Context Service (port 8000)${NC}"
else
    echo -e "${YELLOW}⚠ Context Service not ready yet${NC}"
fi

if curl -s http://localhost:8001/health &> /dev/null; then
    echo -e "${GREEN}✓ Data Ingestion Service (port 8001)${NC}"
else
    echo -e "${YELLOW}⚠ Data Ingestion Service not ready yet${NC}"
fi

echo ""
echo "========================================="
echo "Backend services started!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Populate demo data:"
echo "   cd demo && python3 populate_demo_data.py"
echo ""
echo "2. Start the UI (in another terminal):"
echo "   cd ../context-edge-ui"
echo "   npm install"
echo "   npm run dev"
echo ""
echo "3. Access the platform:"
echo "   • Landing Page:  http://localhost:3000"
echo "   • Admin Panel:   http://localhost:3000/admin"
echo "   • API Docs:      http://localhost:8000/docs"
echo ""

#!/bin/bash
# Context Edge - System Test Script
# This script tests all components of the platform

set -e  # Exit on error

echo "=================================="
echo "Context Edge - System Test"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Test function
test_endpoint() {
    local name=$1
    local url=$2
    local expected=$3

    echo -n "Testing $name... "

    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((FAILED++))
        return 1
    fi
}

echo "1. Testing Docker Services"
echo "--------------------------"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    echo "  Start Docker and run: docker compose up -d"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"

# Check containers
CONTAINERS=$(docker compose ps --services 2>/dev/null | wc -l)
if [ "$CONTAINERS" -gt 0 ]; then
    echo -e "${GREEN}✓ Docker Compose services: $CONTAINERS${NC}"
    docker compose ps
else
    echo -e "${YELLOW}⚠ No Docker Compose services running${NC}"
    echo "  Run: docker compose up -d"
fi

echo ""
echo "2. Testing Backend APIs"
echo "-----------------------"

# Test Context Service Health
test_endpoint "Context Service Health" "http://localhost:8000/health" "healthy"

# Test Context Service API Docs
test_endpoint "Context Service API Docs" "http://localhost:8000/docs" "swagger"

# Test Data Ingestion Health
test_endpoint "Data Ingestion Health" "http://localhost:8001/health" "healthy"

# Test Data Ingestion API Docs
test_endpoint "Data Ingestion API Docs" "http://localhost:8001/docs" "swagger"

# Test if we can fetch metadata
echo -n "Testing Context Service GET /context... "
if curl -s http://localhost:8000/context | grep -q "cid"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ No data (run populate_demo_data.py)${NC}"
fi

echo ""
echo "3. Testing Frontend UI"
echo "----------------------"

# Check if Node.js is installed
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js installed: $NODE_VERSION${NC}"
else
    echo -e "${RED}✗ Node.js not installed${NC}"
    echo "  Install from: https://nodejs.org/"
fi

# Check if UI is running
if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
    test_endpoint "Landing Page" "http://localhost:3000" ""
    test_endpoint "Admin Panel" "http://localhost:3000/admin" ""
    test_endpoint "Downloads Page" "http://localhost:3000/downloads" ""
else
    echo -e "${YELLOW}⚠ UI not running${NC}"
    echo "  Start with: cd context-edge-ui && npm run dev"
fi

echo ""
echo "4. Testing Python Environment"
echo "-----------------------------"

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Python installed: $PYTHON_VERSION${NC}"

    # Check if Edge SDK is installed
    if python3 -c "import context_edge" 2>/dev/null; then
        echo -e "${GREEN}✓ Edge SDK installed${NC}"
    else
        echo -e "${YELLOW}⚠ Edge SDK not installed${NC}"
        echo "  Install with: cd edge-device && pip install -e ."
    fi
else
    echo -e "${RED}✗ Python not installed${NC}"
fi

echo ""
echo "5. Testing Database Connections"
echo "--------------------------------"

# Test PostgreSQL
echo -n "Testing PostgreSQL... "
if docker exec context-edge-postgres-1 pg_isready -U context_user -d context_edge > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAILED++))
fi

# Test Redis
echo -n "Testing Redis... "
if docker exec context-edge-redis-1 redis-cli ping | grep -q "PONG"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAILED++))
fi

echo ""
echo "=================================="
echo "Test Results"
echo "=================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Your Context Edge platform is ready!"
    echo ""
    echo "Access points:"
    echo "  • Landing Page:  http://localhost:3000"
    echo "  • Admin Panel:   http://localhost:3000/admin"
    echo "  • Downloads:     http://localhost:3000/downloads"
    echo "  • API Docs:      http://localhost:8000/docs"
    echo ""
    exit 0
else
    echo -e "${YELLOW}⚠ Some tests failed${NC}"
    echo ""
    echo "See INSTALLATION-AND-TESTING.md for troubleshooting"
    exit 1
fi

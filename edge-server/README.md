# Context Edge - Edge Server

**The brain of Context Edge.** Receives CIDs from camera devices, performs fusion, runs AI inference, and generates LDOs.

## What It Does

This is where the magic happens:

1. **Receives CID** from camera device
2. **Fetches context** from Redis (product_id, batch, operator, etc.)
3. **Reads PLC sensors** (temperature, vibration, pressure, etc.)
4. **Fuses data** - Context Injection Module (CIM) - PATENTED
5. **Runs AI inference** to predict good/defective
6. **Generates LDO** and stores in PostgreSQL

## Architecture

```
Camera Device                Edge Server
━━━━━━━━━━━                ━━━━━━━━━━━━━━━━━━━━━━━━━━
QR Scan → CID ────────────► 1. Receive CID
                             2. Redis.get(CID) → context
                             3. PLC.read() → sensors
                             4. CIM Fusion ──┐
                             5. AI Inference │
                             6. LDO → PostgreSQL
                                      │
                                      └──► Training Data
```

## Services

### Context Lookup Service
- Fetches context metadata from Redis using CID as key
- Sub-1ms lookup time
- Handles cache misses gracefully

### Fusion Service (CIM)
- **Patented Context Injection Module**
- Combines context + sensor data
- Protocol adapters: Modbus TCP, OPC UA
- Fallback to mock data for testing

### LDO Generator Service
- Creates Labeled Data Objects
- Stores in PostgreSQL
- Adds low-confidence predictions to feedback queue

## Deployment

### Docker Compose (Recommended)

```yaml
# docker-compose.yml includes:
services:
  redis:          # Context cache
  postgres:       # Data storage
  edge-server:    # This service
```

Run:
```bash
docker-compose up -d
```

### Environment Variables

```bash
# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=context_edge
POSTGRES_USER=context_user
POSTGRES_PASSWORD=context_pass

# PLC Connections (optional)
MODBUS_HOST=192.168.1.10
MODBUS_PORT=502
OPCUA_SERVER_URL=opc.tcp://192.168.1.11:4840

# Mock data for testing
USE_MOCK_SENSORS=true
```

## API Endpoints

### POST /cid
Receive CID from camera device

**Request:**
```json
{
  "cid": "CID-PROD-12345",
  "camera_id": "CAM-Line1-Station1",
  "timestamp": "2025-01-16T10:30:00"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "LDO generated successfully",
  "ldo_id": "LDO-20250116103000-12345"
}
```

### GET /health
Health check

### GET /stats
Server statistics

## Protocol Adapters

### Modbus TCP
- Reads holding/input registers
- Configurable register mappings
- Auto-reconnect on failure

### OPC UA
- Reads node values
- Configurable node mappings
- Auto-reconnect on failure

### Adding More Protocols
Easy to extend:
- EtherNet/IP: Allen-Bradley PLCs
- PROFINET: Siemens PLCs
- S7: Siemens S7 protocol
- BACnet: Building automation

## Development

### Run Locally

```bash
cd edge-server

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export REDIS_HOST=localhost
export POSTGRES_HOST=localhost
export USE_MOCK_SENSORS=true

# Run
python -m app.main
```

### Run Tests

```bash
pytest tests/
```

## Scaling

**Single Edge Server handles:**
- 5-10 cameras simultaneously
- ~1000 LDOs per day
- Sub-100ms processing time per CID

**For larger deployments:**
- Deploy multiple edge servers
- Use K3s for orchestration
- Load balance with nginx

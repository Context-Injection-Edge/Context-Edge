# Configuration Management Architecture

**Updated:** 2025-01-16

---

## Overview

Context Edge uses a **3-tier configuration system** following industrial IoT best practices:

1. **Environment Variables** - Deployment-level secrets and infrastructure
2. **Database** - Runtime-configurable adapter settings
3. **Admin UI** - User-facing configuration management

---

## 1. Environment Variables (Deployment-Level)

### What Goes Here:
- **Secrets** (passwords, API keys, tokens)
- **Infrastructure** (database URLs, Redis hosts)
- **Deployment flags** (PROD vs DEV)

### Examples:

```bash
# Infrastructure
REDIS_HOST=redis
POSTGRES_HOST=postgres
POSTGRES_PASSWORD=secret123

# Data ingestion
DATA_INGESTION_URL=http://data-ingestion:8001

# Feature flags
USE_MOCK_SENSORS=false
```

### Where Configured:
- `.env` files (local development)
- Docker Compose environment section
- Kubernetes Secrets
- AWS Parameter Store / HashiCorp Vault (production)

**✅ Good for:** Infrastructure, secrets, deployment-specific settings
**❌ Bad for:** Adapter configurations, device mappings (too rigid)

---

## 2. Database (Runtime-Configurable)

### What Goes Here:
- **Adapter configurations** (MES, ERP, SCADA endpoints)
- **Device mappings** (which device uses which adapter)
- **Data source priorities** (try Modbus first, then MES)
- **Business rules** (quality thresholds, alert configs)

### Database Schema:

```sql
-- Adapter configurations (managed by admin UI)
CREATE TABLE data_source_configs (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) UNIQUE NOT NULL,  -- "Line1-Modbus-PLC"
    adapter_type VARCHAR(50) NOT NULL,         -- "modbus", "mes", "erp", "scada"
    config JSONB NOT NULL,                     -- Adapter-specific config
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Example data
INSERT INTO data_source_configs (source_name, adapter_type, config) VALUES
(
    'Line1-Modbus-PLC',
    'modbus',
    '{
        "host": "192.168.1.100",
        "port": 502,
        "register_mappings": {
            "temperature": {"address": 0, "type": "holding", "scale": 100.0},
            "vibration": {"address": 2, "type": "holding", "scale": 100.0}
        }
    }'
),
(
    'Factory-Wonderware-MES',
    'mes',
    '{
        "adapter_class": "WonderwareMESAdapter",
        "base_url": "https://mes.factory.com",
        "api_key": "API_KEY_FROM_VAULT",
        "data_endpoint": "/api/v1/production/workorders/active"
    }'
),
(
    'Corporate-SAP-ERP',
    'erp',
    '{
        "adapter_class": "SAPAdapter",
        "base_url": "https://sap.corp.com",
        "username": "API_USER",
        "password": "PASSWORD_FROM_VAULT",
        "data_endpoint": "/sap/opu/odata/sap/API_PRODUCTION_ORDER_2_SRV/A_ProductionOrder"
    }'
);

-- Device-to-adapter mappings
CREATE TABLE device_adapter_mappings (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(100) NOT NULL,           -- "EDGE-Line1-Station1"
    data_source_id INTEGER REFERENCES data_source_configs(id),
    priority INTEGER DEFAULT 1,                -- Try higher priority first
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Example: Device uses multiple sources
INSERT INTO device_adapter_mappings (device_id, data_source_id, priority) VALUES
('EDGE-Line1-Station1', 1, 1),  -- Modbus PLC (highest priority)
('EDGE-Line1-Station1', 2, 2),  -- Wonderware MES (fallback)
('EDGE-Line1-Station1', 3, 3);  -- SAP ERP (lowest priority)
```

### Why Database Configuration?

**Scenario:** Factory adds new production line

**Without Database Config:**
1. Developer edits code
2. Restart edge server
3. Downtime for all lines
4. Requires technical expertise

**With Database Config:**
1. Admin opens UI
2. Clicks "Add Adapter"
3. Fills form (PLC IP, register mappings)
4. Clicks "Save"
5. Adapter hot-reloaded (no downtime)
6. Production continues

**✅ Good for:** Adapters, devices, business rules
**❌ Bad for:** Secrets (use environment variables + secrets manager)

---

## 3. Admin UI (User-Facing)

### What Users Configure:

#### **Adapter Management:**
- Add/edit/delete data source adapters
- Test connection health
- View real-time data from each source
- Enable/disable adapters

#### **Device Registration:**
- Register new edge devices
- Assign adapters to devices
- Set priority (try PLC first, then MES)
- View device status

#### **Business Rules:**
- Set quality thresholds
- Configure alerts
- Define fusion logic

### UI Wireframe:

```
┌─────────────────────────────────────────────┐
│ Context Edge - Admin Dashboard             │
├─────────────────────────────────────────────┤
│                                             │
│ 📊 Data Sources                             │
│ ┌─────────────────────────────────────────┐ │
│ │ Name              Type    Status        │ │
│ │ Line1-Modbus-PLC  Modbus  ✅ Connected  │ │
│ │ Wonderware-MES    MES     ✅ Connected  │ │
│ │ SAP-ERP           ERP     ⚠️  Timeout   │ │
│ │                   [+ Add Adapter]       │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ 🖥️  Edge Devices                            │
│ ┌─────────────────────────────────────────┐ │
│ │ Device ID            Status   Adapters  │ │
│ │ EDGE-Line1-Station1  🟢 Online    3     │ │
│ │ EDGE-Line2-Station2  🔴 Offline   2     │ │
│ │                   [+ Register Device]   │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### Admin UI Features:

**Add Adapter Form:**
```
┌─────────────────────────────────────┐
│ Add Data Source Adapter             │
├─────────────────────────────────────┤
│ Adapter Name: [Line3-PLC          ] │
│                                     │
│ Adapter Type:                       │
│   ○ Modbus TCP                      │
│   ○ OPC UA                          │
│   ○ Wonderware MES                  │
│   ● SAP ERP                         │
│   ○ Oracle ERP                      │
│   ○ Ignition SCADA                  │
│                                     │
│ --- SAP Configuration ---           │
│ Base URL: [https://sap.corp.com  ] │
│ Username: [API_USER              ] │
│ Password: [••••••••              ] │
│ OData Endpoint: [/sap/opu/odata/] │
│                                     │
│ [Test Connection]  [Save] [Cancel] │
└─────────────────────────────────────┘
```

**Test Connection Results:**
```
✅ Connection successful
✅ Authentication OK
✅ Sample data retrieved:
   - Work Order: WO-12345
   - Material: MAT-001
   - Quantity: 1000
```

---

## Configuration Flow

### Startup Sequence:

```
1. Edge Server starts
   └─ Reads environment variables (POSTGRES_HOST, REDIS_HOST)

2. Connects to PostgreSQL
   └─ Loads data_source_configs table

3. Initializes adapters dynamically
   ├─ Modbus adapter for Line1-Modbus-PLC
   ├─ Wonderware adapter for Factory-Wonderware-MES
   └─ SAP adapter for Corporate-SAP-ERP

4. Ready to receive CIDs
   └─ Device sends CID
   └─ Lookup device_adapter_mappings
   └─ Read data from Modbus (priority 1)
   └─ Read data from MES (priority 2)
   └─ Read data from ERP (priority 3)
   └─ Fuse all data sources
```

### Hot Reload (No Downtime):

```python
# Admin UI calls API:
POST /api/admin/adapters
{
    "source_name": "Line4-PLC",
    "adapter_type": "modbus",
    "config": {...}
}

# Edge server:
1. Inserts into data_source_configs
2. Initializes new adapter
3. Adds to fusion service
4. Returns success (adapter ready immediately)
```

---

## Secrets Management

### Development (Local):
```bash
# .env file
SAP_PASSWORD=dev_password
MES_API_KEY=dev_key_123
```

### Production (Best Practice):

**Option 1: HashiCorp Vault**
```python
import hvac

client = hvac.Client(url='https://vault.corp.com', token=os.getenv('VAULT_TOKEN'))
sap_password = client.secrets.kv.v2.read_secret_version(path='context-edge/sap')['data']['password']
```

**Option 2: AWS Secrets Manager**
```python
import boto3

client = boto3.client('secretsmanager')
response = client.get_secret_value(SecretId='context-edge/sap-password')
sap_password = response['SecretString']
```

**Option 3: Kubernetes Secrets**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: context-edge-secrets
type: Opaque
data:
  sap-password: <base64-encoded>
  mes-api-key: <base64-encoded>
```

**Database stores reference, not secret:**
```json
{
    "adapter_type": "erp",
    "config": {
        "password": "SECRET:vault:context-edge/sap/password"
    }
}
```

Edge server resolves at runtime:
```python
if config['password'].startswith('SECRET:vault:'):
    path = config['password'].replace('SECRET:vault:', '')
    config['password'] = vault_client.read(path)
```

---

## Recommended Architecture

### For POC/Development:
```
✅ Environment variables (.env file)
✅ Hard-coded adapter configs in fusion.py
❌ No admin UI yet
```

### For Production Deployment:
```
✅ Environment variables (infrastructure only)
✅ Database (adapter configs, device mappings)
✅ Admin UI (configuration management)
✅ Secrets manager (HashiCorp Vault, AWS Secrets Manager)
```

---

## Implementation Phases

### Phase 1 (Current - POC):
- Hard-coded adapter configs in code
- Environment variables for secrets
- Manual configuration

### Phase 2 (Next - Production Ready):
- Database-driven adapter configuration
- Admin UI for adapter management
- Hot reload capability

### Phase 3 (Future - Enterprise):
- Secrets manager integration
- Multi-tenant configuration
- Role-based access control (RBAC)
- Audit logging

---

## Example: Complete Configuration

### Environment Variables (.env):
```bash
# Infrastructure
POSTGRES_HOST=postgres
REDIS_HOST=redis

# Secrets (vault references)
VAULT_URL=https://vault.corp.com
VAULT_TOKEN=s.abc123
```

### Database (data_source_configs):
```sql
-- Modbus PLC
{
    "source_name": "Line1-Modbus-PLC",
    "adapter_type": "modbus",
    "config": {
        "host": "192.168.1.100",
        "port": 502,
        "register_mappings": {...}
    }
}

-- Wonderware MES
{
    "source_name": "Wonderware-MES",
    "adapter_type": "mes",
    "config": {
        "adapter_class": "WonderwareMESAdapter",
        "base_url": "https://mes.factory.com",
        "api_key": "SECRET:vault:mes/api_key"
    }
}
```

### Admin UI:
- Manufacturer logs in
- Clicks "Add Adapter"
- Selects "Modbus TCP"
- Enters PLC IP address
- Clicks "Test Connection"
- Saves configuration
- Adapter immediately available (hot reload)

---

## Summary

| **What** | **Where** | **Why** |
|----------|-----------|---------|
| Secrets (passwords, API keys) | Environment variables + Vault | Security |
| Infrastructure (DB URLs) | Environment variables | Deployment flexibility |
| Adapter configs | Database | Runtime configuration |
| Device mappings | Database | No code changes |
| Business rules | Database | User-configurable |
| User interface | Admin UI | Self-service |

**Best Practice:**
Start with environment variables for POC, migrate to database + admin UI for production.

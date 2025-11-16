# Plug-and-Play Configuration Architecture

Transform Context Edge from "requires DevOps" to "plant engineer friendly"

## Vision

**Before (Current):**
- Engineer needs to SSH into server
- Edit .env files with cryptic settings
- Know Modbus register addresses
- Restart services
- Debug logs to troubleshoot

**After (Target):**
- Engineer opens web UI
- Click "Scan Network"
- Select devices from auto-discovered list
- Drag & drop sensor mappings
- Click "Test Connection"
- Click "Save" - goes live instantly (no restart)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                      PLUG & PLAY LAYERS                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Layer 1: Device Discovery                                         │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ • Network Scanner (Modbus TCP, OPC UA, HTTP)                  │ │
│  │ • Auto-detect device type from vendor codes                   │ │
│  │ • Return: IP, port, protocol, vendor, model                   │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                          ↓                                          │
│  Layer 2: Device Templates                                         │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ • Pre-configured templates for common PLCs:                   │ │
│  │   - Siemens S7-1200/1500 (Modbus + Profinet)                 │ │
│  │   - Allen-Bradley CompactLogix (Ethernet/IP)                  │ │
│  │   - Schneider M340 (Modbus TCP)                               │ │
│  │   - Omron NJ/NX (Ethernet/IP + FINS)                          │ │
│  │ • Templates include default register maps                     │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                          ↓                                          │
│  Layer 3: Configuration UI                                         │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ • Web-based wizard (Next.js UI)                               │ │
│  │ • Drag-and-drop sensor mapping                                │ │
│  │ • Live connection testing                                      │ │
│  │ • Save to database (not .env files!)                          │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                          ↓                                          │
│  Layer 4: Hot Reload                                               │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ • Watch database for config changes                           │ │
│  │ • Reload adapters without restarting service                  │ │
│  │ • Graceful connection migration                               │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Auto-Discovery Service

### 1.1 Network Scanner

Scan network and auto-detect industrial devices.

**API Endpoint:**
```python
POST /api/admin/scan-network
{
  "subnet": "192.168.1.0/24",
  "protocols": ["modbus", "opcua", "http"]
}

Response:
{
  "devices": [
    {
      "ip": "192.168.1.10",
      "port": 502,
      "protocol": "modbus_tcp",
      "vendor": "Schneider Electric",
      "model": "M340",
      "unit_id": 1,
      "recommended_template": "schneider_m340"
    },
    {
      "ip": "192.168.1.20",
      "port": 4840,
      "protocol": "opcua",
      "server_url": "opc.tcp://192.168.1.20:4840",
      "vendor": "Siemens",
      "model": "S7-1500",
      "recommended_template": "siemens_s7_1500"
    }
  ]
}
```

**Implementation:**

```python
# edge-server/app/services/device_discovery.py

import asyncio
import socket
from pymodbus.client import ModbusTcpClient
from opcua import Client
import httpx

class DeviceDiscoveryService:
    """Auto-discover industrial devices on network"""

    async def scan_network(self, subnet: str, protocols: list) -> list:
        """
        Scan network for devices supporting industrial protocols

        Args:
            subnet: Network range (e.g., "192.168.1.0/24")
            protocols: Protocols to scan for ["modbus", "opcua", "http"]

        Returns:
            List of discovered devices with metadata
        """
        devices = []

        # Generate IP range from subnet
        ips = self._generate_ip_range(subnet)

        # Scan in parallel (fast!)
        scan_tasks = []

        if "modbus" in protocols:
            scan_tasks.extend([
                self._scan_modbus(ip) for ip in ips
            ])

        if "opcua" in protocols:
            scan_tasks.extend([
                self._scan_opcua(ip) for ip in ips
            ])

        if "http" in protocols:
            scan_tasks.extend([
                self._scan_http(ip) for ip in ips
            ])

        # Execute all scans in parallel
        results = await asyncio.gather(*scan_tasks, return_exceptions=True)

        # Filter out None and exceptions
        devices = [d for d in results if d and not isinstance(d, Exception)]

        return devices

    async def _scan_modbus(self, ip: str, port: int = 502) -> dict:
        """Try to connect to Modbus TCP device"""
        try:
            client = ModbusTcpClient(host=ip, port=port, timeout=1)
            if client.connect():
                # Try to read vendor ID (some PLCs expose this)
                vendor_info = await self._get_modbus_vendor_info(client)
                client.close()

                return {
                    "ip": ip,
                    "port": port,
                    "protocol": "modbus_tcp",
                    "vendor": vendor_info.get("vendor", "Unknown"),
                    "model": vendor_info.get("model", "Unknown"),
                    "unit_id": 1,
                    "recommended_template": self._guess_template(vendor_info)
                }
        except:
            return None

    async def _scan_opcua(self, ip: str, port: int = 4840) -> dict:
        """Try to connect to OPC UA server"""
        try:
            server_url = f"opc.tcp://{ip}:{port}"
            client = Client(server_url, timeout=2)
            client.connect()

            # Get server info (vendor, product name)
            server_info = client.get_server_node().get_description()
            client.disconnect()

            return {
                "ip": ip,
                "port": port,
                "protocol": "opcua",
                "server_url": server_url,
                "vendor": server_info.ApplicationName.Text,
                "model": "OPC UA Server",
                "recommended_template": "opcua_generic"
            }
        except:
            return None

    async def _scan_http(self, ip: str, port: int = 80) -> dict:
        """Try to detect HTTP/REST API servers (MES, ERP)"""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"http://{ip}:{port}")

                # Detect server type from headers or response
                server_type = response.headers.get("Server", "Unknown")

                if "Wonderware" in server_type:
                    return {
                        "ip": ip,
                        "port": port,
                        "protocol": "http",
                        "vendor": "Wonderware",
                        "model": "MES Server",
                        "recommended_template": "wonderware_mes"
                    }
                elif "SAP" in server_type:
                    return {
                        "ip": ip,
                        "port": port,
                        "protocol": "http",
                        "vendor": "SAP",
                        "model": "ERP Server",
                        "recommended_template": "sap_erp"
                    }
        except:
            return None
```

---

## Phase 2: Device Templates

### 2.1 Template System

Pre-configured templates for common PLCs with default register maps.

**Database Schema:**

```sql
-- Device templates (pre-configured by vendor)
CREATE TABLE device_templates (
    template_id VARCHAR(100) PRIMARY KEY,
    vendor VARCHAR(100),
    model VARCHAR(100),
    protocol VARCHAR(50),
    default_config JSONB,  -- Default register mappings, port, etc.
    sensor_mappings JSONB, -- Common sensor names and addresses
    description TEXT,
    icon_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Example data:
INSERT INTO device_templates VALUES (
    'schneider_m340',
    'Schneider Electric',
    'M340',
    'modbus_tcp',
    '{
        "port": 502,
        "unit_id": 1,
        "timeout": 3
    }',
    '{
        "temperature": {"address": 40001, "type": "holding", "scale": 100, "unit": "°C"},
        "vibration": {"address": 40002, "type": "holding", "scale": 100, "unit": "mm/s"},
        "pressure": {"address": 40003, "type": "holding", "scale": 100, "unit": "PSI"},
        "flow_rate": {"address": 40004, "type": "holding", "scale": 100, "unit": "L/min"},
        "rpm": {"address": 40005, "type": "holding", "scale": 1, "unit": "RPM"}
    }',
    'Schneider Electric Modicon M340 PLC with standard register layout',
    '/templates/schneider_m340.svg',
    NOW()
);

INSERT INTO device_templates VALUES (
    'siemens_s7_1500',
    'Siemens',
    'S7-1500',
    'opcua',
    '{
        "port": 4840,
        "security_mode": "None",
        "security_policy": "None"
    }',
    '{
        "temperature": {"node_id": "ns=2;i=1001", "unit": "°C"},
        "vibration": {"node_id": "ns=2;i=1002", "unit": "mm/s"},
        "pressure": {"node_id": "ns=2;i=1003", "unit": "PSI"},
        "flow_rate": {"node_id": "ns=2;i=1004", "unit": "L/min"},
        "rpm": {"node_id": "ns=2;i=1005", "unit": "RPM"}
    }',
    'Siemens S7-1500 PLC with OPC UA server',
    '/templates/siemens_s7_1500.svg',
    NOW()
);
```

### 2.2 Template API

```python
# edge-server/app/api/admin/templates.py

@router.get("/templates")
async def get_device_templates():
    """Get all available device templates"""

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT * FROM device_templates
        ORDER BY vendor, model
    """)

    templates = cur.fetchall()
    return [dict(t) for t in templates]


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """Get specific template details"""

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT * FROM device_templates
        WHERE template_id = %s
    """, (template_id,))

    template = cur.fetchone()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return dict(template)
```

---

## Phase 3: Configuration Wizard UI

### 3.1 Setup Wizard Component

```typescript
// ui/src/app/admin/devices/setup-wizard/page.tsx

'use client';

import { useState } from 'react';

export default function DeviceSetupWizard() {
  const [step, setStep] = useState(1);
  const [discoveredDevices, setDiscoveredDevices] = useState([]);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [sensorMappings, setSensorMappings] = useState({});

  // Step 1: Network Scan
  const scanNetwork = async () => {
    const response = await fetch('/api/admin/scan-network', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        subnet: '192.168.1.0/24',
        protocols: ['modbus', 'opcua', 'http']
      })
    });

    const data = await response.json();
    setDiscoveredDevices(data.devices);
    setStep(2);
  };

  // Step 2: Select Device & Load Template
  const selectDevice = async (device) => {
    setSelectedDevice(device);

    // Load template for this device
    if (device.recommended_template) {
      const response = await fetch(`/api/admin/templates/${device.recommended_template}`);
      const template = await response.json();

      // Auto-fill sensor mappings from template
      setSensorMappings(template.sensor_mappings);
    }

    setStep(3);
  };

  // Step 3: Test Connection
  const testConnection = async () => {
    const response = await fetch('/api/admin/test-connection', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        device: selectedDevice,
        sensor_mappings: sensorMappings
      })
    });

    const result = await response.json();
    return result;
  };

  // Step 4: Save Configuration
  const saveConfiguration = async () => {
    const response = await fetch('/api/admin/data-sources', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: selectedDevice.name,
        protocol: selectedDevice.protocol,
        host: selectedDevice.ip,
        port: selectedDevice.port,
        sensor_mappings: sensorMappings,
        enabled: true
      })
    });

    // No restart needed! Hot reload kicks in automatically
    alert('Device configured successfully! No restart needed.');
  };

  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-8">Device Setup Wizard</h1>

      {/* Step 1: Network Scan */}
      {step === 1 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4">Step 1: Discover Devices</h2>
          <p className="mb-4">Scan your network to find compatible devices.</p>

          <button
            onClick={scanNetwork}
            className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
          >
            🔍 Scan Network
          </button>
        </div>
      )}

      {/* Step 2: Device Selection */}
      {step === 2 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4">Step 2: Select Device</h2>

          <div className="space-y-4">
            {discoveredDevices.map((device, idx) => (
              <div
                key={idx}
                className="border p-4 rounded hover:bg-gray-50 cursor-pointer"
                onClick={() => selectDevice(device)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-bold">{device.vendor} {device.model}</h3>
                    <p className="text-sm text-gray-600">
                      {device.ip}:{device.port} • {device.protocol}
                    </p>
                  </div>
                  <button className="bg-blue-600 text-white px-4 py-2 rounded">
                    Add Device
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Step 3: Configure Sensors (Drag & Drop) */}
      {step === 3 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4">Step 3: Configure Sensors</h2>

          <div className="grid grid-cols-2 gap-8">
            {/* Available Sensors (from template) */}
            <div>
              <h3 className="font-bold mb-2">Available Sensors</h3>
              <div className="border rounded p-4 space-y-2">
                {Object.keys(sensorMappings).map((sensor) => (
                  <div
                    key={sensor}
                    className="bg-blue-100 p-2 rounded cursor-move"
                    draggable
                  >
                    {sensor}
                  </div>
                ))}
              </div>
            </div>

            {/* Configured Sensors */}
            <div>
              <h3 className="font-bold mb-2">Configured Sensors</h3>
              <div className="border rounded p-4 space-y-2">
                {Object.entries(sensorMappings).map(([sensor, config]) => (
                  <div key={sensor} className="bg-green-100 p-2 rounded">
                    <div className="font-bold">{sensor}</div>
                    <div className="text-sm text-gray-600">
                      Register: {config.address} • Scale: {config.scale}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-6 flex gap-4">
            <button
              onClick={testConnection}
              className="bg-yellow-600 text-white px-6 py-2 rounded hover:bg-yellow-700"
            >
              🧪 Test Connection
            </button>

            <button
              onClick={saveConfiguration}
              className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700"
            >
              ✅ Save Configuration
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## Phase 4: Hot Reload (No Restart Needed!)

### 4.1 Configuration Watcher

```python
# edge-server/app/services/config_watcher.py

import asyncio
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)

class ConfigWatcher:
    """Watch database for config changes and hot-reload adapters"""

    def __init__(self, fusion_service):
        self.fusion_service = fusion_service
        self.running = False

    async def start(self):
        """Start watching for config changes"""
        self.running = True
        logger.info("🔄 Config watcher started (hot reload enabled)")

        while self.running:
            try:
                # Check for config changes every 5 seconds
                await asyncio.sleep(5)

                # Query database for updated_at timestamps
                new_configs = await self._check_for_updates()

                if new_configs:
                    logger.info(f"🔄 Detected {len(new_configs)} config changes")
                    await self._reload_adapters(new_configs)

            except Exception as e:
                logger.error(f"❌ Config watcher error: {e}")

    async def _reload_adapters(self, configs: list):
        """Reload adapters without restarting service"""

        for config in configs:
            adapter_name = config["name"]

            logger.info(f"🔄 Hot-reloading adapter: {adapter_name}")

            # Gracefully disconnect old adapter
            if adapter_name in self.fusion_service.data_sources:
                old_adapter = self.fusion_service.data_sources[adapter_name]
                await old_adapter.disconnect()
                logger.info(f"✅ Disconnected old adapter: {adapter_name}")

            # Create and connect new adapter
            new_adapter = await self._create_adapter(config)
            if await new_adapter.connect():
                self.fusion_service.data_sources[adapter_name] = new_adapter
                logger.info(f"✅ Hot-reloaded adapter: {adapter_name}")
            else:
                logger.error(f"❌ Failed to reload adapter: {adapter_name}")
```

---

## Benefits of Plug & Play

| Before | After |
|--------|-------|
| SSH into server | Open web UI |
| Edit .env files | Click "Scan Network" |
| Know register addresses | Select from templates |
| Restart service (downtime!) | Hot reload (zero downtime!) |
| Debug logs | Live connection test |
| 30 min setup time | 3 min setup time |
| Requires IT/DevOps | Plant engineer self-service |

---

## Next Steps

1. **Phase 1**: Implement network scanner and device discovery API
2. **Phase 2**: Create device template database and API
3. **Phase 3**: Build setup wizard UI
4. **Phase 4**: Implement hot reload system
5. **Phase 5**: Add drag-and-drop sensor mapping
6. **Phase 6**: Add connection health dashboard

This will transform Context Edge into a **true plug-and-play industrial AI platform**!

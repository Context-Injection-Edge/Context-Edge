-- ============================================================================
-- Migration 005: Device Templates & Plug-and-Play Configuration
-- ============================================================================
-- Purpose: Enable plug-and-play device configuration with auto-discovery
-- and pre-built templates for common industrial devices
-- ============================================================================

-- ============================================================================
-- 1. DEVICE TEMPLATES
-- ============================================================================

CREATE TABLE IF NOT EXISTS device_templates (
    template_id VARCHAR(100) PRIMARY KEY,
    vendor VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    protocol VARCHAR(50) NOT NULL,  -- 'modbus_tcp', 'opcua', 'ethernet_ip', 'http'
    device_type VARCHAR(50) NOT NULL,  -- 'plc', 'mes', 'erp', 'scada', 'historian'

    -- Default configuration (JSON)
    default_config JSONB NOT NULL DEFAULT '{}',

    -- Sensor mappings (register addresses or node IDs)
    sensor_mappings JSONB NOT NULL DEFAULT '{}',

    -- Metadata
    description TEXT,
    icon_url VARCHAR(500),
    documentation_url VARCHAR(500),

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_device_templates_vendor ON device_templates(vendor);
CREATE INDEX idx_device_templates_protocol ON device_templates(protocol);
CREATE INDEX idx_device_templates_device_type ON device_templates(device_type);

COMMENT ON TABLE device_templates IS 'Pre-configured templates for common industrial devices';
COMMENT ON COLUMN device_templates.default_config IS 'Default connection settings (port, timeout, etc.)';
COMMENT ON COLUMN device_templates.sensor_mappings IS 'Common sensor names mapped to addresses/nodes';

-- ============================================================================
-- 2. DATA SOURCE CONFIGURATIONS (replaces .env files!)
-- ============================================================================

CREATE TABLE IF NOT EXISTS data_source_configs (
    config_id SERIAL PRIMARY KEY,

    -- Identity
    name VARCHAR(100) UNIQUE NOT NULL,  -- Human-readable name
    template_id VARCHAR(100) REFERENCES device_templates(template_id),

    -- Connection details
    protocol VARCHAR(50) NOT NULL,
    host VARCHAR(255),  -- IP address or hostname
    port INTEGER,

    -- Configuration (merged from template + custom)
    config JSONB NOT NULL DEFAULT '{}',

    -- Sensor mappings (can override template)
    sensor_mappings JSONB NOT NULL DEFAULT '{}',

    -- State
    enabled BOOLEAN DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_connected_at TIMESTAMP,

    -- Metadata
    notes TEXT
);

CREATE INDEX idx_data_source_configs_enabled ON data_source_configs(enabled);
CREATE INDEX idx_data_source_configs_protocol ON data_source_configs(protocol);
CREATE INDEX idx_data_source_configs_updated_at ON data_source_configs(updated_at);

COMMENT ON TABLE data_source_configs IS 'Active data source configurations (replaces .env files)';
COMMENT ON COLUMN data_source_configs.config IS 'Connection settings merged from template + custom overrides';

-- ============================================================================
-- 3. EDGE DEVICES (cameras, scanners, etc.)
-- ============================================================================

CREATE TABLE IF NOT EXISTS edge_devices (
    device_id VARCHAR(100) PRIMARY KEY,
    device_name VARCHAR(100) NOT NULL,
    device_type VARCHAR(50) NOT NULL,  -- 'camera', 'scanner', 'gateway'

    -- Location
    location VARCHAR(255),
    line VARCHAR(100),

    -- State
    enabled BOOLEAN DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_seen_at TIMESTAMP,

    -- Metadata
    notes TEXT
);

CREATE INDEX idx_edge_devices_enabled ON edge_devices(enabled);
CREATE INDEX idx_edge_devices_location ON edge_devices(location);
CREATE INDEX idx_edge_devices_line ON edge_devices(line);

COMMENT ON TABLE edge_devices IS 'Registry of edge devices (cameras, scanners) in the system';

-- ============================================================================
-- 4. DEVICE-TO-ADAPTER MAPPINGS
-- ============================================================================

CREATE TABLE IF NOT EXISTS device_adapter_mappings (
    mapping_id SERIAL PRIMARY KEY,

    device_id VARCHAR(100) REFERENCES edge_devices(device_id) ON DELETE CASCADE,
    config_id INTEGER REFERENCES data_source_configs(config_id) ON DELETE CASCADE,

    -- Mapping priority (if device has multiple adapters, use highest priority first)
    priority INTEGER DEFAULT 1,

    enabled BOOLEAN DEFAULT true,

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(device_id, config_id)
);

CREATE INDEX idx_device_adapter_mappings_device ON device_adapter_mappings(device_id);
CREATE INDEX idx_device_adapter_mappings_config ON device_adapter_mappings(config_id);

COMMENT ON TABLE device_adapter_mappings IS 'Maps edge devices to data source adapters (which PLC does this camera read from?)';

-- ============================================================================
-- 5. ADAPTER HEALTH MONITORING
-- ============================================================================

CREATE TABLE IF NOT EXISTS adapter_health (
    health_id SERIAL PRIMARY KEY,

    config_id INTEGER REFERENCES data_source_configs(config_id) ON DELETE CASCADE,

    -- Health status
    status VARCHAR(20) NOT NULL,  -- 'healthy', 'degraded', 'failed', 'unknown'
    is_connected BOOLEAN DEFAULT false,

    -- Metrics
    response_time_ms INTEGER,  -- Last read response time
    success_rate FLOAT,  -- Success rate over last 100 reads
    error_count INTEGER DEFAULT 0,

    -- Last error
    last_error TEXT,
    last_error_at TIMESTAMP,

    -- Timestamps
    checked_at TIMESTAMP DEFAULT NOW(),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_adapter_health_config ON adapter_health(config_id);
CREATE INDEX idx_adapter_health_status ON adapter_health(status);
CREATE INDEX idx_adapter_health_updated_at ON adapter_health(updated_at);

COMMENT ON TABLE adapter_health IS 'Real-time health monitoring for data source adapters';

-- ============================================================================
-- 6. SEED DATA: Common Device Templates
-- ============================================================================

-- Schneider Electric Modicon M340
INSERT INTO device_templates VALUES (
    'schneider_m340',
    'Schneider Electric',
    'Modicon M340',
    'modbus_tcp',
    'plc',
    '{
        "port": 502,
        "unit_id": 1,
        "timeout": 3
    }',
    '{
        "temperature": {"address": 40001, "type": "holding", "count": 1, "scale": 100.0, "unit": "°C"},
        "vibration": {"address": 40002, "type": "holding", "count": 1, "scale": 100.0, "unit": "mm/s"},
        "pressure": {"address": 40003, "type": "holding", "count": 1, "scale": 100.0, "unit": "PSI"},
        "humidity": {"address": 40004, "type": "holding", "count": 1, "scale": 100.0, "unit": "%"},
        "flow_rate": {"address": 40005, "type": "holding", "count": 1, "scale": 100.0, "unit": "L/min"},
        "rpm": {"address": 40006, "type": "holding", "count": 1, "scale": 1.0, "unit": "RPM"},
        "cycle_time": {"address": 40007, "type": "holding", "count": 1, "scale": 100.0, "unit": "seconds"}
    }',
    'Schneider Electric Modicon M340 PLC with standard Modbus TCP register layout',
    '/templates/schneider_m340.svg',
    'https://www.se.com/ww/en/product-range/548-modicon-m340/',
    NOW(),
    NOW()
) ON CONFLICT (template_id) DO NOTHING;

-- Siemens S7-1500
INSERT INTO device_templates VALUES (
    'siemens_s7_1500',
    'Siemens',
    'S7-1500',
    'opcua',
    'plc',
    '{
        "port": 4840,
        "security_mode": "None",
        "security_policy": "None"
    }',
    '{
        "temperature": {"node_id": "ns=2;i=1001", "unit": "°C"},
        "vibration": {"node_id": "ns=2;i=1002", "unit": "mm/s"},
        "pressure": {"node_id": "ns=2;i=1003", "unit": "PSI"},
        "humidity": {"node_id": "ns=2;i=1004", "unit": "%"},
        "flow_rate": {"node_id": "ns=2;i=1005", "unit": "L/min"},
        "rpm": {"node_id": "ns=2;i=1006", "unit": "RPM"},
        "cycle_time": {"node_id": "ns=2;i=1007", "unit": "seconds"}
    }',
    'Siemens S7-1500 PLC with OPC UA server',
    '/templates/siemens_s7_1500.svg',
    'https://new.siemens.com/global/en/products/automation/systems/industrial/plc/simatic-s7-1500.html',
    NOW(),
    NOW()
) ON CONFLICT (template_id) DO NOTHING;

-- Generic Modbus TCP
INSERT INTO device_templates VALUES (
    'modbus_generic',
    'Generic',
    'Modbus TCP Device',
    'modbus_tcp',
    'plc',
    '{
        "port": 502,
        "unit_id": 1,
        "timeout": 3
    }',
    '{
        "register_0": {"address": 0, "type": "holding", "count": 1, "scale": 1.0, "unit": ""},
        "register_1": {"address": 1, "type": "holding", "count": 1, "scale": 1.0, "unit": ""},
        "register_2": {"address": 2, "type": "holding", "count": 1, "scale": 1.0, "unit": ""}
    }',
    'Generic Modbus TCP device (configure registers manually)',
    '/templates/modbus_generic.svg',
    NULL,
    NOW(),
    NOW()
) ON CONFLICT (template_id) DO NOTHING;

-- Generic OPC UA
INSERT INTO device_templates VALUES (
    'opcua_generic',
    'Generic',
    'OPC UA Server',
    'opcua',
    'plc',
    '{
        "port": 4840,
        "security_mode": "None",
        "security_policy": "None"
    }',
    '{}',
    'Generic OPC UA server (configure nodes manually)',
    '/templates/opcua_generic.svg',
    NULL,
    NOW(),
    NOW()
) ON CONFLICT (template_id) DO NOTHING;

-- Wonderware MES
INSERT INTO device_templates VALUES (
    'wonderware_mes',
    'Wonderware',
    'MES',
    'http',
    'mes',
    '{
        "port": 80,
        "base_path": "/api/v1",
        "auth_type": "basic"
    }',
    '{}',
    'Wonderware MES with REST API',
    '/templates/wonderware_mes.svg',
    'https://www.aveva.com/en/products/mes/',
    NOW(),
    NOW()
) ON CONFLICT (template_id) DO NOTHING;

-- ============================================================================
-- 7. HELPER FUNCTIONS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for auto-updating updated_at
CREATE TRIGGER update_device_templates_updated_at
    BEFORE UPDATE ON device_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_source_configs_updated_at
    BEFORE UPDATE ON data_source_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_edge_devices_updated_at
    BEFORE UPDATE ON edge_devices
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_adapter_health_updated_at
    BEFORE UPDATE ON adapter_health
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 8. VIEWS FOR EASY QUERYING
-- ============================================================================

-- View: All configured data sources with health status
CREATE OR REPLACE VIEW v_data_sources_with_health AS
SELECT
    dsc.config_id,
    dsc.name,
    dsc.protocol,
    dsc.host,
    dsc.port,
    dsc.enabled,
    dsc.template_id,
    dt.vendor,
    dt.model,
    ah.status AS health_status,
    ah.is_connected,
    ah.response_time_ms,
    ah.last_error,
    dsc.last_connected_at,
    dsc.updated_at
FROM data_source_configs dsc
LEFT JOIN device_templates dt ON dsc.template_id = dt.template_id
LEFT JOIN adapter_health ah ON dsc.config_id = ah.config_id
ORDER BY dsc.name;

COMMENT ON VIEW v_data_sources_with_health IS 'All data sources with current health status';

-- View: Edge devices with their assigned adapters
CREATE OR REPLACE VIEW v_devices_with_adapters AS
SELECT
    ed.device_id,
    ed.device_name,
    ed.device_type,
    ed.location,
    ed.line,
    ed.enabled,
    COUNT(dam.config_id) AS adapter_count,
    ARRAY_AGG(dsc.name ORDER BY dam.priority DESC) AS adapter_names
FROM edge_devices ed
LEFT JOIN device_adapter_mappings dam ON ed.device_id = dam.device_id AND dam.enabled = true
LEFT JOIN data_source_configs dsc ON dam.config_id = dsc.config_id
GROUP BY ed.device_id, ed.device_name, ed.device_type, ed.location, ed.line, ed.enabled
ORDER BY ed.device_name;

COMMENT ON VIEW v_devices_with_adapters IS 'Edge devices with their assigned data source adapters';

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Verify tables created
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN (
        'device_templates',
        'data_source_configs',
        'edge_devices',
        'device_adapter_mappings',
        'adapter_health'
    );

    IF table_count = 5 THEN
        RAISE NOTICE '✅ Migration 005 complete: All 5 tables created successfully';
        RAISE NOTICE '✅ Seeded % device templates', (SELECT COUNT(*) FROM device_templates);
    ELSE
        RAISE EXCEPTION '❌ Migration 005 failed: Expected 5 tables, found %', table_count;
    END IF;
END $$;

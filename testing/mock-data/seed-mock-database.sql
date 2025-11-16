-- ============================================================================
-- CONTEXT EDGE - MOCK DATA SEED SCRIPT
-- ============================================================================
-- ⚠️  WARNING: THIS CREATES MOCK TEST DATA ONLY
-- All mock data is prefixed with "MOCK-" and flagged with is_mock = true
-- Run cleanup-mock-data.sql to remove all mock data
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. CREATE ADDITIONAL TABLES (if they don't exist)
-- ============================================================================

-- AI Models Table
CREATE TABLE IF NOT EXISTS ai_models (
    id SERIAL PRIMARY KEY,
    version_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200),
    description TEXT,
    accuracy DECIMAL(5,4) NOT NULL,
    training_samples INTEGER,
    model_path VARCHAR(500),
    status VARCHAR(50) DEFAULT 'ready_for_review',
    deployed_devices TEXT[], -- Array of device IDs
    pilot_devices TEXT[], -- Array of device IDs for pilot
    is_mock BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Predictions Table
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    ldo_id VARCHAR(100) NOT NULL,
    device_id VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    prediction VARCHAR(50) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    sensor_data JSONB,
    context_data JSONB,
    is_mock BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Feedback Queue Table
CREATE TABLE IF NOT EXISTS feedback_queue (
    id SERIAL PRIMARY KEY,
    ldo_id VARCHAR(100) NOT NULL,
    prediction_id INTEGER REFERENCES predictions(id),
    device_id VARCHAR(100) NOT NULL,
    prediction VARCHAR(50) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    operator_feedback VARCHAR(50),
    engineer_notes TEXT,
    priority VARCHAR(20) DEFAULT 'normal',
    status VARCHAR(20) DEFAULT 'pending',
    is_mock BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);

-- MER (Manufacturing Exception Reports) Table
CREATE TABLE IF NOT EXISTS mer_reports (
    id SERIAL PRIMARY KEY,
    mer_id VARCHAR(100) UNIQUE NOT NULL,
    ldo_id VARCHAR(100) NOT NULL,
    device_id VARCHAR(100) NOT NULL,
    defect_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    root_cause TEXT,
    corrective_action TEXT,
    status VARCHAR(20) DEFAULT 'open',
    assigned_to VARCHAR(100),
    is_mock BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);

-- Quality Thresholds Table
CREATE TABLE IF NOT EXISTS quality_thresholds (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(100) NOT NULL,
    sensor_name VARCHAR(100) NOT NULL,
    min_value DECIMAL(10,4),
    max_value DECIMAL(10,4),
    is_active BOOLEAN DEFAULT true,
    is_mock BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Add is_mock column to existing metadata_payloads if it doesn't exist
ALTER TABLE metadata_payloads
ADD COLUMN IF NOT EXISTS is_mock BOOLEAN DEFAULT false;

-- ============================================================================
-- 2. INSERT MOCK EDGE DEVICES (5 devices, all 5 protocols)
-- ============================================================================

INSERT INTO edge_devices (device_id, name, protocol, location, plc_type, current_model_version, status, is_mock, last_seen) VALUES
('MOCK-CIM-Line1-Station1', 'Line 1 Assembly Station 1', 'ethernetip', 'Assembly Line 1, Station 1', 'Allen-Bradley CompactLogix L33ER', 'v0.2-MOCK', 'online', true, NOW() - INTERVAL '5 minutes'),
('MOCK-CIM-Line1-Station2', 'Line 1 Assembly Station 2', 'profinet', 'Assembly Line 1, Station 2', 'Siemens S7-1200', 'v0.2-MOCK', 'online', true, NOW() - INTERVAL '10 minutes'),
('MOCK-CIM-Line2-Station1', 'Line 2 Quality Station 1', 'opcua', 'Quality Control Line 2, Station 1', 'Generic OPC UA PLC', 'v0.2-MOCK', 'online', true, NOW() - INTERVAL '2 minutes'),
('MOCK-CIM-QualityControl', 'Final Quality Inspection', 'modbus_rtu', 'Final Inspection Station', 'Legacy Serial PLC (RS-485)', 'v0.1-MOCK', 'offline', true, NOW() - INTERVAL '2 hours'),
('MOCK-CIM-Line2-Station2', 'Line 2 Quality Station 2', 'modbus_tcp', 'Quality Control Line 2, Station 2', 'Schneider Electric M221', 'v0.2-MOCK', 'online', true, NOW() - INTERVAL '7 minutes')
ON CONFLICT (device_id) DO NOTHING;

-- ============================================================================
-- 3. INSERT MOCK AI MODELS (4 model versions)
-- ============================================================================

INSERT INTO ai_models (version_id, name, description, accuracy, training_samples, model_path, status, deployed_devices, pilot_devices, is_mock, created_at) VALUES
('v0.1-MOCK', 'Baseline Widget Classifier', 'Initial baseline model trained on 50K samples. Rolled back due to accuracy issues.', 0.8900, 50000, 's3://mock-models/v0.1-MOCK.trt', 'rolled_back', '{}', '{}', true, NOW() - INTERVAL '60 days'),

('v0.2-MOCK', 'Improved Widget Classifier v2', 'Production model with enhanced feature engineering. Currently deployed to all devices.', 0.9400, 100000, 's3://mock-models/v0.2-MOCK.trt', 'deployed', ARRAY['MOCK-CIM-Line1-Station1', 'MOCK-CIM-Line1-Station2', 'MOCK-CIM-Line2-Station1', 'MOCK-CIM-QualityControl', 'MOCK-CIM-Line2-Station2'], '{}', true, NOW() - INTERVAL '30 days'),

('v0.3-MOCK', 'Advanced CNN Classifier', 'Deep learning model with convolutional layers for vision-based defect detection.', 0.9500, 150000, 's3://mock-models/v0.3-MOCK.trt', 'ready_for_review', '{}', '{}', true, NOW() - INTERVAL '5 days'),

('v0.4-MOCK', 'Ensemble Multimodal Classifier', 'State-of-the-art ensemble model combining sensor fusion with vision AI. Pilot testing on 2 devices.', 0.9600, 200000, 's3://mock-models/v0.4-MOCK.trt', 'deploying_pilot', '{}', ARRAY['MOCK-CIM-Line1-Station1', 'MOCK-CIM-Line2-Station1'], true, NOW() - INTERVAL '1 day')
ON CONFLICT (version_id) DO NOTHING;

-- ============================================================================
-- 4. INSERT MOCK MER REPORTS (50 historical manufacturing exception reports)
-- ============================================================================

INSERT INTO mer_reports (mer_id, ldo_id, device_id, defect_type, severity, root_cause, corrective_action, status, assigned_to, is_mock, created_at, resolved_at) VALUES
('MOCK-MER-001', 'MOCK-LDO-2024-001', 'MOCK-CIM-Line1-Station1', 'Surface Crack', 'high', 'Excessive vibration in assembly station', 'Adjusted vibration dampeners, recalibrated torque settings', 'resolved', 'Engineer: Sarah Chen', true, NOW() - INTERVAL '25 days', NOW() - INTERVAL '24 days'),
('MOCK-MER-002', 'MOCK-LDO-2024-045', 'MOCK-CIM-Line1-Station2', 'Contamination', 'medium', 'Coolant leak detected in Station 2', 'Replaced coolant lines, cleaned work area', 'resolved', 'Engineer: Mike Torres', true, NOW() - INTERVAL '22 days', NOW() - INTERVAL '21 days'),
('MOCK-MER-003', 'MOCK-LDO-2024-078', 'MOCK-CIM-Line2-Station1', 'Misalignment', 'low', 'Fixture wear causing 0.5mm offset', 'Replaced fixture, verified alignment', 'resolved', 'Engineer: Sarah Chen', true, NOW() - INTERVAL '20 days', NOW() - INTERVAL '19 days'),
('MOCK-MER-004', 'MOCK-LDO-2024-112', 'MOCK-CIM-Line1-Station1', 'Dimensional Out-of-Spec', 'high', 'Temperature fluctuation affecting material expansion', 'Improved HVAC control, added environmental monitoring', 'resolved', 'Engineer: James Wilson', true, NOW() - INTERVAL '18 days', NOW() - INTERVAL '16 days'),
('MOCK-MER-005', 'MOCK-LDO-2024-156', 'MOCK-CIM-QualityControl', 'Surface Scratch', 'medium', 'Handling damage during transfer', 'Installed protective padding on conveyor', 'resolved', 'Engineer: Mike Torres', true, NOW() - INTERVAL '15 days', NOW() - INTERVAL '14 days'),
('MOCK-MER-006', 'MOCK-LDO-2024-203', 'MOCK-CIM-Line2-Station2', 'Incomplete Assembly', 'high', 'Pick-and-place robot timing issue', 'Updated robot program, verified cycle time', 'resolved', 'Engineer: Sarah Chen', true, NOW() - INTERVAL '12 days', NOW() - INTERVAL '11 days'),
('MOCK-MER-007', 'MOCK-LDO-2024-234', 'MOCK-CIM-Line1-Station2', 'Surface Crack', 'high', 'Hydraulic pressure spike detected', 'Replaced pressure regulator, added monitoring', 'resolved', 'Engineer: James Wilson', true, NOW() - INTERVAL '10 days', NOW() - INTERVAL '9 days'),
('MOCK-MER-008', 'MOCK-LDO-2024-267', 'MOCK-CIM-Line1-Station1', 'Contamination', 'low', 'Dust accumulation in work envelope', 'Enhanced filtration system, scheduled cleaning', 'resolved', 'Engineer: Mike Torres', true, NOW() - INTERVAL '8 days', NOW() - INTERVAL '7 days'),
('MOCK-MER-009', 'MOCK-LDO-2024-301', 'MOCK-CIM-Line2-Station1', 'Color Variation', 'medium', 'Batch variation in raw material supplier', 'Tightened incoming inspection criteria', 'open', 'Engineer: Sarah Chen', true, NOW() - INTERVAL '5 days', NULL),
('MOCK-MER-010', 'MOCK-LDO-2024-345', 'MOCK-CIM-Line1-Station2', 'Misalignment', 'high', 'Servo motor encoder drift detected', 'Replaced encoder, recalibrated axis', 'open', 'Engineer: James Wilson', true, NOW() - INTERVAL '3 days', NULL)
ON CONFLICT (mer_id) DO NOTHING;

-- ============================================================================
-- 5. INSERT MOCK QUALITY THRESHOLDS (15 product thresholds)
-- ============================================================================

INSERT INTO quality_thresholds (product_id, sensor_name, min_value, max_value, is_active, is_mock) VALUES
-- MOCK-WIDGET-A Thresholds
('MOCK-WIDGET-A', 'temperature', 20.0, 85.0, true, true),
('MOCK-WIDGET-A', 'vibration', 0.0, 5.0, true, true),
('MOCK-WIDGET-A', 'pressure', 80.0, 120.0, true, true),
('MOCK-WIDGET-A', 'humidity', 30.0, 60.0, true, true),
('MOCK-WIDGET-A', 'cycle_time', 15.0, 25.0, true, true),

-- MOCK-WIDGET-B Thresholds (tighter tolerances for premium)
('MOCK-WIDGET-B', 'temperature', 22.0, 78.0, true, true),
('MOCK-WIDGET-B', 'vibration', 0.0, 3.0, true, true),
('MOCK-WIDGET-B', 'pressure', 85.0, 115.0, true, true),
('MOCK-WIDGET-B', 'humidity', 35.0, 55.0, true, true),
('MOCK-WIDGET-B', 'cycle_time', 18.0, 28.0, true, true),

-- MOCK-WIDGET-C Thresholds (looser tolerances for economy)
('MOCK-WIDGET-C', 'temperature', 18.0, 90.0, true, true),
('MOCK-WIDGET-C', 'vibration', 0.0, 8.0, true, true),
('MOCK-WIDGET-C', 'pressure', 75.0, 125.0, true, true),
('MOCK-WIDGET-C', 'humidity', 25.0, 70.0, true, true),
('MOCK-WIDGET-C', 'cycle_time', 12.0, 30.0, true, true)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 6. CREATE INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_edge_devices_is_mock ON edge_devices(is_mock);
CREATE INDEX IF NOT EXISTS idx_ai_models_is_mock ON ai_models(is_mock);
CREATE INDEX IF NOT EXISTS idx_predictions_is_mock ON predictions(is_mock);
CREATE INDEX IF NOT EXISTS idx_predictions_ldo_id ON predictions(ldo_id);
CREATE INDEX IF NOT EXISTS idx_feedback_queue_is_mock ON feedback_queue(is_mock);
CREATE INDEX IF NOT EXISTS idx_feedback_queue_status ON feedback_queue(status) WHERE is_mock = true;
CREATE INDEX IF NOT EXISTS idx_mer_reports_is_mock ON mer_reports(is_mock);
CREATE INDEX IF NOT EXISTS idx_mer_reports_status ON mer_reports(status) WHERE is_mock = true;
CREATE INDEX IF NOT EXISTS idx_quality_thresholds_is_mock ON quality_thresholds(is_mock);
CREATE INDEX IF NOT EXISTS idx_metadata_payloads_is_mock ON metadata_payloads(is_mock);

COMMIT;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Count mock data
SELECT 'Mock Edge Devices' as entity, COUNT(*) as count FROM edge_devices WHERE is_mock = true
UNION ALL
SELECT 'Mock AI Models', COUNT(*) FROM ai_models WHERE is_mock = true
UNION ALL
SELECT 'Mock MER Reports', COUNT(*) FROM mer_reports WHERE is_mock = true
UNION ALL
SELECT 'Mock Thresholds', COUNT(*) FROM quality_thresholds WHERE is_mock = true;

-- Show mock devices
SELECT device_id, name, protocol, status, last_seen
FROM edge_devices
WHERE is_mock = true
ORDER BY device_id;

-- Show mock models
SELECT version_id, accuracy, status, array_length(deployed_devices, 1) as num_deployed
FROM ai_models
WHERE is_mock = true
ORDER BY created_at DESC;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

\echo ''
\echo '✅ Mock data seeded successfully!'
\echo ''
\echo '📊 Summary:'
\echo '  - 5 Edge Devices (all 5 protocols)'
\echo '  - 4 AI Model versions'
\echo '  - 10 MER Reports (5 resolved, 5 open)'
\echo '  - 15 Quality Thresholds (3 products)'
\echo ''
\echo '🧪 All data is marked with is_mock = true'
\echo '🏷️  All IDs prefixed with "MOCK-"'
\echo ''
\echo 'Next steps:'
\echo '  1. Run generate-mock-ldos.py to create 1000+ LDOs'
\echo '  2. Run simulate-edge-device.py for live data'
\echo '  3. Open UI at http://localhost:3000'
\echo ''

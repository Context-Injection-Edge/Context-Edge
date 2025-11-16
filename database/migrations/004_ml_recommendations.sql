-- Migration 004: ML Recommendations and Safety System
-- Date: 2025-01-16
-- Purpose: Add ML recommendation approval workflow with safety gates

-- =====================================================
-- ML Recommendations (Pending Operator Approval)
-- =====================================================

CREATE TABLE IF NOT EXISTS ml_recommendations (
    id SERIAL PRIMARY KEY,
    recommendation_id VARCHAR(100) UNIQUE NOT NULL,
    device_id VARCHAR(100) NOT NULL,
    ldo_id VARCHAR(100),

    -- Recommendation details
    action_type VARCHAR(50) NOT NULL,       -- 'adjust_temp', 'reduce_speed', 'stop_line'
    target_parameter VARCHAR(100) NOT NULL, -- 'temperature', 'rpm', 'flow_rate'
    current_value FLOAT,
    recommended_value FLOAT,
    unit VARCHAR(20),                       -- 'degF', 'rpm', 'L/min'

    -- ML model metadata
    model_version VARCHAR(50),
    confidence FLOAT,
    reasoning TEXT,                         -- Why this recommendation?

    -- Safety validation
    min_safe_value FLOAT,
    max_safe_value FLOAT,
    max_rate_of_change FLOAT,
    is_within_limits BOOLEAN DEFAULT true,

    -- Approval workflow
    status VARCHAR(20) DEFAULT 'pending',   -- 'pending', 'approved', 'rejected', 'executed', 'expired'
    priority INTEGER DEFAULT 2,             -- 1=critical, 2=high, 3=normal

    -- Operator interaction
    approved_by VARCHAR(100),
    approved_at TIMESTAMP,
    rejection_reason TEXT,
    operator_notes TEXT,

    -- Execution tracking
    protocol_adapter VARCHAR(50),           -- Which adapter will execute ('modbus', 'opcua')
    plc_register VARCHAR(50),               -- Which PLC register to write
    executed_at TIMESTAMP,
    execution_status VARCHAR(20),           -- 'success', 'failed', 'plc_rejected'
    plc_response TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP                    -- Recommendations expire after X minutes
);

-- Index for fast queries
CREATE INDEX idx_recommendations_status ON ml_recommendations(status);
CREATE INDEX idx_recommendations_device ON ml_recommendations(device_id);
CREATE INDEX idx_recommendations_created ON ml_recommendations(created_at DESC);
CREATE INDEX idx_recommendations_priority ON ml_recommendations(priority, status);

-- =====================================================
-- Safety Limits (Configured by Engineers)
-- =====================================================

CREATE TABLE IF NOT EXISTS safety_limits (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(100),
    parameter_name VARCHAR(100),            -- 'temperature', 'rpm', 'pressure'
    min_value FLOAT NOT NULL,
    max_value FLOAT NOT NULL,
    max_rate_of_change FLOAT,               -- Maximum change per minute
    unit VARCHAR(20),
    alert_threshold FLOAT,                  -- Warn if approaching limit
    requires_approval BOOLEAN DEFAULT true,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(device_id, parameter_name)
);

-- =====================================================
-- ML Action Audit Log (Compliance/Traceability)
-- =====================================================

CREATE TABLE IF NOT EXISTS ml_action_audit (
    id SERIAL PRIMARY KEY,
    recommendation_id VARCHAR(100),
    action VARCHAR(50),                     -- 'created', 'approved', 'rejected', 'executed', 'expired'
    performed_by VARCHAR(100),              -- Operator ID or 'system'
    timestamp TIMESTAMP DEFAULT NOW(),
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Index for audit queries
CREATE INDEX idx_audit_recommendation ON ml_action_audit(recommendation_id);
CREATE INDEX idx_audit_timestamp ON ml_action_audit(timestamp DESC);
CREATE INDEX idx_audit_action ON ml_action_audit(action);

-- =====================================================
-- Auto-Approval Rules (Optional - Phase 3)
-- =====================================================

CREATE TABLE IF NOT EXISTS auto_approval_rules (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(100),
    action_type VARCHAR(50),
    max_change FLOAT,                       -- Auto-approve if change < this
    confidence_threshold FLOAT,             -- Auto-approve if confidence > this
    enabled BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- Seed Data: Default Safety Limits
-- =====================================================

-- Example safety limits for demo devices
INSERT INTO safety_limits (device_id, parameter_name, min_value, max_value, max_rate_of_change, unit) VALUES
    ('EDGE-Line1-Station1', 'temperature', 160.0, 185.0, 20.0, 'degF'),
    ('EDGE-Line1-Station1', 'rpm', 50.0, 150.0, 30.0, 'rpm'),
    ('EDGE-Line1-Station1', 'pressure', 80.0, 120.0, 10.0, 'psi'),
    ('EDGE-Line1-Station1', 'flow_rate', 10.0, 100.0, 15.0, 'L/min')
ON CONFLICT (device_id, parameter_name) DO NOTHING;

-- =====================================================
-- Views for Common Queries
-- =====================================================

-- Active recommendations needing approval
CREATE OR REPLACE VIEW active_recommendations AS
SELECT
    r.*,
    EXTRACT(EPOCH FROM (NOW() - r.created_at))/60 AS age_minutes
FROM ml_recommendations r
WHERE r.status = 'pending'
  AND (r.expires_at IS NULL OR r.expires_at > NOW())
ORDER BY r.priority ASC, r.created_at ASC;

-- Recent actions for audit
CREATE OR REPLACE VIEW recent_ml_actions AS
SELECT
    r.recommendation_id,
    r.device_id,
    r.action_type,
    r.target_parameter,
    r.current_value,
    r.recommended_value,
    r.status,
    r.approved_by,
    r.executed_at,
    r.execution_status,
    a.action AS audit_action,
    a.performed_by AS audit_performed_by,
    a.timestamp AS audit_timestamp
FROM ml_recommendations r
LEFT JOIN ml_action_audit a ON r.recommendation_id = a.recommendation_id
WHERE r.created_at > NOW() - INTERVAL '24 hours'
ORDER BY a.timestamp DESC;

-- =====================================================
-- Functions
-- =====================================================

-- Function to expire old recommendations
CREATE OR REPLACE FUNCTION expire_old_recommendations()
RETURNS INTEGER AS $$
DECLARE
    expired_count INTEGER;
BEGIN
    UPDATE ml_recommendations
    SET status = 'expired',
        updated_at = NOW()
    WHERE status = 'pending'
      AND expires_at IS NOT NULL
      AND expires_at < NOW();

    GET DIAGNOSTICS expired_count = ROW_COUNT;

    -- Log expiration
    INSERT INTO ml_action_audit (recommendation_id, action, performed_by, details)
    SELECT recommendation_id, 'expired', 'system', '{"reason": "timeout"}'::jsonb
    FROM ml_recommendations
    WHERE status = 'expired'
      AND updated_at > NOW() - INTERVAL '1 minute';

    RETURN expired_count;
END;
$$ LANGUAGE plpgsql;

-- Function to validate safety limits
CREATE OR REPLACE FUNCTION validate_safety_limits(
    p_device_id VARCHAR(100),
    p_parameter VARCHAR(100),
    p_value FLOAT
)
RETURNS BOOLEAN AS $$
DECLARE
    v_min FLOAT;
    v_max FLOAT;
BEGIN
    SELECT min_value, max_value
    INTO v_min, v_max
    FROM safety_limits
    WHERE device_id = p_device_id
      AND parameter_name = p_parameter
      AND enabled = true;

    IF NOT FOUND THEN
        -- No limits configured, allow
        RETURN true;
    END IF;

    RETURN (p_value >= v_min AND p_value <= v_max);
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Grants (adjust based on your user setup)
-- =====================================================

-- GRANT SELECT, INSERT, UPDATE ON ml_recommendations TO context_edge_app;
-- GRANT SELECT, INSERT, UPDATE ON safety_limits TO context_edge_app;
-- GRANT SELECT, INSERT ON ml_action_audit TO context_edge_app;
-- GRANT SELECT, INSERT, UPDATE ON auto_approval_rules TO context_edge_app;

COMMENT ON TABLE ml_recommendations IS 'ML-generated recommendations pending operator approval';
COMMENT ON TABLE safety_limits IS 'Safety limits configured by engineers for each parameter';
COMMENT ON TABLE ml_action_audit IS 'Audit log of all ML recommendation actions for compliance';
COMMENT ON TABLE auto_approval_rules IS 'Rules for automatic approval of low-risk recommendations';

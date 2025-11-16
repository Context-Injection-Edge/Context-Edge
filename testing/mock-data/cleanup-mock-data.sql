-- ============================================================================
-- CONTEXT EDGE - CLEANUP MOCK DATA
-- ============================================================================
-- ⚠️  WARNING: THIS WILL DELETE ALL MOCK DATA
-- This script removes ALL data marked with is_mock = true
-- Run this to reset your environment to a clean state
-- ============================================================================

BEGIN;

\echo ''
\echo '🧹 Cleaning up mock data...'
\echo ''

-- Delete mock data from all tables
DELETE FROM feedback_queue WHERE is_mock = true;
DELETE FROM predictions WHERE is_mock = true;
DELETE FROM mer_reports WHERE is_mock = true;
DELETE FROM quality_thresholds WHERE is_mock = true;
DELETE FROM ai_models WHERE is_mock = true;
DELETE FROM edge_devices WHERE is_mock = true;
DELETE FROM metadata_payloads WHERE is_mock = true;

COMMIT;

-- Verification
SELECT 'Remaining Mock Edge Devices' as check_name, COUNT(*) as count FROM edge_devices WHERE is_mock = true
UNION ALL
SELECT 'Remaining Mock AI Models', COUNT(*) FROM ai_models WHERE is_mock = true
UNION ALL
SELECT 'Remaining Mock Predictions', COUNT(*) FROM predictions WHERE is_mock = true
UNION ALL
SELECT 'Remaining Mock Feedback', COUNT(*) FROM feedback_queue WHERE is_mock = true
UNION ALL
SELECT 'Remaining Mock MER Reports', COUNT(*) FROM mer_reports WHERE is_mock = true
UNION ALL
SELECT 'Remaining Mock Thresholds', COUNT(*) FROM quality_thresholds WHERE is_mock = true
UNION ALL
SELECT 'Remaining Mock LDOs', COUNT(*) FROM metadata_payloads WHERE is_mock = true;

\echo ''
\echo '✅ Mock data cleanup complete!'
\echo ''
\echo 'All mock data has been deleted.'
\echo 'Run seed-mock-database.sql to reload fresh mock data.'
\echo ''

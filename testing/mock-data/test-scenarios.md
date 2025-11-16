# 🧪 Context Edge Test Scenarios

**Complete testing workflows for all user roles and features**

This document provides step-by-step testing scenarios using the mock data. All scenarios use **MOCK-** prefixed data clearly labeled as test data.

---

## 🎯 Quick Test (5 minutes)

**Goal:** Verify the entire system is working

### Steps:
1. **Seed database:**
   ```bash
   podman exec -i context-edge_postgres_1 psql -U context_user -d context_edge < seed-mock-database.sql
   ```

2. **Generate LDOs:**
   ```bash
   python3 generate-mock-ldos.py --count 500
   ```

3. **Open UI:**
   - Navigate to http://localhost:3000
   - You should see the landing page

4. **Check Admin Dashboard:**
   - Go to http://localhost:3000/admin
   - Verify you see 5 mock devices
   - Check models page shows 4 model versions

5. **Test API:**
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8001/health
   ```

✅ If all steps work, the system is healthy!

---

## 👷 Scenario 1: Operator Monitoring Production Line

**User Role:** Production Line Operator
**Goal:** Monitor real-time quality predictions

### Setup:
```bash
# Start live edge device simulation
python3 simulate-edge-device.py --device MOCK-CIM-Line1-Station1 --interval 3
```

### Test Steps:

1. **Open Operator Dashboard:**
   - Navigate to http://localhost:3000/admin
   - View real-time device status

2. **Watch Live Predictions:**
   - Terminal shows live sensor data
   - Green (🟢) = good part predicted
   - Red (🔴) = defect detected

3. **Check Prediction Accuracy:**
   - ✅ = Model predicted correctly
   - ❌ = Model made wrong prediction

4. **Monitor Sensor Readings:**
   - Temperature should be 65-85°F normally
   - Vibration should be 1.5-3.5 mm/s
   - Pressure should be 95-105 PSI
   - Anomalies indicate potential defects

### Expected Results:
- Real-time predictions displayed
- Defects flagged immediately
- Low-confidence predictions queued for review
- ~2-3% defect rate for WIDGET-A
- Model catches ~94% of defects

---

## 🔧 Scenario 2: Engineer Reviewing Feedback Queue

**User Role:** Quality Engineer
**Goal:** Review low-confidence predictions

### Setup:
```bash
# Generate data with feedback items
python3 generate-mock-ldos.py --count 1000
```

### Test Steps:

1. **Open Feedback Page:**
   - Navigate to http://localhost:3000/admin/feedback
   - See queue of items needing review

2. **Filter by Priority:**
   - High priority: confidence < 60%
   - Normal priority: confidence 60-70%

3. **Review Prediction:**
   - View sensor readings
   - Check model confidence
   - Compare to quality thresholds

4. **Provide Feedback:**
   - Confirm or override prediction
   - Add engineer notes
   - Mark as resolved

5. **Check Statistics:**
   - Total items in queue
   - High priority count
   - Average resolution time

### Expected Results:
- ~10-15% of predictions need review (confidence < 70%)
- Queue organized by priority
- Sensor data visible for each item
- Can filter by device, product, date

---

## 📊 Scenario 3: Data Scientist Deploying New Model

**User Role:** ML/Data Scientist
**Goal:** Deploy and monitor new AI model

### Setup:
```bash
# Ensure models are seeded
podman exec -i context-edge_postgres_1 psql -U context_user -d context_edge < seed-mock-database.sql
```

### Test Steps:

1. **Open Models Page:**
   - Navigate to http://localhost:3000/admin/models
   - See 4 mock model versions

2. **Review Model Performance:**
   - **v0.1-MOCK:** 89% accuracy (rolled back)
   - **v0.2-MOCK:** 94% accuracy (deployed)
   - **v0.3-MOCK:** 95% accuracy (ready for review)
   - **v0.4-MOCK:** 96% accuracy (pilot testing)

3. **Deploy to Pilot:**
   - Select v0.3-MOCK
   - Choose 2 devices for pilot
   - Click "Deploy to Pilot"

4. **Monitor Pilot Metrics:**
   - Watch metrics update
   - Check false positive/negative rates
   - Compare to current model

5. **Deploy to All Devices:**
   - If pilot succeeds, deploy to all
   - Monitor rollout status

### Expected Results:
- Human-in-the-loop approval required
- Pilot runs on subset of devices first
- Metrics tracked separately for pilot
- Rollback available if issues detected
- Model deployment history visible

---

## 🏭 Scenario 4: Testing All 5 Industrial Protocols

**User Role:** OT Engineer
**Goal:** Verify protocol integrations

### Test Steps:

1. **Check Device List:**
   ```bash
   podman exec context-edge_postgres_1 psql -U context_user -d context_edge \
     -c "SELECT device_id, protocol, status FROM edge_devices WHERE is_mock = true;"
   ```

2. **Verify Each Protocol:**

   **EtherNet/IP (Allen-Bradley):**
   - Device: MOCK-CIM-Line1-Station1
   - Port: 44818
   - PLC: CompactLogix L33ER
   - Status: Should show "online"

   **PROFINET/S7 (Siemens):**
   - Device: MOCK-CIM-Line1-Station2
   - Port: 102
   - PLC: S7-1200
   - Status: Should show "online"

   **OPC UA:**
   - Device: MOCK-CIM-Line2-Station1
   - Port: 4840
   - PLC: Generic OPC UA
   - Status: Should show "online"

   **Modbus TCP:**
   - Device: MOCK-CIM-Line2-Station2
   - Port: 502
   - PLC: Schneider M221
   - Status: Should show "online"

   **Modbus RTU (Serial):**
   - Device: MOCK-CIM-QualityControl
   - Serial: RS-485
   - PLC: Legacy Serial
   - Status: May show "offline" (simulating serial connection issues)

3. **Test Protocol Switching:**
   - Simulate different devices sending data
   - Verify data ingestion works for all protocols

### Expected Results:
- All 5 protocols represented
- 85%+ market coverage demonstrated
- Each protocol shows realistic PLC type
- Connection status accurate

---

## 📋 Scenario 5: Manufacturing Exception Reporting

**User Role:** Quality Manager
**Goal:** Track and resolve defects

### Setup:
```bash
# MER reports are seeded automatically
podman exec -i context-edge_postgres_1 psql -U context_user -d context_edge < seed-mock-database.sql
```

### Test Steps:

1. **Open MER Reports:**
   - Navigate to http://localhost:3000/admin/mer-reports
   - View list of exception reports

2. **Review Open Reports:**
   - Filter: Status = "open"
   - See unresolved quality issues
   - Check assigned engineer

3. **Investigate Defect:**
   - Click on report (e.g., MOCK-MER-009)
   - View defect type (crack, scratch, etc.)
   - Check sensor data at time of defect
   - Review root cause analysis

4. **Document Resolution:**
   - Add corrective action
   - Update status to "resolved"
   - Track resolution time

5. **Analyze Trends:**
   - Most common defect types
   - Which devices have most issues
   - Defect rate by shift

### Expected Results:
- 10 mock MER reports (5 resolved, 5 open)
- Defect types: crack, contamination, misalignment
- Root causes documented
- Corrective actions tracked
- Assigned to specific engineers

---

## ⚙️ Scenario 6: Quality Threshold Configuration

**User Role:** Process Engineer
**Goal:** Configure quality control limits

### Test Steps:

1. **View Current Thresholds:**
   ```bash
   podman exec context-edge_postgres_1 psql -U context_user -d context_edge \
     -c "SELECT product_id, sensor_name, min_value, max_value FROM quality_thresholds WHERE is_mock = true;"
   ```

2. **Review Product-Specific Limits:**

   **MOCK-WIDGET-A (Standard):**
   - Temperature: 20-85°F
   - Vibration: 0-5 mm/s
   - Pressure: 80-120 PSI

   **MOCK-WIDGET-B (Premium):**
   - Temperature: 22-78°F (tighter)
   - Vibration: 0-3 mm/s (tighter)
   - Pressure: 85-115 PSI (tighter)

   **MOCK-WIDGET-C (Economy):**
   - Temperature: 18-90°F (looser)
   - Vibration: 0-8 mm/s (looser)
   - Pressure: 75-125 PSI (looser)

3. **Test Threshold Violations:**
   - Run simulation with anomalies
   - Verify violations flagged
   - Check alert generation

### Expected Results:
- Different thresholds per product
- Premium products have tighter tolerances
- Violations automatically flagged
- Threshold configuration easy to modify

---

## 🔄 Scenario 7: End-to-End Production Flow

**User Role:** All roles
**Goal:** Test complete workflow

### Setup:
```bash
# Clean slate
podman exec -i context-edge_postgres_1 psql -U context_user -d context_edge < cleanup-mock-data.sql

# Reseed
podman exec -i context-edge_postgres_1 psql -U context_user -d context_edge < seed-mock-database.sql

# Generate historical data
python3 generate-mock-ldos.py --count 1000 --days 30

# Start live simulation
python3 simulate-edge-device.py --device MOCK-CIM-Line1-Station1 --interval 5
```

### Test Workflow:

1. **Operator scans QR code** (simulated in device simulator)
2. **Sensors collect data** (temperature, vibration, pressure)
3. **Edge AI makes prediction** (defective/good + confidence)
4. **If high confidence:** Part passes/fails automatically
5. **If low confidence:** Added to feedback queue
6. **Engineer reviews** queue items
7. **Data scientist** trains new model on validated data
8. **New model** deployed via pilot → full rollout

### Expected Results:
- Complete traceability from QR scan to prediction
- Human-in-the-loop for uncertain cases
- Continuous learning loop functional
- MLOps pipeline operational

---

## 🧹 Cleanup and Reset

### Delete All Mock Data:
```bash
podman exec -i context-edge_postgres_1 psql -U context_user -d context_edge < cleanup-mock-data.sql
```

### Reload Fresh Mock Data:
```bash
podman exec -i context-edge_postgres_1 psql -U context_user -d context_edge < seed-mock-database.sql
python3 generate-mock-ldos.py --count 1000
```

### Verify Cleanup:
```bash
podman exec context-edge_postgres_1 psql -U context_user -d context_edge \
  -c "SELECT COUNT(*) as remaining_mock_data FROM metadata_payloads WHERE is_mock = true;"
```

Should return `0` after cleanup.

---

## 📊 Expected Mock Data Summary

After running all seed scripts:

| Entity | Count | Notes |
|--------|-------|-------|
| Edge Devices | 5 | All 5 protocols |
| AI Models | 4 | Different versions/statuses |
| LDOs | 1000+ | Sensor + context data |
| Predictions | 1000+ | With confidence scores |
| Feedback Items | ~100-150 | Low confidence cases |
| MER Reports | 10 | 5 open, 5 resolved |
| Quality Thresholds | 15 | 3 products × 5 sensors |

---

## 🆘 Troubleshooting

### No mock data showing?
```bash
# Check database
podman exec context-edge_postgres_1 psql -U context_user -d context_edge \
  -c "SELECT COUNT(*) FROM edge_devices WHERE is_mock = true;"

# Should return 5
```

### Simulator won't connect?
```bash
# Check APIs are running
curl http://localhost:8000/health
curl http://localhost:8001/health

# Should both return 200 OK
```

### Want to see raw data?
```bash
# View sample LDOs
podman exec context-edge_postgres_1 psql -U context_user -d context_edge \
  -c "SELECT cid, payload_data FROM metadata_payloads WHERE is_mock = true LIMIT 5;"
```

---

**Remember: All this is MOCK DATA for testing!** 🧪
Look for the "MOCK-" prefix and `is_mock = true` flag.

# 🧪 Mock Data Testing Suite

**⚠️ WARNING: THIS IS MOCK DATA FOR TESTING ONLY**

This directory contains scripts to populate Context Edge with realistic mock data for testing and demonstration purposes.

## 🏷️ Mock Data Identification

All mock data follows these conventions:
- **Devices:** Prefixed with `MOCK-CIM-`
- **Products:** Prefixed with `MOCK-WIDGET-`
- **LDO IDs:** Prefixed with `MOCK-LDO-`
- **Models:** Use `v0.x-MOCK` version format
- **Factory:** Named `MOCK-ACME-Manufacturing`
- **Database:** All entries have `is_mock = true`

## 📁 Files in This Directory

| File | Purpose |
|------|---------|
| `seed-mock-database.sql` | Populates PostgreSQL with mock devices, models, reports |
| `generate-mock-ldos.py` | Creates 1000+ realistic LDOs with sensor data |
| `simulate-edge-device.py` | Simulates live edge device sending data to APIs |
| `cleanup-mock-data.sql` | **DELETES ALL MOCK DATA** - use to reset |
| `test-scenarios.md` | Step-by-step testing workflows |

## 🚀 Quick Start

### 1. Seed the Database
```bash
# Load mock devices, models, thresholds, etc.
podman exec -i context-edge_postgres_1 psql -U context_user -d context_edge < seed-mock-database.sql
```

### 2. Generate Mock LDOs
```bash
# Create 1000+ realistic labeled data objects
python3 generate-mock-ldos.py --count 1000
```

### 3. Simulate Live Edge Device
```bash
# Run a simulated edge device sending real-time data
python3 simulate-edge-device.py --device MOCK-CIM-Line1-Station1 --interval 5
```

### 4. Test the UI
- Open http://localhost:3000
- Navigate to Admin → Models
- See mock devices, metrics, and feedback
- Look for "🧪 MOCK" badges

## 🧹 Clean Up Mock Data

**To delete ALL mock data and start fresh:**
```bash
podman exec -i context-edge_postgres_1 psql -U context_user -d context_edge < cleanup-mock-data.sql
```

## 🏭 Mock Manufacturing Scenario

**MOCK-ACME Manufacturing Plant**
- **Location:** Simulated factory environment
- **Production Lines:** 2 lines (Assembly, Quality Control)
- **Products:** 3 widget types (A, B, C)
- **Edge Devices:** 5 devices with different protocols
- **Time Range:** 30 days of historical data + live simulation

### Mock Edge Devices

| Device ID | Protocol | PLC Type | Location |
|-----------|----------|----------|----------|
| MOCK-CIM-Line1-Station1 | EtherNet/IP | Allen-Bradley CompactLogix | Line 1, Assembly Station 1 |
| MOCK-CIM-Line1-Station2 | PROFINET/S7 | Siemens S7-1200 | Line 1, Assembly Station 2 |
| MOCK-CIM-Line2-Station1 | OPC UA | Generic PLC | Line 2, Quality Station 1 |
| MOCK-CIM-QualityControl | Modbus RTU | Legacy Serial PLC | Final Quality Inspection |
| MOCK-CIM-Line2-Station2 | Modbus TCP | Schneider M221 | Line 2, Quality Station 2 |

### Mock Products

| Product ID | Description | Typical Defect Rate | Sensors |
|------------|-------------|---------------------|---------|
| MOCK-WIDGET-A | Standard widget | 2% | Temp, Vibration, Pressure |
| MOCK-WIDGET-B | Premium widget | 1% | Temp, Vibration, Pressure, Vision |
| MOCK-WIDGET-C | Economy widget | 5% | Temp, Pressure |

### Mock AI Models

| Version | Accuracy | Status | Training Samples | Deployed To |
|---------|----------|--------|------------------|-------------|
| v0.1-MOCK | 89% | Rolled back | 50,000 | None (historical) |
| v0.2-MOCK | 94% | Deployed | 100,000 | All 5 devices |
| v0.3-MOCK | 95% | Ready for review | 150,000 | None (pending approval) |
| v0.4-MOCK | 96% | Pilot testing | 200,000 | 2 devices (pilot) |

## 📊 Expected Test Data

After running the seed scripts, you should have:
- ✅ 5 edge devices (all protocols represented)
- ✅ 1000+ LDOs spanning 30 days
- ✅ 4 AI model versions
- ✅ 50+ MER (Manufacturing Exception Reports)
- ✅ 100+ feedback items in operator queue
- ✅ 15+ quality control thresholds
- ✅ Realistic sensor data with anomalies

## 🧪 Test Scenarios

See `test-scenarios.md` for detailed testing workflows including:
- Operator viewing real-time predictions
- Engineer reviewing feedback queue
- Data scientist deploying new models
- Protocol switching and edge device management
- Quality control threshold configuration

## 🔒 Safety Notes

1. **Never use mock data in production**
2. All mock data has `is_mock = true` flag
3. Easy to identify with `MOCK-` prefix
4. Easy to delete with cleanup script
5. Isolated from real production data

## 🆘 Troubleshooting

**Mock data not showing in UI?**
- Check database connection: `podman exec -it context-edge_postgres_1 psql -U context_user -d context_edge`
- Verify data loaded: `SELECT COUNT(*) FROM metadata_payloads WHERE is_mock = true;`
- Check API health: `curl http://localhost:8000/health`

**Want to reset and start over?**
```bash
# Delete all mock data
psql < cleanup-mock-data.sql

# Reload fresh mock data
psql < seed-mock-database.sql
python3 generate-mock-ldos.py --count 1000
```

## 📚 Related Documentation

- [Main README](../../README.md) - Project overview
- [Industrial Protocol Setup](../../docs/industrial-protocol-setup.md) - Protocol configuration
- [MLOps Guide](../../docs/mlops-deployment-guide.md) - Model deployment

---

**Remember: All data in this directory is MOCK DATA for testing purposes only!** 🧪

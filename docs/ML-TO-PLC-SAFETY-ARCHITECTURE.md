# ML-to-PLC Safety Architecture

**Critical Requirement:** ML models MUST NOT directly control PLCs
**Safety Pattern:** ML Recommendation → Human Approval → Protocol Adapter → PLC Validation
**Date:** 2025-01-16

---

## 🛑 Core Safety Principle

**ML models are NON-DETERMINISTIC:**
- Outputs are predictions/probabilities
- Subject to drift and errors
- Cannot guarantee safety

**PLCs are DETERMINISTIC:**
- Execute control logic at precise intervals
- Require reliable, validated inputs
- Safety-critical for equipment and personnel

**Therefore:** ML models provide **recommendations**, not **commands**

---

## Current vs. Required Architecture

### **Current (Read-Only):**

```
PLC Sensors → Protocol Adapter → Fusion Service → ML Model → LDO
                    ↓
              (READ ONLY - Data Collection)
```

**Purpose:** Data collection, prediction, training data generation

---

### **Required (Bidirectional with Safety Gates):**

```
┌─────────────────────────────────────────────────────────────┐
│ READ PATH (Data Collection - Current)                       │
│ PLC → Adapter → Fusion → ML → Prediction → LDO             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ WRITE PATH (Control - NEW with Safety Gates)                │
│                                                             │
│ ML Model                                                    │
│    ↓                                                        │
│ Recommendation (JSON)                                       │
│    {"action": "adjust_temp", "target": 180.0}              │
│    ↓                                                        │
│ ┌─────────────────────────────────────────┐                │
│ │ SAFETY GATE 1: Operator Approval        │                │
│ │ - Human reviews recommendation          │                │
│ │ - Can approve/reject/modify             │                │
│ │ - Logged for audit trail                │                │
│ └─────────────────────────────────────────┘                │
│    ↓ (if approved)                                          │
│ ┌─────────────────────────────────────────┐                │
│ │ SAFETY GATE 2: Range Validation         │                │
│ │ - Check MIN/MAX limits                  │                │
│ │ - Verify rate-of-change limits          │                │
│ │ - Check interlock conditions            │                │
│ └─────────────────────────────────────────┘                │
│    ↓ (if valid)                                             │
│ Protocol Adapter                                            │
│    ↓                                                        │
│ PLC Register Write (Modbus, OPC UA)                        │
│    ↓                                                        │
│ ┌─────────────────────────────────────────┐                │
│ │ SAFETY GATE 3: PLC Logic Validation     │                │
│ │ - PLC checks if value is safe           │                │
│ │ - Verifies interlocks                   │                │
│ │ - Can reject and raise alarm            │                │
│ └─────────────────────────────────────────┘                │
│    ↓ (if PLC accepts)                                       │
│ Physical Actuator (Valve, Motor, Heater)                   │
└─────────────────────────────────────────────────────────────┘
```

**Three Safety Gates:**
1. **Human Approval** - Operator reviews and approves
2. **Range Validation** - Software checks limits
3. **PLC Logic** - Hardware validates and executes

---

## Database Schema for ML Recommendations

```sql
-- ML recommendations waiting for operator approval
CREATE TABLE ml_recommendations (
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
    is_within_limits BOOLEAN,

    -- Approval workflow
    status VARCHAR(20) DEFAULT 'pending',   -- 'pending', 'approved', 'rejected', 'executed'
    priority INTEGER DEFAULT 2,             -- 1=critical, 2=high, 3=normal

    -- Operator interaction
    approved_by VARCHAR(100),
    approved_at TIMESTAMP,
    rejection_reason TEXT,
    operator_notes TEXT,

    -- Execution tracking
    protocol_adapter VARCHAR(50),           -- Which adapter will execute
    plc_register VARCHAR(50),               -- Which PLC register to write
    executed_at TIMESTAMP,
    execution_status VARCHAR(20),           -- 'success', 'failed', 'plc_rejected'
    plc_response TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP                    -- Recommendations expire after X minutes
);

-- Safety limits for each parameter (configured by engineers)
CREATE TABLE safety_limits (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(100),
    parameter_name VARCHAR(100),            -- 'temperature', 'rpm', 'pressure'
    min_value FLOAT NOT NULL,
    max_value FLOAT NOT NULL,
    max_rate_of_change FLOAT,               -- Maximum change per minute
    unit VARCHAR(20),
    alert_threshold FLOAT,                  -- Warn if approaching limit
    requires_approval BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Audit log of all ML actions (compliance/traceability)
CREATE TABLE ml_action_audit (
    id SERIAL PRIMARY KEY,
    recommendation_id VARCHAR(100),
    action VARCHAR(50),                     -- 'created', 'approved', 'rejected', 'executed'
    performed_by VARCHAR(100),              -- Operator ID or 'system'
    timestamp TIMESTAMP DEFAULT NOW(),
    details JSONB
);
```

---

## Operator UI Design

### **1. Recommendations Dashboard (`/admin/recommendations`)**

```
┌─────────────────────────────────────────────────────────────────┐
│ ML Recommendations                          🔴 3 Pending         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🔴 CRITICAL: High Temperature Detected                      │ │
│ │ Device: EDGE-Line1-Station1 | Time: 2 minutes ago           │ │
│ │                                                             │ │
│ │ Current Temperature: 195°F                                  │ │
│ │ Recommended:        180°F (reduce by 15°F)                  │ │
│ │ Safe Range:         160°F - 185°F                           │ │
│ │                                                             │ │
│ │ Model: TempControl-v2.1 | Confidence: 94%                   │ │
│ │ Reasoning: Temperature trending above safe limit.           │ │
│ │            Reduce to prevent equipment damage.              │ │
│ │                                                             │ │
│ │ [✓ Approve] [✗ Reject] [📝 Modify] [⏸️ Snooze 5min]        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🟡 HIGH: Reduce Line Speed                                  │ │
│ │ Device: EDGE-Line2-Station3 | Time: 5 minutes ago           │ │
│ │                                                             │ │
│ │ Current Speed:      120 parts/min                           │ │
│ │ Recommended:        100 parts/min (reduce by 20)            │ │
│ │ Safe Range:         50 - 150 parts/min                      │ │
│ │                                                             │ │
│ │ Model: QualityOpt-v1.3 | Confidence: 87%                    │ │
│ │ Reasoning: Quality declining at current speed.              │ │
│ │            Slower speed improves defect rate.               │ │
│ │                                                             │ │
│ │ [✓ Approve] [✗ Reject] [📝 Modify] [⏸️ Snooze 5min]        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🟢 NORMAL: Optimize Flow Rate                               │ │
│ │ [Collapsed - Click to expand]                               │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Approval Modal:**

```
┌─────────────────────────────────────────────────────────────┐
│ Approve Recommendation?                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Action: Reduce Temperature                                  │
│ From:   195°F → To: 180°F                                   │
│                                                             │
│ ✓ Within safe range (160°F - 185°F)                        │
│ ✓ Rate of change: 15°F (max: 20°F/min)                     │
│ ✓ No active interlocks                                     │
│                                                             │
│ This will write to:                                         │
│ • PLC: Line1-Modbus-PLC                                     │
│ • Register: 40001 (Temperature Setpoint)                    │
│ • Value: 1800 (scaled: 180.0°F × 10)                        │
│                                                             │
│ Your Notes (Optional):                                      │
│ [Approved - high temp alarm triggered              ]       │
│                                                             │
│ ⚠️  This action will be logged for audit trail              │
│                                                             │
│ [✓ Confirm Approval]  [Cancel]                              │
└─────────────────────────────────────────────────────────────┘
```

---

### **2. Safety Limits Configuration (`/admin/safety-limits`)**

```
┌─────────────────────────────────────────────────────────────┐
│ Safety Limits Configuration                                 │
├─────────────────────────────────────────────────────────────┤
│ Device: [EDGE-Line1-Station1 ▼]                             │
│                                                             │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ Parameter      Min    Max    Max Δ/min  Approval Req │   │
│ │ Temperature    160°F  185°F  20°F       ✓            │   │
│ │ Line Speed     50     150    30          ✓            │   │
│ │ Flow Rate      10     100    15          ✓            │   │
│ │ Pressure       80     120    10          ✓            │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                             │
│ [+ Add Parameter]  [Save Changes]                          │
└─────────────────────────────────────────────────────────────┘
```

---

### **3. Execution History (`/admin/ml-actions`)**

```
┌─────────────────────────────────────────────────────────────┐
│ ML Action History                                           │
├─────────────────────────────────────────────────────────────┤
│ [Filter: Last 24 hours ▼] [Device: All ▼] [Status: All ▼]  │
│                                                             │
│ Time        Device          Action           Operator  Status│
│ 10:45 AM    Line1-Station1  Temp 195→180°F  JSmith    ✓    │
│ 10:30 AM    Line2-Station3  Speed 120→100   JSmith    ✓    │
│ 10:15 AM    Line1-Station2  Stop Line       Auto      ✗    │
│ 09:58 AM    Line3-Station1  Pressure Adj    TJones    ✓    │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation in Code

### **Step 1: ML Model Generates Recommendation**

```python
# edge-server/app/services/fusion.py

async def run_inference(self, fused_data: Dict[str, Any]) -> Dict[str, Any]:
    """Run AI inference and generate recommendations"""

    # Run prediction
    prediction = await ml_model.predict(fused_data)

    # Generate recommendation (if needed)
    recommendation = None
    if prediction["temperature"] > 190:
        recommendation = {
            "action_type": "adjust_temp",
            "target_parameter": "temperature",
            "current_value": prediction["temperature"],
            "recommended_value": 180.0,
            "unit": "degF",
            "reasoning": "Temperature above safe threshold. Reduce to prevent damage.",
            "priority": 1,  # Critical
            "confidence": prediction["confidence"]
        }

    return {
        "prediction": prediction,
        "recommendation": recommendation
    }
```

---

### **Step 2: Store Recommendation for Operator Approval**

```python
# edge-server/app/services/recommendation_service.py

class RecommendationService:
    async def create_recommendation(
        self,
        device_id: str,
        recommendation: Dict[str, Any]
    ) -> str:
        """Store ML recommendation and validate safety limits"""

        # Get safety limits for this parameter
        limits = await self.get_safety_limits(
            device_id,
            recommendation["target_parameter"]
        )

        # Validate against limits
        is_safe = (
            limits["min_value"] <= recommendation["recommended_value"] <= limits["max_value"]
        )

        # Create recommendation record
        rec_id = f"REC-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        await db.execute("""
            INSERT INTO ml_recommendations (
                recommendation_id, device_id, action_type, target_parameter,
                current_value, recommended_value, unit, reasoning,
                min_safe_value, max_safe_value, is_within_limits,
                status, priority, model_version, confidence
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            rec_id, device_id, recommendation["action_type"],
            recommendation["target_parameter"],
            recommendation["current_value"],
            recommendation["recommended_value"],
            recommendation["unit"],
            recommendation["reasoning"],
            limits["min_value"], limits["max_value"],
            is_safe,
            "pending",
            recommendation["priority"],
            recommendation.get("model_version", "unknown"),
            recommendation["confidence"]
        ))

        # Send real-time notification to operator UI
        await websocket_manager.send_notification({
            "type": "new_recommendation",
            "recommendation_id": rec_id,
            "priority": recommendation["priority"]
        })

        return rec_id
```

---

### **Step 3: Operator Approves via UI**

```python
# edge-server/app/api/recommendations.py

@app.post("/api/recommendations/{rec_id}/approve")
async def approve_recommendation(
    rec_id: str,
    approval: ApprovalRequest,
    operator: str = Depends(get_current_operator)
):
    """Operator approves ML recommendation"""

    # Get recommendation
    rec = await db.fetch_one(
        "SELECT * FROM ml_recommendations WHERE recommendation_id = %s",
        (rec_id,)
    )

    # Validate still within limits
    if not rec["is_within_limits"]:
        raise HTTPException(400, "Recommendation outside safe limits")

    # Update status
    await db.execute("""
        UPDATE ml_recommendations
        SET status = 'approved',
            approved_by = %s,
            approved_at = NOW(),
            operator_notes = %s
        WHERE recommendation_id = %s
    """, (operator, approval.notes, rec_id))

    # Audit log
    await db.execute("""
        INSERT INTO ml_action_audit (recommendation_id, action, performed_by, details)
        VALUES (%s, 'approved', %s, %s)
    """, (rec_id, operator, Json({"notes": approval.notes})))

    # Execute via protocol adapter
    await execute_recommendation(rec)

    return {"status": "approved", "rec_id": rec_id}
```

---

### **Step 4: Protocol Adapter Executes Write**

```python
# edge-server/app/services/protocol_executor.py

async def execute_recommendation(recommendation: Dict[str, Any]):
    """Execute approved recommendation via protocol adapter"""

    device_id = recommendation["device_id"]

    # Get adapter for this device
    adapter = await get_adapter_for_device(device_id)

    # Get PLC register mapping
    register_config = await get_register_config(
        device_id,
        recommendation["target_parameter"]
    )

    try:
        # Write to PLC
        success = await adapter.write_register(
            address=register_config["address"],
            value=recommendation["recommended_value"] * register_config["scale"],
            data_type=register_config["type"]
        )

        if success:
            # Update recommendation status
            await db.execute("""
                UPDATE ml_recommendations
                SET status = 'executed',
                    executed_at = NOW(),
                    execution_status = 'success'
                WHERE recommendation_id = %s
            """, (recommendation["recommendation_id"],))

            logger.info(f"✅ Executed: {recommendation['action_type']}")

        else:
            # PLC rejected
            await db.execute("""
                UPDATE ml_recommendations
                SET execution_status = 'plc_rejected',
                    plc_response = 'PLC safety logic rejected command'
                WHERE recommendation_id = %s
            """, (recommendation["recommendation_id"],))

            logger.warning(f"⚠️ PLC rejected: {recommendation['action_type']}")

    except Exception as e:
        # Execution failed
        await db.execute("""
            UPDATE ml_recommendations
            SET execution_status = 'failed',
                plc_response = %s
            WHERE recommendation_id = %s
        """, (str(e), recommendation["recommendation_id"]))

        logger.error(f"❌ Execution failed: {e}")
```

---

### **Step 5: Protocol Adapter Write Implementation**

```python
# edge-server/app/adapters/plc.py

class ModbusPLCAdapter(PLCAdapter):
    async def write_register(
        self,
        address: int,
        value: float,
        data_type: str = "holding"
    ) -> bool:
        """
        Write value to PLC register (SAFETY-CRITICAL)

        This is where ML recommendations become physical actions!
        """

        if not self.is_connected:
            logger.error("Cannot write - adapter not connected")
            return False

        try:
            # Scale value
            scaled_value = int(value)

            logger.info(f"📝 Writing to PLC: Register {address} = {scaled_value}")

            # Write to Modbus register
            if data_type == "holding":
                result = self.client.write_register(
                    address,
                    scaled_value,
                    unit=self.config.get("unit_id", 1)
                )
            else:
                logger.error(f"Unsupported data type: {data_type}")
                return False

            # Check result
            if result.isError():
                logger.error(f"Modbus write error: {result}")
                return False

            logger.info(f"✅ PLC write successful")
            return True

        except Exception as e:
            logger.error(f"❌ PLC write failed: {e}")
            return False
```

---

## Integration with Existing Architecture

### **Existing (Read-Only):**
```python
# Current fusion flow
sensor_data = await fusion_service.read_sensor_data(device_id)
fused_data = await fusion_service.fuse_data(cid, context, sensor_data, ...)
prediction = await fusion_service.run_inference(fused_data)
ldo_id = await ldo_service.create_ldo(cid, fused_data, prediction)
```

### **New (Bidirectional with Recommendations):**
```python
# Enhanced fusion flow
sensor_data = await fusion_service.read_sensor_data(device_id)
fused_data = await fusion_service.fuse_data(cid, context, sensor_data, ...)

# Inference now returns predictions AND recommendations
result = await fusion_service.run_inference(fused_data)

# Store LDO (unchanged)
ldo_id = await ldo_service.create_ldo(cid, fused_data, result["prediction"])

# NEW: Store recommendation for operator approval (if generated)
if result.get("recommendation"):
    rec_id = await recommendation_service.create_recommendation(
        device_id=device_id,
        recommendation=result["recommendation"]
    )
    logger.info(f"📋 Recommendation created: {rec_id} (pending operator approval)")
```

---

## User-Friendly Features for Engineers/Operators

### **1. Auto-Approval Rules (Optional)**
Engineers can configure rules for low-risk actions:

```sql
CREATE TABLE auto_approval_rules (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(100),
    action_type VARCHAR(50),
    max_change FLOAT,              -- Auto-approve if change < this
    confidence_threshold FLOAT,     -- Auto-approve if confidence > this
    enabled BOOLEAN DEFAULT false
);
```

Example: "Auto-approve temperature adjustments < 10°F with confidence > 95%"

---

### **2. Batch Approval**
Operator can approve multiple recommendations at once:

```
┌─────────────────────────────────────────────────────────────┐
│ ☑ Select All (3 recommendations)                            │
│                                                             │
│ ☑ Reduce Temp Line1: 195°F → 180°F                         │
│ ☑ Reduce Speed Line2: 120 → 100 rpm                        │
│ ☑ Adjust Flow Line3: 45 → 50 L/min                         │
│                                                             │
│ [✓ Approve Selected (3)]  [✗ Reject Selected]              │
└─────────────────────────────────────────────────────────────┘
```

---

### **3. Mobile Notifications**
Critical recommendations send push notifications:

```
📱 [Context Edge Alert]
🔴 CRITICAL: High Temperature
Line 1, Station 1: 195°F → 180°F
Tap to approve or reject
```

---

### **4. Expiration/Auto-Reject**
Recommendations expire after configurable time:

```python
# Recommendations older than 10 minutes auto-reject
async def expire_old_recommendations():
    await db.execute("""
        UPDATE ml_recommendations
        SET status = 'expired',
            rejection_reason = 'Timed out - no operator response'
        WHERE status = 'pending'
          AND created_at < NOW() - INTERVAL '10 minutes'
    """)
```

---

## Summary: How This Integrates

### **Your Multi-Source Adapters (Already Built):**
- ✅ Read from PLCs, MES, ERP, SCADA, Historians
- ✅ Parallel data fusion
- ✅ Rich LDO generation

### **New Safety Layer (What We're Adding):**
- ✅ ML models generate recommendations (not commands)
- ✅ Operator approves via UI
- ✅ Safety validation (3 gates)
- ✅ Protocol adapters write to PLC (bidirectional)
- ✅ PLC validates and executes
- ✅ Full audit trail

### **Benefits:**
✅ **Safe** - Human-in-the-loop, triple validation
✅ **User-Friendly** - Operators use UI, not code
✅ **Audit-Ready** - Complete traceability for compliance
✅ **Flexible** - Auto-approval for low-risk actions
✅ **Industry-Standard** - Matches Ignition, Wonderware patterns

---

## Next Steps

**Phase 1: Database + Basic Approval (3-5 days)**
- [ ] Create recommendation tables
- [ ] Build approval API endpoints
- [ ] Build operator UI for recommendations
- [ ] Implement write capability in protocol adapters

**Phase 2: Safety Features (3-5 days)**
- [ ] Safety limits configuration UI
- [ ] Range validation
- [ ] Auto-approval rules
- [ ] Audit logging

**Phase 3: Advanced Features (5-7 days)**
- [ ] Mobile notifications
- [ ] Batch approval
- [ ] Recommendation analytics
- [ ] ML model performance tracking

**Total: 2-3 weeks to production-ready**

---

**This is the missing piece!** Your multi-source fusion is excellent for data collection, but this adds the control loop back to PLCs - safely and with human oversight.

Want to start with Phase 1?

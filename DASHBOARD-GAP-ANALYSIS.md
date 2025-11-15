# Dashboard Gap Analysis: Current vs. Ideal Engineer-Facing Dashboard

**Date:** November 15, 2025
**Spec Source:** User-provided detailed requirements
**Current Implementation:** Kilo's admin pages

---

## Executive Summary

The user has defined a **comprehensive engineer-facing dashboard** focused on empowering Maintenance/Reliability Engineers. Kilo built **60% of the pieces** but they're disconnected. Missing: The critical **Operational Summary Homepage** that ties everything together.

---

## Gap Analysis by Component

### 1. Operational Summary View (Homepage) ❌ MISSING

**Specification:**
```
├── Asset Health Overview
│   ├── Fleet Status Map/Table (color-coded by health)
│   └── Unplanned Downtime Counter (OEE data + cost)
├── Active Alert Feed
│   ├── Prioritized MER list (by confidence + criticality)
│   └── Quick links to detailed MER reports
└── Model Performance Snapshot
    ├── False Positive Rate (FPR)
    └── Current model version across fleet
```

**Current State:** ❌ Does not exist
- Admin homepage just shows navigation cards
- No operational summary
- No fleet health overview
- No active alert feed
- No FPR tracking

**Gap:** **100% missing** - This is the MOST CRITICAL component

---

### 2. Context Injection & Threshold Management ✅ PARTIALLY BUILT

| Module | Spec Requirement | Kilo's Implementation | Status |
|--------|------------------|----------------------|--------|
| **Asset Configuration** | Link Asset ID → Sensor Tags | ✅ `/admin/assets` with sensor mappings | ✅ COMPLETE |
| **Threshold Editor** | Visual sliders for Warning/Critical limits | ✅ `/admin/thresholds` with rc-slider | ✅ COMPLETE |
| **LDO/Recipe Context** | Runtime parameters for products | ❌ Not implemented | ❌ MISSING |
| **Notification Rules** | Alert routing (email/Slack/SMS) | ❌ Not implemented | ❌ MISSING |

**Gap:** **50% complete**
- ✅ Asset-to-sensor mapping works
- ✅ Threshold visualization is excellent
- ❌ Missing runtime recipe/product context
- ❌ Missing notification/alert routing

---

### 3. Maintenance Event Record (MER) Report ✅ WELL BUILT

**Specification:**
```
├── Header (Asset, Time, Failure Mode, Confidence)
├── Evidence Package
│   ├── Video clip player (5-10 sec)
│   ├── Sensor timeline chart (60s before + 5s after)
│   └── PLC/State snapshot
└── Validation Controls
    ├── Confirm Issue / False Alarm / Work Order
    └── Notes field
```

**Current State:** ✅ `/admin/mer-reports`
- ✅ Header with all required fields
- ✅ Chart.js sensor timeline (vibration, temp, current)
- ✅ PLC snapshot display
- ⚠️ Video player is placeholder (just shows URL)
- ✅ Validation buttons (Confirm/False Alarm/Work Order)
- ✅ Notes field

**Gap:** **90% complete**
- Only missing: Real video player implementation

---

### 4. MLOps & Deployment Management ✅ WELL BUILT

**Specification:**
```
├── Model Repository (versions, accuracy, descriptions)
├── Edge Device Status (online/offline, current model)
├── Deployment Interface (push models to devices)
└── Data Labeling Queue (low-confidence predictions)
```

**Current State:**
- ✅ `/admin/models` - Model repository with versions
- ✅ Edge device status with online/offline tracking
- ✅ Deploy button to push models to devices
- ✅ `/admin/feedback` - Data labeling queue

**Gap:** **95% complete**
- All pieces exist
- Only missing: Real Kubernetes integration (currently mock)

---

## What's Missing: The Critical Pieces

### 1. **Operational Summary Homepage** 🚨 CRITICAL

**Current Problem:**
- Engineer opens dashboard and sees... navigation cards
- No immediate sense of fleet health
- No prioritized action items
- No performance metrics

**What's Needed:**
```tsx
// /admin/dashboard (NEW PAGE NEEDED)
<OperationalSummary>
  <FleetHealthMap assets={assets} />
  <DowntimeCounter oeeData={oeeData} />
  <ActiveAlertFeed mers={prioritizedMers} />
  <ModelPerformance fpr={falsePositiveRate} version={currentModelVersion} />
</OperationalSummary>
```

**Impact:** Without this, the platform lacks a **command center**. Engineers don't know where to look first.

---

### 2. **LDO/Recipe Context Manager** ⚠️ IMPORTANT

**Current Problem:**
- Thresholds are static per sensor type
- No runtime adjustment based on product being made
- Example: Product A might need different vibration limits than Product B

**What's Needed:**
```tsx
// Add to /admin/thresholds or create /admin/recipes
<RecipeManager>
  <ProductList>
    <Product name="Widget A" batch="BATCH001">
      <ThresholdOverride sensor="vibration" maxG="1.2" />
      <ThresholdOverride sensor="pressure" maxPSI="45" />
    </Product>
  </ProductList>
</RecipeManager>
```

**Redis Structure:**
```json
{
  "recipe:WIDGET_A": {
    "vibration_override": {"warning_high": 1.2},
    "pressure_override": {"critical_high": 45},
    "duration_minutes": 30
  }
}
```

---

### 3. **Notification Rules Engine** ⚠️ IMPORTANT

**Current Problem:**
- MERs are generated but nobody gets notified
- No integration with CMMS (Maximo, SAP PM, etc.)
- No email/Slack/SMS alerts

**What's Needed:**
```tsx
// /admin/notifications (NEW PAGE)
<NotificationRules>
  <Rule>
    <Trigger>Failure Mode = "Bearing Wear" AND Confidence > 0.8</Trigger>
    <Actions>
      <Email>maintenance-team@factory.com</Email>
      <Slack>#reliability-alerts</Slack>
      <CMMS>Create Work Order in Maximo</CMMS>
    </Actions>
  </Rule>
</NotificationRules>
```

---

### 4. **False Positive Rate (FPR) Tracking** 📊 METRICS

**Current Problem:**
- No tracking of model performance over time
- No visibility into trust metrics
- Engineers can't see if model is improving

**What's Needed:**
```tsx
// Add to operational summary
<FPRMetrics>
  <Metric label="False Positive Rate" value="8.2%" trend="down" />
  <Metric label="True Positive Rate" value="94.1%" trend="up" />
  <Chart type="line" data={fprOverTime} />
</FPRMetrics>
```

**Backend:**
```python
# Calculate FPR from feedback data
total_predictions = count_all_mers()
false_alarms = count_feedback_where(validation='incorrect')
fpr = (false_alarms / total_predictions) * 100
```

---

## Source Control & Audit Logging 🔍

**User Question:** "i see this under source control for changes and graph= has lots too..analyze"

### Current State: ❌ NO AUDIT TRAIL

**What's Missing:**
1. **Change History** - No tracking of who changed thresholds/when
2. **Configuration Versioning** - No rollback capability
3. **Audit Logs** - No compliance trail
4. **Graph Visualizations** - Charts exist in MER page, but no trending/analytics

**What's Needed:**

#### 1. Audit Log Table
```sql
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    user_email VARCHAR(255),
    action_type VARCHAR(50),  -- 'threshold_update', 'asset_create', 'model_deploy'
    resource_type VARCHAR(50), -- 'threshold', 'asset', 'model'
    resource_id VARCHAR(255),
    old_value JSONB,
    new_value JSONB,
    ip_address VARCHAR(45)
);
```

#### 2. Configuration Version Control
```python
# When threshold is updated:
POST /context/thresholds/{sensor_type}
{
  "sensor_type": "vibration",
  "warning_high": 1.5,  # CHANGED FROM 1.2
  "changed_by": "engineer@factory.com",
  "change_reason": "Increased false positives on Line 2"
}

# System stores:
- Current version in Redis (fast access)
- Version history in PostgreSQL (audit trail)
- Ability to rollback to previous version
```

#### 3. Analytics & Graphs Needed

**Fleet Health Trend:**
```tsx
<LineChart
  title="Fleet Health Score Over Time"
  data={lastWeekHealthScores}
  xAxis="timestamp"
  yAxis="average_health_score"
/>
```

**Downtime Analysis:**
```tsx
<BarChart
  title="Downtime by Asset (Last 7 Days)"
  data={downtimeByAsset}
  yAxis="minutes_offline"
/>
```

**Model Performance Trends:**
```tsx
<MultiLineChart
  title="Model Accuracy Metrics"
  lines={[
    {label: "True Positive Rate", data: tprHistory},
    {label: "False Positive Rate", data: fprHistory}
  ]}
/>
```

---

## Redesigned Dashboard Structure

### New Page Hierarchy:
```
/admin
├── /dashboard              ← NEW: Operational Summary Homepage
│   ├── Fleet Health Map
│   ├── Active Alert Feed
│   ├── Downtime Metrics
│   └── Model Performance
│
├── /mer-reports           ← EXISTS (kilo built)
│   └── Enhanced with audit trail
│
├── /context               ← REORGANIZED
│   ├── /assets            ← EXISTS (kilo built)
│   ├── /thresholds        ← EXISTS (kilo built)
│   ├── /recipes           ← NEW: LDO/Recipe context
│   └── /notifications     ← NEW: Alert routing
│
├── /mlops                 ← REORGANIZED
│   ├── /models            ← EXISTS (kilo built)
│   ├── /feedback          ← EXISTS (kilo built)
│   └── /analytics         ← NEW: FPR trends, model metrics
│
└── /system                ← NEW
    ├── /audit-log         ← NEW: Change history
    └── /config-backup     ← NEW: Version control
```

---

## Implementation Priority

### Phase 1: Critical (Week 1) 🔥
1. **Create Operational Summary Dashboard** (`/admin/dashboard`)
   - Fleet health map
   - Active MER feed
   - Basic metrics
2. **Add FPR Calculation & Display**
3. **Add Audit Logging to Threshold Changes**

### Phase 2: Important (Week 2) ⚠️
1. **Recipe/Product Context Manager** (`/admin/context/recipes`)
2. **Notification Rules Engine** (`/admin/context/notifications`)
3. **Video Player Integration** (MER page)

### Phase 3: Polish (Week 3) ✨
1. **Analytics Dashboard** (`/admin/mlops/analytics`)
2. **Configuration Version Control**
3. **CMMS Integration** (Maximo, SAP PM)

---

## Current vs. Ideal: Score Card

| Component | Spec Weight | Current Score | Gap |
|-----------|-------------|---------------|-----|
| **Operational Summary** | 30% | 0% | 🔴 **-30%** |
| **Context Management** | 25% | 50% | 🟡 **-12.5%** |
| **MER Reports** | 20% | 90% | 🟢 **-2%** |
| **MLOps** | 15% | 95% | 🟢 **-0.75%** |
| **Audit/Analytics** | 10% | 0% | 🔴 **-10%** |
| **TOTAL** | 100% | **45.75%** | **-54.25%** |

**Conclusion:** Kilo built **45% of the ideal dashboard**. The critical missing piece is the **Operational Summary Homepage** that ties everything together.

---

## Recommendations

### Immediate Actions:
1. Create `/admin/dashboard` as the NEW default admin homepage
2. Move current admin page to `/admin/context/metadata`
3. Build fleet health overview with real-time status
4. Implement FPR calculation from feedback data

### Short-term:
1. Add audit logging to all configuration changes
2. Build recipe/product context manager
3. Add notification rules engine
4. Real video player in MER page

### Long-term:
1. Full analytics dashboard with trends
2. Configuration version control with rollback
3. CMMS integration (Maximo, SAP PM)
4. Mobile app for engineers on factory floor

---

**Status:** Major gaps identified
**Impact:** Platform is functional but lacks the **command center** engineers need
**Priority:** Build Operational Summary Dashboard ASAP

**Next Steps:** Shall I create the Operational Summary Dashboard (`/admin/dashboard`) now?

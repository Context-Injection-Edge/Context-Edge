# 🚦 Context Edge UI - Complete Guide

## What We Built (UI with Traffic Light Theme!)

### 1. **Setup Wizard** (`/admin/devices/setup-wizard`)
**The "magic" plug-and-play experience!**

```
Step 1: Scan Network 🔍
  → Button: "Scan Network"
  → Shows loading spinner while scanning
  → Displays discovered devices

Step 2: Select Device 🏭
  → Lists all found devices with icons:
     🔌 Modbus TCP
     🌐 OPC UA
     ☁️ HTTP/REST
  → Shows vendor, model, IP, port
  → Green badge: "✓ Template available"

Step 3: Configure Sensors ⚙️
  → Auto-fills device name
  → Click sensors to toggle (checkmark when selected)
  → Green background when selected
  → Shows register addresses/node IDs
  → Summary panel on right

Step 4: Test & Save 🧪
  → Yellow button: "🧪 Test Connection"
  → Shows live data stream:
     10:30:15 - temperature: 72.5 ✓
     10:30:16 - temperature: 72.6 ✓
  → Green success box if connected
  → Red error box if failed
  → Green button: "💾 Save Configuration"
```

---

### 2. **Devices Dashboard** (`/admin/devices`)
**Traffic light heaven! 🚦**

**Top Stats Cards:**
```
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│ Total Devices   │  🟢 Healthy     │  🟡 Degraded    │  🔴 Failed      │  ⚪ Disabled     │
│      10         │       7         │       1         │       1         │       1         │
│ (Blue border)   │ (Green border)  │ (Yellow border) │ (Red border)    │ (Gray border)   │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┴─────────────────┘
```

**Each Device Card Shows:**
```
┌────────────────────────────────────────────────────────────────────┐
│  🔌  Line 1 Assembly PLC                            [⏸️ Disable]  │
│      Schneider Electric M340                         [✏️ Edit]    │
│      192.168.1.10:502 • MODBUS TCP                   [🗑️ Delete]  │
│                                                                    │
│  🟢 Connected    🟢 125ms    Last connected: 2 min ago           │
│                                                                    │
│ ┌────────────────────────────────────────────────────────────┐   │
│ │ 🟢 Connection Healthy                                       │   │
│ │ All systems operational • Response time: 125ms              │   │
│ └────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

**Status Badge Colors:**
- 🟢 **Green** - Connected, healthy
  - `bg-green-50 border-green-300 text-green-800`
- 🟡 **Yellow** - Degraded, slow
  - `bg-yellow-50 border-yellow-300 text-yellow-800`
- 🔴 **Red** - Failed, disconnected
  - `bg-red-50 border-red-300 text-red-800`
- ⚪ **Gray** - Disabled, unknown
  - `bg-gray-50 border-gray-300 text-gray-600`

**Response Time Badges:**
- 🟢 **< 200ms** - Green
- 🟡 **200-500ms** - Yellow
- 🔴 **> 500ms** - Red

**Auto-refresh:**
- Toggle: `🔄 Auto-refresh ON` / `⏸️ Auto-refresh OFF`
- Refreshes every 5 seconds
- Shows real-time status changes

---

### 3. **Health Monitor** (`/admin/health`)
**Real-time monitoring with MASSIVE traffic lights! 🚦**

**Giant Traffic Light Box:**
```
┌─────────────────────────────────────────────────────┐
│  ┌──────────────────────┐                           │
│  │  🔴 (pulsing glow)   │    98%                    │
│  │  🟡 (pulsing glow)   │    Overall System Health  │
│  │  🟢 (pulsing glow)   │    9 of 10 devices healthy│
│  └──────────────────────┘                           │
└─────────────────────────────────────────────────────┘
```

**Live Metrics:**
```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ 🟢 Healthy   │ 🟡 Degraded  │ 🔴 Failed    │ Avg Response │
│     9        │      1       │      0       │    145 ms    │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

**Health Meters (Progress Bars):**
- 🟢 **> 80%** - Green bar
- 🟡 **50-80%** - Yellow bar
- 🔴 **< 50%** - Red bar

**Response Time Chart:**
```
< 100ms  < 200ms  < 500ms  < 1s
  🟢       🟢       🟡      🔴
```

**Device Cards:**
- Green border + green background = Healthy
- Yellow border + yellow background = Degraded
- Red border + red background = Failed
- Gray = Disabled

**Live Updates:**
- Updates every 3 seconds
- Shows timestamp: "Last updated 10:30:15"
- Green dot: "🟢 Live"

---

### 4. **Navigation Bar** (AdminNav component)
**Always visible at the top!**

```
┌────────────────────────────────────────────────────────────────────┐
│ ⚡ Context Edge  [🏭 Devices] [➕ Add Device] [🚦 Health] [💡 Recs] │
│                                                                    │
│                                         🟢 Edge Server Online     │
└────────────────────────────────────────────────────────────────────┘
```

**Server Status Indicator:**
- 🟢 **Online** - Green border, green dot (pulsing)
- 🔴 **Offline** - Red border, red dot
- ⚪ **Checking** - Gray border, gray dot (pulsing)

**Checks server every 10 seconds**

---

## 🎨 Traffic Light Color Scheme

### Status Lights (Animated)
```css
.healthy {
  bg-green-500
  shadow-green-500/50
  animate-pulse (glow effect)
}

.degraded {
  bg-yellow-500
  shadow-yellow-500/50
  animate-pulse
}

.failed {
  bg-red-500
  shadow-red-500/50
  animate-pulse
}

.unknown {
  bg-gray-400
  shadow-gray-400/50
}
```

### Card Backgrounds
```css
.healthy-card {
  bg-green-50
  border-green-300
  text-green-800
}

.degraded-card {
  bg-yellow-50
  border-yellow-300
  text-yellow-800
}

.failed-card {
  bg-red-50
  border-red-300
  text-red-800
}
```

### Progress Bars
```css
.healthy-bar { bg-green-500 }
.degraded-bar { bg-yellow-500 }
.failed-bar { bg-red-500 }
```

---

## 🚀 How to Use

### Step 1: Start the servers

```bash
# Terminal 1: Start Edge Server
cd edge-server
python -m uvicorn app.main:app --host 0.0.0.0 --port 5000

# Terminal 2: Run database migration
psql -U context_user -d context_edge -f database/migrations/005_device_templates.sql

# Terminal 3: Start UI
cd ui
npm install  # First time only
npm run dev
```

### Step 2: Open browser

```
http://localhost:3000/admin/devices
```

**You should see:**
- 🟢 "Edge Server Online" in nav bar (green)
- Empty devices list
- Button: "+ Add New Device"

### Step 3: Add your first device

```
1. Click "+ Add New Device"
   → Opens setup wizard

2. Enter subnet: 192.168.1.0/24
   → Click "🔍 Scan Network"
   → Wait ~10 seconds (scanning)

3. Select a device from the list
   → Click "Add Device →"
   → Template auto-loads

4. Configure sensors
   → Click sensors to select/deselect
   → Edit device name if needed
   → Click "🧪 Test Connection"

5. Verify live data
   → Should show green box: "✅ Connection Successful!"
   → See live data stream with timestamps
   → Click "💾 Save Configuration & Go Live!"

6. Done!
   → Redirects to devices dashboard
   → Device shows up with 🟢 green status
   → Hot reload activates in 5 seconds
```

### Step 4: Monitor health

```
1. Click "🚦 Health Monitor" in nav

2. See giant traffic light with overall health

3. Watch metrics update every 3 seconds:
   - Response times
   - Success rates
   - Error counts

4. Traffic lights show real-time status:
   - 🟢 All good
   - 🟡 Something slow
   - 🔴 Something broken
```

---

## 🎭 Visual Examples

### Healthy System
```
Dashboard shows:
┌─────────────────────────────────────────────┐
│  Total: 10  🟢 Healthy: 10  🟡:0  🔴:0     │
└─────────────────────────────────────────────┘

All devices have:
  🟢 Connected badge
  🟢 <200ms response time
  Green background sections
```

### Degraded System
```
Dashboard shows:
┌─────────────────────────────────────────────┐
│  Total: 10  🟢:7  🟡 Degraded: 3  🔴:0     │
└─────────────────────────────────────────────┘

Some devices have:
  🟡 Degraded badge
  🟡 200-500ms response time
  Yellow background sections
  Warning: "Slow response times detected"
```

### Failed System
```
Dashboard shows:
┌─────────────────────────────────────────────┐
│  Total: 10  🟢:5  🟡:2  🔴 Failed: 3       │
└─────────────────────────────────────────────┘

Failed devices have:
  🔴 Failed badge
  🔴 >500ms or disconnected
  Red background sections
  Error message shown
  "View Logs" and "Test Connection" buttons
```

---

## 🔥 Cool Features

### 1. **Pulsing Status Lights**
All status indicators pulse/glow to show they're live!

### 2. **Real-time Updates**
- Devices dashboard: Auto-refresh every 5 sec
- Health monitor: Auto-refresh every 3 sec
- Server status: Check every 10 sec

### 3. **Instant Feedback**
- Click "Enable" → Status changes immediately
- Click "Disable" → Turns gray immediately
- Save config → "Hot reload will activate in 5 seconds"

### 4. **Responsive Colors**
Everything changes color based on state:
- Borders, backgrounds, text, badges, progress bars
- All use traffic light theme

### 5. **Live Data Streams**
Test connection shows:
```
10:30:15 - temperature: 72.5 ✓
10:30:16 - temperature: 72.6 ✓
10:30:17 - temperature: 72.4 ✓
```

---

## 🎯 Next Steps

1. **Add Edit Modal** (edit device config)
2. **Add Charts** (historical response times)
3. **Add Logs Viewer** (view error logs)
4. **Add Alerts** (email/slack when device fails)
5. **Add Dark Mode** (for night shift operators)

---

## 📸 Screenshot Guide

### What to Expect:

**Setup Wizard:**
- Clean, modern interface
- Large buttons with icons
- Step-by-step progress bar
- Green success indicators
- Live data preview

**Devices Dashboard:**
- Card-based layout
- Huge traffic lights on each card
- Color-coded everything
- Quick actions (Enable/Disable/Edit/Delete)

**Health Monitor:**
- Giant traffic light box (like a real traffic light!)
- Real-time metrics
- Beautiful progress bars
- Color-coded device health cards

**Everything is color-coded with traffic lights! 🚦**

---

This is a **world-class industrial UI** with traffic light theming throughout! 🎨

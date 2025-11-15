# In-Platform Help System
**Contextual Help for Operators, Engineers, and ML Scientists**

---

## 🎯 **Goal**

Make Context Edge **self-documenting** with:
- ✅ Help icons (?) next to every section
- ✅ Pop-up modals with step-by-step guides
- ✅ Contextual tooltips on hover
- ✅ **Role-specific help** (Operator vs Engineer vs ML Scientist)
- ✅ Video tutorials embedded
- ✅ Links to full documentation

---

## 📋 **User Roles and Their Needs**

### **1. Operators 👷 (Factory Floor)**
**What they need:**
- Simple, visual instructions ("Click the green button")
- Screenshots/videos
- No technical jargon
- Quick reference guides

**Example Help Topics:**
- "How do I scan a QR code?"
- "What does this alert mean?"
- "How do I acknowledge an MER?"

---

### **2. Engineers 👨‍🔧 (Maintenance/Process)**
**What they need:**
- Technical details about thresholds
- Root cause analysis
- How to adjust settings
- Troubleshooting guides

**Example Help Topics:**
- "How do I set vibration thresholds?"
- "What sensors are mapped to this asset?"
- "How do I validate an MER?"

---

### **3. ML Scientists 👨‍💻 (Data Scientists)**
**What they need:**
- Model training details
- Deployment workflows
- API documentation
- Performance metrics

**Example Help Topics:**
- "How does model training work?"
- "How do I deploy a model to edge devices?"
- "What is the feedback loop?"

---

## 🛠️ **Implementation Plan**

### **Step 1: Create Help Component**

Create `ui/src/components/HelpPopup.tsx`:

```typescript
'use client';

import { useState } from 'react';

interface HelpContent {
  title: string;
  role: 'operator' | 'engineer' | 'ml-scientist' | 'all';
  content: string;
  steps?: string[];
  videoUrl?: string;
  docsUrl?: string;
}

interface HelpPopupProps {
  helpKey: string;
  helpContent: HelpContent;
}

export default function HelpPopup({ helpKey, helpContent }: HelpPopupProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Help Icon Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="inline-flex items-center justify-center w-5 h-5 text-blue-600 hover:text-blue-800 rounded-full border border-blue-600 hover:border-blue-800"
        title="Click for help"
      >
        ?
      </button>

      {/* Modal */}
      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <h3 className="text-xl font-semibold text-gray-900">
                {helpContent.title}
              </h3>
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-400 hover:text-gray-600 text-2xl"
              >
                ×
              </button>
            </div>

            {/* Content */}
            <div className="px-6 py-4">
              <p className="text-gray-700 mb-4">{helpContent.content}</p>

              {/* Step-by-step instructions */}
              {helpContent.steps && (
                <div className="mb-4">
                  <h4 className="font-semibold text-gray-900 mb-2">Steps:</h4>
                  <ol className="list-decimal list-inside space-y-2">
                    {helpContent.steps.map((step, index) => (
                      <li key={index} className="text-gray-700">{step}</li>
                    ))}
                  </ol>
                </div>
              )}

              {/* Video tutorial */}
              {helpContent.videoUrl && (
                <div className="mb-4">
                  <h4 className="font-semibold text-gray-900 mb-2">Video Tutorial:</h4>
                  <iframe
                    width="100%"
                    height="315"
                    src={helpContent.videoUrl}
                    title="Tutorial video"
                    frameBorder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  ></iframe>
                </div>
              )}

              {/* Link to full docs */}
              {helpContent.docsUrl && (
                <div className="mt-4">
                  <a
                    href={helpContent.docsUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 underline"
                  >
                    📖 Read Full Documentation →
                  </a>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
              <button
                onClick={() => setIsOpen(false)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Got it, thanks!
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
```

---

### **Step 2: Create Help Content Database**

Create `ui/src/content/help-content.ts`:

```typescript
export const helpContent = {
  // ========================================
  // OPERATORS
  // ========================================
  'operator-qr-scan': {
    title: 'How to Scan a QR Code',
    role: 'operator',
    content: 'QR codes tell the system what product is being made. This helps the AI know what to expect.',
    steps: [
      'Hold the QR code 6-12 inches from the camera',
      'Wait for the green checkmark',
      'Start production - the system is now tracking'
    ],
    videoUrl: 'https://youtube.com/embed/example-qr-scan',
    docsUrl: '/docs/operator-guide#qr-scanning'
  },

  'operator-mer-alert': {
    title: 'What is an MER Alert?',
    role: 'operator',
    content: 'MER (Maintenance Event Record) alerts mean the AI detected something unusual. An engineer will review it.',
    steps: [
      'Click the alert to see details',
      'Read what the AI detected (bearing wear, belt slippage, etc.)',
      'Wait for engineer to arrive - DO NOT stop production unless told',
      'Click "Acknowledge" when engineer arrives'
    ],
    docsUrl: '/docs/operator-guide#mer-alerts'
  },

  // ========================================
  // ENGINEERS
  // ========================================
  'engineer-threshold-config': {
    title: 'How to Configure Thresholds',
    role: 'engineer',
    content: 'Thresholds define warning and critical limits for sensor values. Set these based on equipment specs.',
    steps: [
      'Select the sensor type (vibration, temperature, current, pressure)',
      'Drag the yellow slider for WARNING level',
      'Drag the red slider for CRITICAL level',
      'Click "Save" to apply to all assets of this type',
      'Monitor for 24 hours to verify thresholds are correct'
    ],
    videoUrl: 'https://youtube.com/embed/example-thresholds',
    docsUrl: '/docs/engineer-guide#threshold-configuration'
  },

  'engineer-mer-validation': {
    title: 'How to Validate an MER',
    role: 'engineer',
    content: 'Validating MERs helps the AI learn. Confirm if the AI was correct or wrong.',
    steps: [
      'Review sensor data (vibration spike, temperature, etc.)',
      'Watch the video clip (if available)',
      'Physically inspect the equipment',
      'Click "Confirm" if AI was correct, or "False Alarm" if wrong',
      'Add notes about what you found'
    ],
    docsUrl: '/docs/engineer-guide#mer-validation'
  },

  'engineer-asset-mapping': {
    title: 'How to Map Sensors to Assets',
    role: 'engineer',
    content: 'Asset mapping connects sensors (from PLCs) to physical equipment.',
    steps: [
      'Enter Asset ID (e.g., CNC-Line1)',
      'Select sensor tags from dropdown (OPC UA path)',
      'Map vibration, temperature, current sensors',
      'Test the mapping - click "Read Sensors"',
      'Save the configuration'
    ],
    videoUrl: 'https://youtube.com/embed/example-asset-mapping',
    docsUrl: '/docs/engineer-guide#asset-mapping'
  },

  // ========================================
  // ML SCIENTISTS
  // ========================================
  'ml-model-deployment': {
    title: 'How Model Deployment Works',
    role: 'ml-scientist',
    content: 'Models are trained on GPU servers, converted to TensorRT, then deployed to edge devices.',
    steps: [
      'Training container runs on GPU server (6-8 hours)',
      'Model is uploaded to S3/MinIO',
      'Engineer reviews model in UI',
      'Engineer deploys to 5 pilot devices',
      'Monitor pilot for 24-48 hours',
      'If successful, deploy to all 50+ devices'
    ],
    videoUrl: 'https://youtube.com/embed/example-deployment',
    docsUrl: '/docs/mlops-workflow-guide'
  },

  'ml-training-pipeline': {
    title: 'How ML Training Works',
    role: 'ml-scientist',
    content: 'Training uses LDOs (Labeled Data Objects) collected from edge devices. Labels are 100% accurate from QR codes.',
    steps: [
      'Edge devices upload LDOs to S3 (sensor data + context)',
      'Training container downloads 100K LDOs',
      'PyTorch model trains for 50 epochs (6-8 hours)',
      'Model converts to TensorRT (optimized for Jetson)',
      'Model registered via API for deployment'
    ],
    docsUrl: '/docs/ml-architecture-explained'
  },

  'ml-feedback-loop': {
    title: 'How the Feedback Loop Works',
    role: 'ml-scientist',
    content: 'Low-confidence predictions (<60%) are queued for engineer validation. This improves the model.',
    steps: [
      'Edge device makes prediction with low confidence',
      'Prediction queued in Feedback Queue',
      'Engineer validates (correct/incorrect)',
      'Validated data added to training dataset',
      'Next training run uses this data to improve'
    ],
    docsUrl: '/docs/ml-architecture-explained#feedback-loop'
  },

  'ml-industrial-rag': {
    title: 'What is Industrial RAG?',
    role: 'ml-scientist',
    content: 'Industrial RAG retrieves context (product, recipe, asset data) from Redis to augment sensor data.',
    steps: [
      'QR code scanned → CID extracted (e.g., QM-BATCH-12345)',
      'Redis lookup: GET context:QM-BATCH-12345',
      'Returns JSON with product_id, recipe_id, asset_id',
      'This context is fed to AI model alongside sensor data',
      'Model makes context-aware predictions (94% accuracy)'
    ],
    docsUrl: '/docs/ml-architecture-explained#industrial-rag'
  },

  // ========================================
  // DEPLOYMENT (ALL ROLES)
  // ========================================
  'deployment-options': {
    title: 'Model Deployment Options',
    role: 'all',
    content: 'Choose deployment method based on factory size: Manual (1-10 devices), Script (10-50), or K3s (50+).',
    steps: [
      'Small factory (1-10 devices): Use manual SSH deployment',
      'Medium factory (10-50 devices): Use deploy-model.sh script',
      'Large factory (50+ devices): Use K3s DaemonSet',
      'All methods work with Docker or Podman',
      'See full deployment guide for step-by-step instructions'
    ],
    docsUrl: '/docs/deployment-guide-for-manufacturers'
  },

  // ========================================
  // INDUSTRIAL PROTOCOLS (ENGINEERS)
  // ========================================
  'engineer-protocol-selection': {
    title: 'Which Protocol Should I Use?',
    role: 'engineer',
    content: 'Choose the protocol based on your PLC brand. Context Edge supports 5 major protocols covering 85%+ of industrial PLCs.',
    steps: [
      'Check your PLC model number (on the PLC case or in programming software)',
      'Allen-Bradley/Rockwell → Use EtherNet/IP',
      'Siemens S7-1200/1500 → Use OPC UA or PROFINET/S7',
      'Siemens S7-300/400 → Use PROFINET/S7',
      'Schneider Electric → Use Modbus TCP or OPC UA (M580)',
      'Legacy PLC (pre-2000) → Use Modbus RTU (serial)',
      'Unknown brand → Try OPC UA (most universal)'
    ],
    videoUrl: 'https://youtube.com/embed/protocol-selection-guide',
    docsUrl: '/docs/industrial-protocol-setup'
  },

  'engineer-ethernetip-config': {
    title: 'How to Configure EtherNet/IP',
    role: 'engineer',
    content: 'EtherNet/IP is used for Allen-Bradley and Rockwell Automation PLCs (ControlLogix, CompactLogix).',
    steps: [
      'Find PLC IP address in Studio 5000 (Controller Properties → General)',
      'Identify PLC tag names in Studio 5000 (Controller Tags tab)',
      'Copy tag names exactly (case-sensitive!): Motor1_Temp, Conveyor_Speed, etc.',
      'Enter PLC IP and port (default 44818) in Context Edge UI',
      'Map sensor names to PLC tag names',
      'Click "Test Connection" to verify communication'
    ],
    docsUrl: '/docs/industrial-protocol-setup#ethernetip'
  },

  'engineer-opcua-config': {
    title: 'How to Configure OPC UA',
    role: 'engineer',
    content: 'OPC UA is a universal protocol supported by Siemens, ABB, B&R, Allen-Bradley, and many others.',
    steps: [
      'Find OPC UA server URL (usually opc.tcp://[PLC_IP]:4840)',
      'Download UaExpert tool (free OPC UA browser)',
      'Connect UaExpert to PLC and browse available nodes',
      'Copy node IDs (e.g., ns=2;i=1001 or ns=2;s=Temperature)',
      'Enter server URL and node mappings in Context Edge',
      'Test connection'
    ],
    videoUrl: 'https://youtube.com/embed/opcua-configuration',
    docsUrl: '/docs/industrial-protocol-setup#opcua'
  },

  'engineer-profinet-config': {
    title: 'How to Configure PROFINET/S7',
    role: 'engineer',
    content: 'PROFINET/S7 protocol is used for Siemens S7-300/400/1200/1500 PLCs.',
    steps: [
      'Find PLC IP address in TIA Portal (Device Configuration → Properties)',
      'Note rack and slot numbers (usually Rack=0, Slot=1 for S7-1200/1500)',
      'Identify Data Blocks (DB) in TIA Portal PLC Tags',
      'Note DB number, byte offset, and data type (REAL, INT, DINT, BOOL)',
      'Enter IP, rack, slot, and DB mappings in Context Edge',
      'Ensure PUT/GET is enabled in PLC security settings',
      'Ensure DB blocks are non-optimized (required for S7 protocol)'
    ],
    videoUrl: 'https://youtube.com/embed/profinet-s7-setup',
    docsUrl: '/docs/industrial-protocol-setup#profinet'
  },

  'engineer-modbus-tcp-config': {
    title: 'How to Configure Modbus TCP',
    role: 'engineer',
    content: 'Modbus TCP is used for Schneider Electric, Emerson, and many legacy PLCs.',
    steps: [
      'Find PLC IP address (check PLC web interface or programming software)',
      'Identify register addresses from PLC documentation',
      'Determine register type: Holding (read/write) or Input (read-only)',
      'Note scaling factors (register value ÷ scale = actual value)',
      'Enter IP, port (default 502), and register mappings in Context Edge',
      'Test connection'
    ],
    docsUrl: '/docs/industrial-protocol-setup#modbus'
  },

  'engineer-modbus-rtu-config': {
    title: 'How to Configure Modbus RTU (Serial)',
    role: 'engineer',
    content: 'Modbus RTU is used for legacy PLCs and devices with RS-232/RS-485 serial communication.',
    steps: [
      'Connect serial cable: RS-232 (3-wire) or RS-485 (2-wire + ground)',
      'Find serial port: Linux (/dev/ttyUSB0) or Windows (COM3)',
      'Check device manual for: Baudrate (usually 9600), Parity (usually None), Slave ID',
      'Grant permissions on Linux: sudo usermod -a -G dialout $USER',
      'Configure register addresses and scaling factors',
      'Enter port, baudrate, slave ID, and register mappings in Context Edge',
      'Test connection'
    ],
    docsUrl: '/docs/industrial-protocol-setup#modbus-rtu'
  },

  'engineer-protocol-compatibility': {
    title: 'PLC Brand Compatibility Matrix',
    role: 'engineer',
    content: 'Quick reference for which protocol works with which PLC brand.',
    steps: [
      'Allen-Bradley, Rockwell → EtherNet/IP (primary), OPC UA (alternative)',
      'Siemens S7-1200/1500 → OPC UA (primary), PROFINET/S7 (alternative)',
      'Siemens S7-300/400 → PROFINET/S7 (primary), OPC UA (alternative)',
      'Schneider M340 → Modbus TCP',
      'Schneider M580 → OPC UA (primary), Modbus TCP (alternative)',
      'ABB, B&R → OPC UA',
      'Legacy PLCs (pre-2000) → Modbus RTU (serial)'
    ],
    docsUrl: '/docs/industrial-protocol-setup#protocol-selection-guide'
  }
};
```

---

### **Step 3: Add Help Icons to UI**

Update `ui/src/app/admin/models/page.tsx`:

```typescript
import HelpPopup from '@/components/HelpPopup';
import { helpContent } from '@/content/help-content';

// In your component:
<div className="flex items-center gap-2">
  <h2 className="text-xl font-semibold text-gray-900">
    MLOps Dashboard
  </h2>
  <HelpPopup
    helpKey="ml-model-deployment"
    helpContent={helpContent['ml-model-deployment']}
  />
</div>
```

Update `ui/src/app/admin/thresholds/page.tsx`:

```typescript
<div className="flex items-center gap-2">
  <h2 className="text-xl font-semibold text-gray-900">
    Threshold Configuration
  </h2>
  <HelpPopup
    helpKey="engineer-threshold-config"
    helpContent={helpContent['engineer-threshold-config']}
  />
</div>
```

---

## 📝 **Where to Add Help Icons**

### **Priority 1: High-Impact Pages**

| Page | Help Topics | User Role |
|------|------------|-----------|
| **MLOps Dashboard** | Model deployment, pilot testing | ML Scientist |
| **Thresholds** | How to set limits, sensor types | Engineer |
| **MER Reports** | What is MER, how to validate | Engineer + Operator |
| **Feedback Queue** | Feedback loop, retraining | ML Scientist |
| **Assets** | Sensor mapping, asset master data | Engineer |
| **Live View** (future) | QR scanning, alerts | Operator |

---

## 🎨 **Visual Examples**

### **Help Icon Placement**

```
╔═══════════════════════════════════════════════════╗
║  MLOps Dashboard (?)   ← Help icon here           ║
║  ─────────────────────────────────────────────    ║
║                                                    ║
║  🤖 New Model Available!                          ║
║  Version: v2.1                                     ║
║  Accuracy: 94% (+5%)                               ║
║                                                    ║
║  What does this mean? (?) ← Contextual help       ║
║                                                    ║
║  [Deploy to Pilot (5 devices)] (?)                ║
║   ↑ Help on what "pilot" means                    ║
╚═══════════════════════════════════════════════════╝
```

---

## 🚀 **Implementation Checklist**

- [ ] Create `HelpPopup.tsx` component
- [ ] Create `help-content.ts` with all help topics
- [ ] Add help icons to MLOps Dashboard
- [ ] Add help icons to Thresholds page
- [ ] Add help icons to MER Reports page
- [ ] Add help icons to Feedback Queue page
- [ ] Add help icons to Assets page
- [ ] Record video tutorials (or link to YouTube)
- [ ] Test help popups on mobile devices
- [ ] Add role-based filtering (show only relevant help)

---

## 🎯 **Next Steps**

1. **Implement Help Component** (1 hour)
2. **Add Help Content** (2 hours)
3. **Place Help Icons** (1 hour per page)
4. **Record Videos** (optional, 1 week)
5. **User Testing** (1 week with operators, engineers, ML scientists)

---

**Goal: Make Context Edge the easiest industrial AI platform to use!** 🏭

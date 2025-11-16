# Context Edge - Edge Device

**Modular edge device platform** for capturing CID via multiple input methods and sending to Edge Server.

## What It Does

The edge device sits on the factory floor and captures Context IDs (CID) using various input methods:

- **Camera** (QR codes) ✅ Implemented
- **RFID Reader** ⚠️ Placeholder
- **Barcode Scanner** ⚠️ Placeholder
- **OCR Scanner** ⚠️ Future
- **NFC Reader** ⚠️ Future

Once CID is captured, it sends to the Edge Server for fusion, AI inference, and LDO generation.

## Architecture

```
Edge Device (Raspberry Pi/Jetson)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input Layer:
├── Camera Stream (QR codes)     ✅
├── RFID Reader                  ⚠️
├── Barcode Scanner              ⚠️
└── [Future: OCR, NFC, etc.]
            │
            ▼
        Extract CID
            │
            ▼
    Send to Edge Server ──────────► Edge Server
                                    (Fusion + AI + LDO)
```

## Hardware Requirements

### Minimum:
- Raspberry Pi 4 (2GB RAM)
- USB camera OR RFID reader OR barcode scanner
- Network connection to Edge Server

### Recommended:
- Jetson Nano (for better camera performance)
- Pi Camera Module v2 (better than USB)
- Ethernet connection (more reliable than WiFi)

## Installation

### On Raspberry Pi / Jetson

```bash
# Clone repo
git clone https://github.com/yourorg/context-edge.git
cd context-edge/edge-device

# Install dependencies
pip3 install -r requirements.txt

# Configure
export EDGE_SERVER_URL="http://edge-server.local:5000/cid"
export DEVICE_ID="EDGE-Line1-Station1"
export INPUT_TYPE="camera"  # or "rfid", "barcode"
export CAMERA_INDEX="0"     # Only for camera input

# Run
python3 -m edge_app.main
```

### Docker (Alternative)

```bash
docker build -t edge-device .
docker run --device=/dev/video0 \
  -e EDGE_SERVER_URL="http://edge-server:5000/cid" \
  -e DEVICE_ID="EDGE-Line1-Station1" \
  -e INPUT_TYPE="camera" \
  edge-device
```

## Configuration

All configuration via environment variables:

### Required:
- `EDGE_SERVER_URL`: URL of Edge Server endpoint (default: http://localhost:5000/cid)
- `DEVICE_ID`: Unique identifier for this edge device (default: EDGE-Line1-Station1)

### Input Selection:
- `INPUT_TYPE`: Type of input module (default: "camera")
  - `"camera"` - Camera stream with QR decoding ✅
  - `"rfid"` - RFID reader ⚠️ Not implemented
  - `"barcode"` - Barcode scanner ⚠️ Not implemented

### Camera-specific:
- `CAMERA_INDEX`: Camera device index (default: 0)
- `SCAN_INTERVAL`: Minimum seconds between duplicate scans (default: 1.0)

### RFID-specific (when implemented):
- `RFID_PORT`: Serial port (e.g., /dev/ttyUSB0)
- `RFID_BAUDRATE`: Serial baudrate (default: 9600)

### Barcode-specific (when implemented):
- `BARCODE_PORT`: Serial port (e.g., /dev/ttyUSB0)
- `BARCODE_BAUDRATE`: Serial baudrate (default: 9600)

## Input Modules

### Camera Stream (Implemented ✅)

**File:** `edge_app/inputs/camera_stream.py`

**Features:**
- Real-time video streaming (OpenCV)
- QR code decoding (pyzbar)
- Automatic CID extraction
- Debouncing to avoid duplicates
- ~30 FPS processing

**Usage:**
```bash
export INPUT_TYPE="camera"
export CAMERA_INDEX="0"
python3 -m edge_app.main
```

### RFID Reader (Placeholder ⚠️)

**File:** `edge_app/inputs/rfid_reader.py`

**TODO:**
- Implement serial communication
- Parse RFID tag data
- Extract CID from tag

### Barcode Scanner (Placeholder ⚠️)

**File:** `edge_app/inputs/barcode_scanner.py`

**TODO:**
- Implement serial communication
- Parse barcode data
- Support 1D and 2D barcodes

## Adding New Input Types

Easy to extend! Create a new input module:

```python
# edge_app/inputs/my_input.py
class MyInput:
    def __init__(self, on_cid_detected=None):
        self.on_cid_detected = on_cid_detected

    def start(self):
        # Your input logic here
        cid = self._read_cid()
        if self.on_cid_detected:
            self.on_cid_detected(cid)

    def stop(self):
        # Cleanup
        pass
```

Then add to `main.py`:
```python
elif self.input_type == "my_input":
    from edge_app.inputs.my_input import MyInput
    self.input_module = MyInput(on_cid_detected=self.send_cid)
```

## Cost

**Per Edge Device:**
- Raspberry Pi 4 (2GB): $45
- Pi Camera Module v2: $25
- Power supply + case: $15-20
- MicroSD card: $10

**Total: ~$95 per edge device**

**Alternative with RFID:**
- Raspberry Pi 4: $45
- USB RFID Reader: $30-50
- Total: ~$75-95

## Troubleshooting

### Camera not detected
```bash
# List video devices
ls -la /dev/video*

# Test camera
python3 -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

### QR codes not scanning
- Ensure good lighting
- Keep QR code 6-12 inches from camera
- Use high-contrast QR codes (black on white)
- Avoid reflections/glare

### Connection errors
```bash
# Test edge server
curl http://edge-server-url:5000/health

# Check network
ping edge-server-host
```

### Serial port issues (RFID/Barcode)
```bash
# List serial ports
ls -la /dev/ttyUSB* /dev/ttyACM*

# Add user to dialout group
sudo usermod -a -G dialout $USER
# Then logout and login
```

## Development

### Run locally
```bash
python3 -m edge_app.main
```

### Run tests
```bash
pytest tests/
```

### Simulate input without hardware
```bash
# TODO: Add simulation mode for testing
export SIMULATION_MODE="true"
python3 -m edge_app.main
```

## Scalability

**One Edge Server can handle:**
- 5-10 edge devices simultaneously
- ~1000 CID scans per day
- Sub-100ms latency per scan

**For larger deployments:**
- Deploy multiple edge servers
- Use load balancing
- Consider K3s for orchestration

## Support Matrix

| Input Type | Status | Hardware | Cost |
|------------|--------|----------|------|
| Camera (QR) | ✅ Implemented | USB webcam / Pi Camera | $20-30 |
| RFID Reader | ⚠️ Placeholder | USB RFID (125kHz/13.56MHz) | $30-50 |
| Barcode Scanner | ⚠️ Placeholder | USB barcode scanner | $40-60 |
| OCR Scanner | ⚠️ Future | Camera + OCR software | $25-35 |
| NFC Reader | ⚠️ Future | USB NFC reader | $20-40 |

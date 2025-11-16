#!/usr/bin/env python3
"""
Context Edge - Edge Device Main Application
Modular edge device supporting multiple input methods
"""

import os
import sys
import requests
from datetime import datetime
import logging

from edge_app.inputs import CameraStreamInput
# from edge_app.inputs.rfid_reader import RFIDReaderInput
# from edge_app.inputs.barcode_scanner import BarcodeScannerInput

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
EDGE_SERVER_URL = os.getenv("EDGE_SERVER_URL", "http://localhost:5000/cid")
DEVICE_ID = os.getenv("DEVICE_ID", "EDGE-Line1-Station1")
INPUT_TYPE = os.getenv("INPUT_TYPE", "camera")  # camera, rfid, barcode
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
SCAN_INTERVAL = float(os.getenv("SCAN_INTERVAL", "1.0"))


class EdgeDevice:
    """
    Modular edge device that captures CID via multiple input methods
    and sends to Edge Server
    """

    def __init__(self):
        self.device_id = DEVICE_ID
        self.edge_server_url = EDGE_SERVER_URL
        self.input_type = INPUT_TYPE
        self.input_module = None

    def start(self):
        """Start edge device with configured input module"""
        logger.info("=" * 60)
        logger.info("Context Edge - Edge Device")
        logger.info("=" * 60)
        logger.info(f"🔧 Device ID: {self.device_id}")
        logger.info(f"📡 Edge Server: {self.edge_server_url}")
        logger.info(f"🎛️  Input Type: {self.input_type}")
        logger.info("")

        # Initialize input module based on configuration
        if self.input_type == "camera":
            logger.info("📷 Initializing Camera Stream Input...")
            self.input_module = CameraStreamInput(
                camera_index=CAMERA_INDEX,
                scan_interval=SCAN_INTERVAL,
                on_cid_detected=self.send_cid
            )
        elif self.input_type == "rfid":
            logger.info("🔖 Initializing RFID Reader Input...")
            logger.error("❌ RFID input not yet implemented")
            sys.exit(1)
            # from edge_app.inputs.rfid_reader import RFIDReaderInput
            # self.input_module = RFIDReaderInput(on_cid_detected=self.send_cid)
        elif self.input_type == "barcode":
            logger.info("📊 Initializing Barcode Scanner Input...")
            logger.error("❌ Barcode input not yet implemented")
            sys.exit(1)
            # from edge_app.inputs.barcode_scanner import BarcodeScannerInput
            # self.input_module = BarcodeScannerInput(on_cid_detected=self.send_cid)
        else:
            logger.error(f"❌ Unknown input type: {self.input_type}")
            sys.exit(1)

        # Start input module
        logger.info("✅ Input module initialized")
        logger.info("🚀 Starting CID capture...")
        logger.info("")
        self.input_module.start()

    def send_cid(self, cid: str, video_path: str = None):
        """
        Send CID + video to Edge Server

        Args:
            cid: Context ID from input module
            video_path: Path to video clip file (if captured)
        """
        timestamp = datetime.now().isoformat()

        logger.info(f"📤 Sending CID: {cid}")
        if video_path:
            logger.info(f"📹 Sending video: {video_path}")

        try:
            # Prepare multipart form data
            files = {}
            if video_path and os.path.exists(video_path):
                files['video'] = open(video_path, 'rb')

            data = {
                "cid": cid,
                "device_id": self.device_id,
                "timestamp": timestamp
            }

            response = requests.post(
                self.edge_server_url,
                files=files,
                data=data,
                timeout=30  # Longer timeout for video upload
            )

            # Close file handle
            if 'video' in files:
                files['video'].close()

            if response.status_code == 200:
                result = response.json()
                ldo_id = result.get('ldo_id', 'unknown')
                logger.info(f"   ✅ Edge Server accepted: {result.get('status', 'ok')}")
                logger.info(f"   💾 LDO created: {ldo_id}")

                # Clean up video file after successful upload
                if video_path and os.path.exists(video_path):
                    os.remove(video_path)
                    logger.info(f"   🗑️  Video file cleaned up")
            else:
                logger.error(f"   ❌ Error: HTTP {response.status_code}")
                logger.error(f"      {response.text}")

        except requests.exceptions.ConnectionError:
            logger.error(f"   ❌ Connection error: Edge Server not reachable")
        except requests.exceptions.Timeout:
            logger.error(f"   ❌ Timeout: Edge Server took too long")
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")


def main():
    device = EdgeDevice()
    device.start()


if __name__ == "__main__":
    main()
